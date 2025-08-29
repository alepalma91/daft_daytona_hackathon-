from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uuid
import json
import asyncio
from datetime import datetime
import base64
import os
from contextlib import asynccontextmanager
from io import BytesIO

# Daft and ML imports for style analysis
import daft
from daft import col, udf
from PIL import Image
import numpy as np
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Global variables for style analysis
llm_client = None
image_analysis_df = None

@asynccontextmanager
async def lifespan(app):
    # Startup - Initialize LLM and Daft
    global llm_client, image_analysis_df
    initialize_llm()
    initialize_daft_dataframe()
    # Set up Daft configuration
    os.environ["DAFT_PROGRESS_BAR"] = "0"
    yield
    # Shutdown (cleanup if needed)
    pass

app = FastAPI(title="Image Canvas Workspace API", version="1.0.0", lifespan=lifespan)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:8001", "http://127.0.0.1:8001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data Models
class Point(BaseModel):
    x: float
    y: float

class ImageNode(BaseModel):
    id: str
    src: str  # URL or base64 data
    x: float
    y: float
    w: float
    h: float
    selected: bool = False
    groupId: Optional[str] = None

class ImageGroup(BaseModel):
    id: str
    imageIds: List[str]
    name: Optional[str] = None

class Viewport(BaseModel):
    scale: float = 1.0
    tx: float = 0.0  # translation x
    ty: float = 0.0  # translation y

class CanvasState(BaseModel):
    id: str
    images: List[ImageNode] = []
    groups: List[ImageGroup] = []
    viewport: Viewport = Viewport()
    lastModified: datetime

class ChatMessage(BaseModel):
    id: str
    text: str
    sender: str = "User"
    timestamp: datetime
    canvasId: str

class WebSocketMessage(BaseModel):
    type: str  # 'canvas_update', 'chat_message', 'user_joined', etc.
    data: Dict[str, Any]
    canvasId: str

# Style Analysis Models
class StyleAnalysisRequest(BaseModel):
    image_ids: List[str]

class ImageAnalysisResponse(BaseModel):
    id: str
    filename: str
    canvas_id: str
    style_description: str
    dominant_colors: List[str]
    artistic_elements: List[str]
    timestamp: datetime

# Style Analysis Functions and UDFs
def initialize_llm():
    """Initialize the LLM client for style analysis"""
    global llm_client
    
    if os.getenv("OPENAI_API_KEY"):
        try:
            from openai import AsyncOpenAI
            llm_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            print("✅ Initialized OpenAI client for style analysis")
        except ImportError:
            print("⚠️ OpenAI package not available, falling back to local model")
            llm_client = None
    
    if llm_client is None:
        # Fallback to using a vision transformer model locally
        try:
            import torch
            from transformers import AutoModelForCausalLM
            
            device = 'cuda' if torch.cuda.is_available() else 'mps' if torch.backends.mps.is_available() else 'cpu'
            print(f"Using device: {device}")
            
            llm_client = {
                "model": AutoModelForCausalLM.from_pretrained(
                    "vikhyatk/moondream2",
                    revision="2025-06-21",
                    trust_remote_code=True,
                    device_map={"": device}
                ),
                "type": "moondream"
            }
            print("✅ Initialized Moondream model for style analysis")
        except Exception as e:
            print(f"❌ Could not initialize local model: {e}")
            llm_client = None

def initialize_daft_dataframe():
    """Initialize the Daft DataFrame for storing image analysis data"""
    global image_analysis_df
    
    # Create empty DataFrame with consistent schema by using proper types
    # We'll create the DataFrame on first upload to avoid schema mismatches
    image_analysis_df = None
    print("✅ Initialized Daft DataFrame for image analysis storage")

