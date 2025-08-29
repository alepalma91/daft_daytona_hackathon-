from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uuid
import json
import asyncio
from datetime import datetime
import base64

app = FastAPI(title="Image Canvas Workspace API", version="1.0.0")

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

# In-memory storage (replace with database in production)
canvas_states: Dict[str, CanvasState] = {}
chat_messages: Dict[str, List[ChatMessage]] = {}
active_connections: Dict[str, List[WebSocket]] = {}

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
