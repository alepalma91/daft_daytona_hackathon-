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
import re
import aiohttp
from openai import AsyncOpenAI

app = FastAPI(title="Image Canvas Workspace API", version="1.0.0")

# Initialize OpenAI client
openai_client = AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
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

class ImageGenerationRequest(BaseModel):
    prompt: str
    size: str = "1024x1024"  # DALL-E 3 sizes: 1024x1024, 1792x1024, 1024x1792
    quality: str = "standard"  # "standard" or "hd"
    style: str = "vivid"  # "vivid" or "natural"

class ImageGenerationResponse(BaseModel):
    id: str
    prompt: str
    imageUrl: str
    revisedPrompt: Optional[str] = None

# In-memory storage (replace with database in production)
canvas_states: Dict[str, CanvasState] = {}
chat_messages: Dict[str, List[ChatMessage]] = {}
active_connections: Dict[str, List[WebSocket]] = {}

# Helper functions for image generation
def detect_generation_command(text: str) -> Optional[str]:
    """Detect if a chat message is requesting image generation"""
    generation_patterns = [
        r"^generate\s+(.+)$",
        r"^create\s+(?:an?\s+)?image\s+of\s+(.+)$",
        r"^draw\s+(.+)$",
        r"^make\s+(?:an?\s+)?image\s+of\s+(.+)$",
        r"^/imagine\s+(.+)$",
        r"^imagine\s+(.+)$"
    ]
    
    text_lower = text.lower().strip()
    for pattern in generation_patterns:
        match = re.match(pattern, text_lower)
        if match:
            return match.group(1).strip()
    return None

def enhance_prompt(prompt: str) -> str:
    """Enhance the user prompt for better DALL-E 3 results"""
    # Add quality descriptors if not present
    quality_words = ["high quality", "detailed", "professional", "4k", "hd"]
    if not any(word in prompt.lower() for word in quality_words):
        prompt += ", high quality, detailed"
    
    return prompt

