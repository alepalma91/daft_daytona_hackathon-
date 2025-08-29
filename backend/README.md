# Image Canvas Workspace API

FastAPI backend for the Image Canvas Workspace application.

## Features

- **Canvas State Management**: Create, read, update canvas workspaces
- **Real-time Collaboration**: WebSocket connections for live updates
- **Image Management**: Add, delete, move images on canvas
- **Image Grouping**: Group/ungroup images with persistent state
- **Chat System**: Real-time chat for each canvas workspace
- **File Upload**: Upload images directly to the canvas
- **CORS Enabled**: Works with frontend development server

## API Endpoints

### Canvas Management
- `POST /api/canvas` - Create new canvas
- `GET /api/canvas/{canvas_id}` - Get canvas state
- `PUT /api/canvas/{canvas_id}` - Update canvas state

### Image Operations
- `POST /api/canvas/{canvas_id}/images` - Add image to canvas
- `DELETE /api/canvas/{canvas_id}/images/{image_id}` - Delete image

### Grouping Operations
- `POST /api/canvas/{canvas_id}/groups` - Create image group
- `DELETE /api/canvas/{canvas_id}/groups/{group_id}` - Ungroup images

### Chat System
- `GET /api/canvas/{canvas_id}/messages` - Get chat messages
- `POST /api/canvas/{canvas_id}/messages` - Send chat message

### File Upload
- `POST /api/upload` - Upload image file

### WebSocket
- `WS /ws/{canvas_id}` - Real-time collaboration

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the server:
```bash
python main.py
```

The API will be available at `http://localhost:8000`

## API Documentation

Visit `http://localhost:8000/docs` for interactive API documentation.

## Data Models

### ImageNode
```json
{
  "id": "uuid",
  "src": "image_url_or_data",
  "x": 100.0,
  "y": 200.0,
  "w": 300.0,
  "h": 200.0,
  "selected": false,
  "groupId": "optional_group_uuid"
}
```

### CanvasState
```json
{
  "id": "canvas_uuid",
  "images": [ImageNode],
  "groups": [ImageGroup],
  "viewport": {
    "scale": 1.0,
    "tx": 0.0,
    "ty": 0.0
  },
  "lastModified": "2025-01-01T00:00:00Z"
}
```

### ChatMessage
```json
{
  "id": "message_uuid",
  "text": "Hello world",
  "sender": "User",
  "timestamp": "2025-01-01T00:00:00Z",
  "canvasId": "canvas_uuid"
}
```