@daft.func(return_dtype=daft.DataType.string())
def analyze_image_style(image_array) -> str:
    """Analyze the artistic style of an image using LLM"""
    if llm_client is None:
        return "Style analysis unavailable - no LLM configured"
    
    try:
        pil_image = Image.fromarray(image_array)
        
        if isinstance(llm_client, dict) and llm_client.get("type") == "moondream":
            # Use Moondream for style analysis
            model = llm_client["model"]
            prompt = ("Describe the artistic style of this image in detail. "
                     "Focus on color palette, composition, artistic technique, "
                     "mood, and visual elements. Be specific about the style characteristics.")
            
            response = model.query(pil_image, prompt)
            return response.get('answer', 'Unable to analyze style')
        else:
            # This would be handled differently for OpenAI - we'll implement async version
            return "Style analysis pending..."
            
    except Exception as e:
        return f"Error analyzing style: {str(e)}"

@daft.func(return_dtype=daft.DataType.string())
def extract_dominant_colors(image_array) -> str:
    """Extract dominant colors from an image and return as comma-separated string"""
    try:
        pil_image = Image.fromarray(image_array)
        
        # Convert to RGB if necessary
        if pil_image.mode != 'RGB':
            pil_image = pil_image.convert('RGB')
        
        # Resize for faster processing
        pil_image = pil_image.resize((150, 150))
        
        # Get pixel data
        pixels = list(pil_image.getdata())
        
        # Simple color clustering - get most common colors
        from collections import Counter
        color_counts = Counter(pixels)
        
        # Get top 5 colors and convert to hex
        dominant_colors = []
        for (r, g, b), count in color_counts.most_common(5):
            hex_color = f"#{r:02x}{g:02x}{b:02x}"
            dominant_colors.append(hex_color)
        
        # Return as comma-separated string to avoid list type issues
        return ",".join(dominant_colors)
        
    except Exception as e:
        return f"Error: {str(e)}"

async def analyze_image_with_openai(image_array: np.ndarray) -> tuple[str, List[str]]:
    """Analyze image style using OpenAI Vision API"""
    if not llm_client or not hasattr(llm_client, 'chat'):
        return "OpenAI not available", []
    
    try:
        # Convert numpy array to PIL Image
        pil_image = Image.fromarray(image_array)
        
        # Convert to base64 for API
        buffered = BytesIO()
        pil_image.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        response = await llm_client.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": """Analyze this image's artistic style in detail. Please provide:
1. Overall artistic style (e.g., impressionist, modern, photorealistic, etc.)
2. Color palette characteristics
3. Composition and visual elements
4. Mood and atmosphere
5. Notable artistic techniques used