async def download_and_convert_image(image_url: str) -> str:
    """Download image from URL and convert to base64 data URL"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as response:
                if response.status == 200:
                    image_data = await response.read()
                    # Determine content type
                    content_type = response.headers.get('content-type', 'image/png')
                    # Convert to base64
                    base64_data = base64.b64encode(image_data).decode('utf-8')
                    return f"data:{content_type};base64,{base64_data}"
                else:
                    raise HTTPException(status_code=400, detail="Failed to download generated image")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing generated image: {str(e)}")

async def generate_dalle_image(prompt: str, size: str = "1024x1024", quality: str = "standard", style: str = "vivid") -> ImageGenerationResponse:
    """Generate image using OpenAI DALL-E 3"""
    if not openai_client.api_key:
        raise HTTPException(status_code=500, detail="OpenAI API key not configured")
    
    try:
        enhanced_prompt = enhance_prompt(prompt)
        
        response = await openai_client.images.generate(
            model="dall-e-3",
            prompt=enhanced_prompt,
            size=size,
            quality=quality,
            style=style,
            n=1
        )
        
        image_data = response.data[0]
        image_url = image_data.url
        
        # Download and convert to base64 for storage
        data_url = await download_and_convert_image(image_url)
        
        return ImageGenerationResponse(
            id=str(uuid.uuid4()),
            prompt=prompt,
            imageUrl=data_url,
            revisedPrompt=getattr(image_data, 'revised_prompt', None)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image generation failed: {str(e)}")

# Canvas State Endpoints
@app.post("/api/canvas", response_model=CanvasState)
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
    """Send a chat message and check for image generation commands"""
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
    
    # Check if message is an image generation command
    generation_prompt = detect_generation_command(text)
    if generation_prompt:
        # Trigger image generation asynchronously
        asyncio.create_task(handle_image_generation_command(canvas_id, generation_prompt, sender))
    
    return message

async def handle_image_generation_command(canvas_id: str, prompt: str, sender: str = "System"):
    """Handle image generation from chat command"""
    try:
        # Notify that generation is starting
        progress_message = ChatMessage(
            id=str(uuid.uuid4()),
            text=f"🎨 Generating image: '{prompt}'...",
            sender="System",
            timestamp=datetime.now(),
            canvasId=canvas_id
        )
        
        chat_messages[canvas_id].append(progress_message)
        
        await broadcast_to_canvas(canvas_id, {
            "type": "chat_message", 
            "data": progress_message.dict(),
            "canvasId": canvas_id
        })
        
        await broadcast_to_canvas(canvas_id, {
            "type": "generation_started",
            "data": {"prompt": prompt},
            "canvasId": canvas_id
        })
        
        # Generate the image
        generated_image = await generate_dalle_image(prompt)
        
        # Add image to canvas
        if canvas_id in canvas_states:
            # Get canvas center for placement
            canvas_state = canvas_states[canvas_id]
            center_x = 0  # Center of the viewport
            center_y = 0
            
            # Create new image node
            image_node = ImageNode(
                id=generated_image.id,
                src=generated_image.imageUrl,
                x=center_x - 160,  # Half of typical width (320px)
                y=center_y - 120,  # Half of typical height
                w=320,
                h=240,  # Will be adjusted based on actual image dimensions
                selected=False
            )
            
            canvas_state.images.append(image_node)
            canvas_state.lastModified = datetime.now()
            
            # Success message
            success_text = f"✅ Image generated and added to canvas!"
            if generated_image.revisedPrompt and generated_image.revisedPrompt != prompt:
                success_text += f" (DALL-E refined: '{generated_image.revisedPrompt}')"
            
            success_message = ChatMessage(
                id=str(uuid.uuid4()),
                text=success_text,
                sender="System",
                timestamp=datetime.now(),
                canvasId=canvas_id
            )
            
            chat_messages[canvas_id].append(success_message)
            
            # Broadcast updates
            await broadcast_to_canvas(canvas_id, {
                "type": "chat_message",
                "data": success_message.dict(),
                "canvasId": canvas_id
            })
            
            await broadcast_to_canvas(canvas_id, {
                "type": "image_generated",
                "data": {
                    "image": image_node.dict(),
                    "generationId": generated_image.id,
                    "prompt": prompt,
                    "revisedPrompt": generated_image.revisedPrompt
                },
                "canvasId": canvas_id
            })
            
    except Exception as e:
        # Error message
        error_message = ChatMessage(
            id=str(uuid.uuid4()),
            text=f"❌ Failed to generate image: {str(e)}",
            sender="System", 
            timestamp=datetime.now(),
            canvasId=canvas_id
        )
        
        chat_messages[canvas_id].append(error_message)
        
        await broadcast_to_canvas(canvas_id, {
            "type": "chat_message",
            "data": error_message.dict(),
            "canvasId": canvas_id
        })
        
        await broadcast_to_canvas(canvas_id, {
            "type": "generation_failed",
            "data": {"error": str(e), "prompt": prompt},
            "canvasId": canvas_id
        })

# Image Generation Endpoint
@app.post("/api/canvas/{canvas_id}/generate-image", response_model=ImageGenerationResponse)
async def generate_image_endpoint(canvas_id: str, request: ImageGenerationRequest):
    """Generate an image using DALL-E 3 and optionally add to canvas"""
    if canvas_id not in canvas_states:
        raise HTTPException(status_code=404, detail="Canvas not found")
    
    try:
        # Generate the image
        generated_image = await generate_dalle_image(
            request.prompt, 
            request.size, 
            request.quality, 
            request.style
        )
        
        # Broadcast generation completed
        await broadcast_to_canvas(canvas_id, {
            "type": "image_generation_complete",
            "data": generated_image.dict(),
            "canvasId": canvas_id
        })
        
        return generated_image
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image generation failed: {str(e)}")

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
    return {"status": "healthy", "canvases": len(canvas_states)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