Format your response as a detailed but concise style description."""
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{img_str}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=300
        )
        
        style_description = response.choices[0].message.content
        
        # Extract artistic elements (simple keyword extraction)
        artistic_elements = []
        keywords = ["abstract", "realistic", "impressionist", "modern", "classic", "vibrant", "muted", "dramatic", "subtle", "geometric", "organic"]
        for keyword in keywords:
            if keyword.lower() in style_description.lower():
                artistic_elements.append(keyword)
        
        return style_description, artistic_elements
        
    except Exception as e:
        return f"Error with OpenAI analysis: {str(e)}", []

# In-memory storage (replace with database in production)
canvas_states: Dict[str, CanvasState] = {}
chat_messages: Dict[str, List[ChatMessage]] = {}
active_connections: Dict[str, List[WebSocket]] = {}

# Canvas State Endpoints
@app.post("/api/cs", response_model=CanvasState)
async def create_canvas():
    """Create a new canvas workspace"""
    canvas_id = str(uuid.uuid4())
    canvas_state = CanvasState(
        id=canvas_id,
        lastModified=datetime.now()
    )
    canvas_states[canvas_id] = canvas_state
    chat_messages[canvas_id] = []
    active_connections[canvas_id] = []
    return canvas_state

@app.get("/api/canvas/{canvas_id}", response_model=CanvasState)
async def get_canvas(canvas_id: str):
    """Get canvas state by ID"""
    if canvas_id not in canvas_states:
        raise HTTPException(status_code=404, detail="Canvas not found")
    return canvas_states[canvas_id]

@app.put("/api/canvas/{canvas_id}", response_model=CanvasState)
async def update_canvas(canvas_id: str, canvas_state: CanvasState):
    """Update entire canvas state"""
    if canvas_id not in canvas_states:
        raise HTTPException(status_code=404, detail="Canvas not found")
    
    canvas_state.id = canvas_id
    canvas_state.lastModified = datetime.now()
    canvas_states[canvas_id] = canvas_state
    
    # Broadcast to all connected clients
    await broadcast_to_canvas(canvas_id, {
        "type": "canvas_update",
        "data": canvas_state.dict(),
        "canvasId": canvas_id
    })
    
    return canvas_state

@app.post("/api/canvas/{canvas_id}/images", response_model=ImageNode)
async def add_image(canvas_id: str, image: ImageNode):
    """Add a new image to the canvas"""
    if canvas_id not in canvas_states:
        raise HTTPException(status_code=404, detail="Canvas not found")
    
    image.id = str(uuid.uuid4())
    canvas_states[canvas_id].images.append(image)
    canvas_states[canvas_id].lastModified = datetime.now()
    
    # Broadcast to all connected clients
    await broadcast_to_canvas(canvas_id, {
        "type": "image_added",
        "data": image.dict(),
        "canvasId": canvas_id
    })
    
    return image

@app.delete("/api/canvas/{canvas_id}/images/{image_id}")
async def delete_image(canvas_id: str, image_id: str):
    """Delete an image from the canvas"""
    if canvas_id not in canvas_states:
        raise HTTPException(status_code=404, detail="Canvas not found")
    
    canvas_state = canvas_states[canvas_id]
    canvas_state.images = [img for img in canvas_state.images if img.id != image_id]
    canvas_state.lastModified = datetime.now()
    
    # Remove from groups
    for group in canvas_state.groups:
        if image_id in group.imageIds:
            group.imageIds.remove(image_id)
    
    # Remove empty groups
    canvas_state.groups = [group for group in canvas_state.groups if len(group.imageIds) >= 2]
    
    # Broadcast to all connected clients
    await broadcast_to_canvas(canvas_id, {
        "type": "image_deleted",
        "data": {"imageId": image_id},
        "canvasId": canvas_id
    })
    
    return {"status": "deleted"}

@app.post("/api/canvas/{canvas_id}/groups", response_model=ImageGroup)
async def create_group(canvas_id: str, image_ids: List[str]):
    """Group selected images together"""
    if canvas_id not in canvas_states:
        raise HTTPException(status_code=404, detail="Canvas not found")
    
    if len(image_ids) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 images to create a group")
    
    canvas_state = canvas_states[canvas_id]
    
    # Verify all images exist
    existing_image_ids = {img.id for img in canvas_state.images}
    if not all(img_id in existing_image_ids for img_id in image_ids):
        raise HTTPException(status_code=400, detail="One or more images not found")
    
    # Remove images from existing groups
    for group in canvas_state.groups:
        group.imageIds = [img_id for img_id in group.imageIds if img_id not in image_ids]
    
    # Remove empty groups
    canvas_state.groups = [group for group in canvas_state.groups if len(group.imageIds) >= 2]
    
    # Create new group
    group_id = str(uuid.uuid4())
    new_group = ImageGroup(
        id=group_id,
        imageIds=image_ids,
        name=f"Group {len(canvas_state.groups) + 1}"
    )
    
    canvas_state.groups.append(new_group)
    
    # Update image groupIds
    for image in canvas_state.images:
        if image.id in image_ids:
            image.groupId = group_id
    
    canvas_state.lastModified = datetime.now()
    
    # Broadcast to all connected clients
    await broadcast_to_canvas(canvas_id, {
        "type": "images_grouped",
        "data": new_group.dict(),
        "canvasId": canvas_id
    })
    
    return new_group

@app.delete("/api/canvas/{canvas_id}/groups/{group_id}")
async def delete_group(canvas_id: str, group_id: str):
    """Ungroup images"""
    if canvas_id not in canvas_states:
        raise HTTPException(status_code=404, detail="Canvas not found")
    
    canvas_state = canvas_states[canvas_id]
    
    # Find and remove the group
    group_to_remove = None
    for i, group in enumerate(canvas_state.groups):
        if group.id == group_id:
            group_to_remove = canvas_state.groups.pop(i)
            break
    
    if not group_to_remove:
        raise HTTPException(status_code=404, detail="Group not found")
    
    # Update image groupIds
    for image in canvas_state.images:
        if image.groupId == group_id:
            image.groupId = None
    
    canvas_state.lastModified = datetime.now()
    
    # Broadcast to all connected clients
    await broadcast_to_canvas(canvas_id, {
        "type": "images_ungrouped",
        "data": {"groupId": group_id, "imageIds": group_to_remove.imageIds},
        "canvasId": canvas_id
    })
    
    return {"status": "ungrouped", "imageIds": group_to_remove.imageIds}

# Chat Endpoints
@app.get("/api/canvas/{canvas_id}/messages", response_model=List[ChatMessage])
async def get_messages(canvas_id: str, limit: int = 50):
    """Get chat messages for a canvas"""
    if canvas_id not in chat_messages:
        return []
    return chat_messages[canvas_id][-limit:]

@app.post("/api/canvas/{canvas_id}/messages", response_model=ChatMessage)
async def send_message(canvas_id: str, text: str, sender: str = "User"):
    """Send a chat message"""
    if canvas_id not in chat_messages:
        chat_messages[canvas_id] = []
    
    message = ChatMessage(
        id=str(uuid.uuid4()),
        text=text,
        sender=sender,
        timestamp=datetime.now(),
        canvasId=canvas_id
    )
    
    chat_messages[canvas_id].append(message)
    
    # Broadcast to all connected clients
    await broadcast_to_canvas(canvas_id, {
        "type": "chat_message",
        "data": message.dict(),
        "canvasId": canvas_id
    })
    
    return message

# File Upload Endpoint
@app.post("/api/upload")
async def upload_image(file: UploadFile = File(...)):
    """Upload an image file and return a data URL"""
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Read file content
    content = await file.read()
    
    # Convert to base64 data URL
    base64_content = base64.b64encode(content).decode('utf-8')
    data_url = f"data:{file.content_type};base64,{base64_content}"
    
    return {"dataUrl": data_url, "filename": file.filename}

# Style Analysis Endpoints
@app.post("/api/analyze-image")
async def analyze_uploaded_image(file: UploadFile = File(...), canvas_id: str = "default"):
    """Upload an image and store it in Daft DataFrame for style analysis"""
    global image_analysis_df
    
    print(f"📤 Image upload request: {file.filename}, canvas: {canvas_id}")
    
    try:
        if not file.content_type.startswith('image/'):
            print(f"❌ Invalid file type: {file.content_type}")
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read image file
        contents = await file.read()
        
        # Convert to PIL Image and then to numpy array
        pil_image = Image.open(BytesIO(contents))
        if pil_image.mode != 'RGB':
            pil_image = pil_image.convert('RGB')
        
        image_array = np.array(pil_image)
        
        # Generate unique ID
        image_id = str(uuid.uuid4())
        timestamp = datetime.now()
        
        # Create new row data with consistent schema
        new_data = {
            "id": [image_id],
            "filename": [file.filename or "unknown"],
            "canvas_id": [canvas_id],
            "image_data": [image_array],
            "timestamp": [timestamp],
            "style_description": [""],  # Will be filled by analysis
            "dominant_colors": ["#000000"],  # String instead of list to avoid schema issues
            "artistic_elements": ["unknown"]   # String instead of list to avoid schema issues
        }
        
        # Create DataFrame from new data and concatenate
        print("📊 Creating Daft DataFrame from uploaded image")
        new_df = daft.from_pydict(new_data)
        
        if image_analysis_df is None:
            print("🔧 Initializing Daft DataFrame with first image")
            image_analysis_df = new_df
        else:
            print("🔧 Concatenating image to existing Daft DataFrame")
            image_analysis_df = image_analysis_df.concat(new_df)
        
        print(f"✅ Image stored in Daft. Total images: {image_analysis_df.count_rows()}")
        
        # Convert to base64 data URL for frontend
        base64_content = base64.b64encode(contents).decode('utf-8')
        data_url = f"data:{file.content_type};base64,{base64_content}"
        
        return {
            "message": "Image uploaded successfully for analysis",
            "image_id": image_id,
            "filename": file.filename,
            "timestamp": timestamp.isoformat(),
            "dataUrl": data_url,
            "canvas_id": canvas_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error uploading image: {str(e)}")

@app.post("/api/analyze-styles")
async def analyze_styles(request: StyleAnalysisRequest, canvas_id: str = "default"):
    """Analyze styles for specified images using LLM"""
    global image_analysis_df
    
    print(f"🔍 Style analysis request for canvas: {canvas_id}, image_ids: {request.image_ids}")
    
    try:
        if image_analysis_df is None:
            print("❌ No Daft DataFrame initialized")
            raise HTTPException(status_code=404, detail="No images found for analysis")
            
        total_rows = image_analysis_df.count_rows()
        print(f"📊 Total images in Daft: {total_rows}")
        
        if total_rows == 0:
            print("❌ Daft DataFrame is empty")
            raise HTTPException(status_code=404, detail="No images found for analysis")
        
        # Filter images by canvas_id (simplify for now - analyze all images in canvas)
        print(f"🔍 Filtering by canvas_id: {canvas_id}")
        filtered_df = image_analysis_df.filter(col("canvas_id") == canvas_id)
        filtered_count = filtered_df.count_rows()
        print(f"📊 Filtered images count: {filtered_count}")
        
        if filtered_count == 0:
            print("❌ No images found for this canvas")
            raise HTTPException(status_code=404, detail="No matching images found for analysis")
        
        print("🧠 Starting LLM style analysis...")
        # Apply style analysis using Daft UDFs - simplified approach
        try:
            print("🔍 Step 1: Adding style description...")
            analyzed_df = filtered_df.with_column("style_description", analyze_image_style(col("image_data")))
            print("✅ Step 1 completed")
            
            print("🔍 Step 2: Adding dominant colors...")
            analyzed_df = analyzed_df.with_column("dominant_colors", extract_dominant_colors(col("image_data")))
            print("✅ Step 2 completed")
            
            print("✅ Style analysis completed")
        except Exception as analysis_error:
            print(f"❌ Analysis error: {str(analysis_error)}")
            print(f"Analysis error type: {type(analysis_error)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            raise Exception(f"Style analysis failed: {str(analysis_error)}")
        
        # For simplicity, just replace the entire DataFrame (in production you'd want incremental updates)
        print("💾 Updating global DataFrame with analysis results")
        image_analysis_df = analyzed_df
        
        # Collect results using proper Daft API
        print("📋 Collecting analysis results...")
        try:
            # Use to_pandas() to get actual data values (not Expression objects)
            print("🔍 Converting DataFrame to pandas...")
            pandas_df = analyzed_df.to_pandas()
            print(f"✅ Pandas conversion successful: {len(pandas_df)} rows")
            
            # Convert to list of dictionaries
            results = pandas_df.to_dict('records')
            print(f"✅ Results processed: {len(results)} items")
            
        except Exception as collect_error:
            print(f"❌ Error collecting results: {str(collect_error)}")
            print(f"Error type: {type(collect_error)}")
            import traceback
            print(f"Full traceback: {traceback.format_exc()}")
            raise Exception(f"Failed to collect analysis results: {str(collect_error)}")
        
        # Send style analysis results via WebSocket to canvas
        print("📡 Broadcasting WebSocket results...")
        try:
            for result in results:
                if result["style_description"] and result["style_description"] != "":
                    # Convert comma-separated color string to array for WebSocket
                    color_array = result["dominant_colors"].split(",") if result["dominant_colors"] and "," in result["dominant_colors"] else [result["dominant_colors"]] if result["dominant_colors"] else []
                    
                    await broadcast_to_canvas(canvas_id, {
                        "type": "style_analysis_complete",
                        "data": {
                            "image_id": result["id"],
                            "filename": result["filename"],
                            "style_description": result["style_description"],
                            "dominant_colors": color_array
                        },
                        "canvasId": canvas_id
                    })
            print("✅ WebSocket broadcast completed")
        except Exception as broadcast_error:
            print(f"❌ WebSocket broadcast error: {str(broadcast_error)}")
            # Don't fail the entire request if WebSocket fails
            pass
        
        # Format final response
        print("📄 Formatting final response...")
        try:
            response_data = {
                "message": "Style analysis completed",
                "analyzed_count": len(results),
                "canvas_id": canvas_id,
                "results": [
                    {
                        "id": row["id"],
                        "filename": row["filename"],
                        "style_description": row["style_description"],
                        "dominant_colors": row["dominant_colors"].split(",") if row["dominant_colors"] and "," in row["dominant_colors"] else [row["dominant_colors"]] if row["dominant_colors"] else [],
                        "timestamp": row["timestamp"]
                    }
                    for row in results
                ]
            }
            print("✅ Response formatted successfully")
            return response_data
        except Exception as format_error:
            print(f"❌ Response formatting error: {str(format_error)}")
            print(f"Error details: {type(format_error)} - {str(format_error)}")
            print(f"Results data: {results}")
            raise Exception(f"Failed to format response: {str(format_error)}")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing styles: {str(e)}")

@app.get("/api/canvas/{canvas_id}/analyzed-images")
async def get_analyzed_images(canvas_id: str):
    """Get all analyzed images for a specific canvas"""
    global image_analysis_df
    
    try:
        if image_analysis_df.count_rows() == 0:
            return {"images": [], "count": 0}
        
        # Filter by canvas_id and get analyzed images
        canvas_images = image_analysis_df.filter(
            (col("canvas_id") == canvas_id) & 
            (col("style_description") != "")
        )
        
        if canvas_images.count_rows() == 0:
            return {"images": [], "count": 0}
        
        # Collect data (excluding the actual image arrays for API response)
        results = canvas_images.select([
            col("id"),
            col("filename"), 
            col("timestamp"),
            col("style_description"),
            col("dominant_colors"),
            col("artistic_elements")
        ]).collect()
        
        return {
            "images": results,
            "count": len(results),
            "canvas_id": canvas_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving analyzed images: {str(e)}")

@app.delete("/api/canvas/{canvas_id}/analyzed-images/{image_id}")
async def delete_analyzed_image(canvas_id: str, image_id: str):
    """Delete a specific analyzed image from the DataFrame"""
    global image_analysis_df
    
    try:
        if image_analysis_df.count_rows() == 0:
            raise HTTPException(status_code=404, detail="No analyzed images found")
        
        # Filter out the image to delete
        image_analysis_df = image_analysis_df.filter(
            ~((col("id") == image_id) & (col("canvas_id") == canvas_id))
        )
        
        return {"message": f"Analyzed image {image_id} deleted successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting analyzed image: {str(e)}")

# WebSocket for Real-time Collaboration
@app.websocket("/ws/{canvas_id}")
async def websocket_endpoint(websocket: WebSocket, canvas_id: str):
    await websocket.accept()
    
    # Add connection to active connections
    if canvas_id not in active_connections:
        active_connections[canvas_id] = []
    active_connections[canvas_id].append(websocket)
    
    try:
        # Send current canvas state
        if canvas_id in canvas_states:
            await websocket.send_json({
                "type": "canvas_state",
                "data": canvas_states[canvas_id].dict(),
                "canvasId": canvas_id
            })
        
        # Notify others that a user joined
        await broadcast_to_canvas(canvas_id, {
            "type": "user_joined",
            "data": {"message": "A user joined the canvas"},
            "canvasId": canvas_id
        }, exclude_websocket=websocket)
        
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Broadcast message to other clients
            await broadcast_to_canvas(canvas_id, message, exclude_websocket=websocket)
            
    except WebSocketDisconnect:
        # Remove connection
        active_connections[canvas_id].remove(websocket)
        
        # Notify others that user left
        await broadcast_to_canvas(canvas_id, {
            "type": "user_left",
            "data": {"message": "A user left the canvas"},
            "canvasId": canvas_id
        })

async def broadcast_to_canvas(canvas_id: str, message: Dict[str, Any], exclude_websocket: WebSocket = None):
    """Broadcast a message to all connected clients for a canvas"""
    if canvas_id not in active_connections:
        return
    
    disconnected = []
    for websocket in active_connections[canvas_id]:
        if websocket == exclude_websocket:
            continue
        
        try:
            await websocket.send_json(message)
        except:
            disconnected.append(websocket)
    
    # Remove disconnected websockets
    for websocket in disconnected:
        active_connections[canvas_id].remove(websocket)

# Health Check
@app.get("/health")
async def health_check():
    global image_analysis_df
    
    analyzed_count = 0
    total_images = 0
    if image_analysis_df is not None:
        total_images = image_analysis_df.count_rows()
        if total_images > 0:
            analyzed_images = image_analysis_df.filter(col("style_description") != "")
            analyzed_count = analyzed_images.count_rows()
    
    return {
        "status": "healthy", 
        "canvases": len(canvas_states),
        "llm_available": llm_client is not None,
        "total_images": total_images,
        "total_analyzed_images": analyzed_count,
        "daft_initialized": image_analysis_df is not None
    }

# Debug/Inspection Endpoints for Testing
@app.get("/debug/daft-summary")
async def get_daft_summary():
    """Get summary of data stored in Daft DataFrame"""
    global image_analysis_df
    
    if image_analysis_df is None:
        return {"error": "Daft DataFrame not initialized"}
    
    try:
        if image_analysis_df is None:
            return {
                "total_images": 0,
                "analyzed_images": 0,
                "pending_analysis": 0,
                "sample_data": []
            }
            
        total_rows = image_analysis_df.count_rows()
        
        if total_rows == 0:
            return {
                "total_images": 0,
                "analyzed_images": 0,
                "pending_analysis": 0,
                "sample_data": []
            }
        
        # Get basic statistics
        analyzed_images = image_analysis_df.filter(col("style_description") != "").count_rows()
        pending_analysis = total_rows - analyzed_images
        
        # Get sample data (first 5 rows)
        sample_df = image_analysis_df.select([
            col("id"),
            col("filename"),
            col("canvas_id"), 
            col("timestamp"),
            col("style_description")
        ]).limit(5)
        sample_data = sample_df.to_pandas().to_dict('records')
        
        return {
            "total_images": total_rows,
            "analyzed_images": analyzed_images,
            "pending_analysis": pending_analysis,
            "sample_data": sample_data
        }
        
    except Exception as e:
        return {"error": f"Error accessing Daft data: {str(e)}"}

@app.get("/debug/daft-raw")
async def get_daft_raw_data():
    """Get raw data from Daft DataFrame (excluding image arrays)"""
    global image_analysis_df
    
    if image_analysis_df is None:
        return {"error": "Daft DataFrame not initialized"}
    
    try:
        if image_analysis_df is None or image_analysis_df.count_rows() == 0:
            return {"message": "No data in Daft DataFrame", "data": []}
        
        # Get all data except image arrays (which would be too large)
        selected_df = image_analysis_df.select([
            col("id"),
            col("filename"),
            col("canvas_id"),
            col("timestamp"),
            col("style_description"),
            col("dominant_colors"),
            col("artistic_elements")
        ])
        raw_data = selected_df.to_pandas().to_dict('records')
        
        return {
            "message": "Raw Daft DataFrame data",
            "count": len(raw_data),
            "data": raw_data
        }
        
    except Exception as e:
        return {"error": f"Error retrieving raw data: {str(e)}"}

@app.post("/debug/simple-test")
async def simple_connection_test():
    """Simple test to verify frontend-backend connection"""
    return {
        "message": "Frontend-backend connection working!",
        "backend_status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/debug/simple-upload")
async def simple_image_upload(file: UploadFile = File(...)):
    """Simple image upload test without Daft complexity"""
    try:
        contents = await file.read()
        image_id = str(uuid.uuid4())
        
        # Simple success response
        return {
            "message": "Image upload successful!",
            "image_id": image_id,
            "filename": file.filename,
            "size_bytes": len(contents),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"error": f"Upload failed: {str(e)}"}

@app.post("/debug/basic-daft-test")
async def basic_daft_test():
    """Test basic Daft operations without UDFs"""
    try:
        print("🧪 Testing basic Daft operations...")
        
        # Create simple test data
        test_data = {
            "id": ["test-123"],
            "name": ["test-image.jpg"],
            "description": ["A simple test"]
        }
        
        print("📊 Creating test DataFrame...")
        test_df = daft.from_pydict(test_data)
        
        print("📋 Collecting test results...")
        results = test_df.to_pandas().to_dict('records')
        
        print(f"✅ Test successful: {len(results)} rows")
        
        return {
            "message": "Basic Daft test successful!",
            "results": results
        }
        
    except Exception as e:
        print(f"❌ Basic Daft test failed: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return {"error": f"Basic Daft test failed: {str(e)}"}

@app.post("/debug/simple-analysis")
async def simple_analysis_test():
    """Test analysis without complex UDFs"""
    global image_analysis_df
    
    try:
        if image_analysis_df is None or image_analysis_df.count_rows() == 0:
            return {"error": "No images to analyze"}
        
        print("🧪 Testing simple analysis without UDFs...")
        
        # Try to just collect existing data without UDFs
        print("📋 Collecting existing data...")
        existing_data = image_analysis_df.to_pandas().to_dict('records')
        print(f"✅ Collected {len(existing_data)} rows")
        
        # Try to add a simple string column instead of UDF
        print("🔍 Adding simple test column...")
        test_df = image_analysis_df.with_column("test_column", "test_value")
        
        print("📋 Collecting test results...")
        test_results = test_df.to_pandas().to_dict('records')
        print(f"✅ Test results: {len(test_results)} rows")
        
        return {
            "message": "Simple analysis test successful!",
            "original_count": len(existing_data),
            "test_count": len(test_results)
        }
        
    except Exception as e:
        print(f"❌ Simple analysis test failed: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return {"error": f"Simple analysis test failed: {str(e)}"}

@app.post("/debug/test-analysis")
async def test_style_analysis():
    """Test the style analysis pipeline with a simple image"""
    try:
        # Create a simple test image (red square)
        import numpy as np
        from PIL import Image
        
        # Create a 100x100 red image
        test_image = np.full((100, 100, 3), [255, 0, 0], dtype=np.uint8)
        
        # Generate test data
        image_id = str(uuid.uuid4())
        timestamp = datetime.now()
        
        # Create test row
        test_data = {
            "id": [image_id],
            "filename": ["test-red-square.png"],
            "canvas_id": ["test-canvas"],
            "image_data": [test_image],
            "timestamp": [timestamp],
            "style_description": [""],
            "dominant_colors": [[]],
            "artistic_elements": [[]]
        }
        
        # Add to Daft DataFrame
        global image_analysis_df
        test_df = daft.from_pydict(test_data)
        
        if image_analysis_df.count_rows() == 0:
            image_analysis_df = test_df
        else:
            image_analysis_df = image_analysis_df.concat(test_df)
        
        # Run style analysis
        analyzed_df = (
            test_df
            .with_column("style_description", analyze_image_style(col("image_data")))
            .with_column("dominant_colors", extract_dominant_colors(col("image_data")))
        )
        
        result = analyzed_df.select([
            col("id"),
            col("filename"),
            col("style_description"),
            col("dominant_colors")
        ]).collect()[0]
        
        return {
            "message": "Test analysis completed",
            "test_image_id": image_id,
            "result": result
        }
        
    except Exception as e:
        return {"error": f"Test analysis failed: {str(e)}"}

@app.delete("/debug/clear-daft")
async def clear_daft_data():
    """Clear all data from Daft DataFrame (for testing)"""
    global image_analysis_df
    
    try:
        image_analysis_df = None  # Reset to None
        return {"message": "Daft DataFrame cleared successfully"}
        
    except Exception as e:
        return {"error": f"Error clearing Daft data: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
