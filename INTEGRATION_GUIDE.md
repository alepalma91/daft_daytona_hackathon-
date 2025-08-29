# Integration Guide: Frontend + FastAPI Backend

## 🚀 Quick Start

### 1. Start the Backend API

```bash
cd backend
pip install -r requirements.txt
python start.py
```

The API will be running at `http://localhost:8000`

### 2. Start the Frontend

```bash
cd image-canvas
npm install
npm run dev
```

The frontend will be running at `http://localhost:5173`

## 🔗 Integration Points

### Current State vs. Enhanced State

| Feature | Current (Frontend Only) | With FastAPI Backend |
|---------|-------------------------|----------------------|
| **Canvas State** | Local browser storage | Persistent database storage |
| **Chat Messages** | Local array | Real-time chat with history |
| **Image Upload** | File picker only | File upload + URL storage |
| **Collaboration** | Single user | Multi-user real-time |
| **Image Grouping** | Local state | Persistent groups |
| **Canvas Sharing** | Not possible | Shareable canvas URLs |

## 🎯 Key Integration Examples

### 1. Enhanced Chat System

**Before (Local Only):**
```typescript
// main.ts
private addChatMessage(sender: string, text: string): void {
  const message: ChatMessage = {
    id: crypto.randomUUID(),
    text,
    timestamp: Date.now()
  };
  this.chatMessages.push(message);
  this.updateChatDisplay();
}
```

**After (With API):**
```typescript
import { canvasAPI } from './api';

private async addChatMessage(sender: string, text: string): Promise<void> {
  try {
    // Send to backend and get response
    const message = await canvasAPI.sendMessage(text, sender);
    this.chatMessages.push(message);
    this.updateChatDisplay();
  } catch (error) {
    console.error('Failed to send message:', error);
  }
}

// Real-time message receiving
private setupRealTimeChat(): void {
  canvasAPI.connectWebSocket({
    onChatMessage: (message) => {
      this.chatMessages.push(message);
      this.updateChatDisplay();
    }
  });
}
```

### 2. Persistent Canvas State

**Before (Local Only):**
```typescript
// Canvas state lost on page refresh
```

**After (With API):**
```typescript
// Save canvas state to backend
private async saveCanvasState(): Promise<void> {
  const canvasState = {
    id: this.canvasId,
    images: this.canvas.getAllImages(),
    groups: this.canvas.getAllGroups(),
    viewport: this.canvas.getViewport(),
    lastModified: new Date()
  };
  
  await canvasAPI.updateCanvas(canvasState);
}

// Load canvas state from backend
private async loadCanvasState(canvasId: string): Promise<void> {
  const canvasState = await canvasAPI.getCanvas(canvasId);
  this.canvas.loadState(canvasState);
}
```

### 3. Real-time Collaboration

```typescript
// Set up real-time collaboration
private setupCollaboration(): void {
  canvasAPI.connectWebSocket({
    onCanvasUpdate: (canvasState) => {
      // Update canvas when others make changes
      this.canvas.loadState(canvasState);
    },
    
    onUserJoined: (message) => {
      this.addChatMessage('System', message);
    },
    
    onImageAdded: (image) => {
      this.canvas.addImageFromData(image);
    },
    
    onImagesGrouped: (group) => {
      this.canvas.createGroupFromData(group);
    }
  });
}
```

## 📡 API Endpoints Summary

### Canvas Management
- `POST /api/canvas` - Create new canvas
- `GET /api/canvas/{id}` - Load canvas
- `PUT /api/canvas/{id}` - Save canvas

### Real-time Features  
- `WS /ws/{canvas_id}` - WebSocket connection
- Auto-sync canvas changes
- Multi-user chat
- Live cursors (can be added)

### Enhanced Features
- `POST /api/upload` - Upload images
- `GET /api/canvas/{id}/messages` - Chat history
- Persistent image grouping
- Canvas sharing via URL

## 🎨 Frontend Integration Steps

### Step 1: Update Main Application

```typescript
// main.ts - Add API integration
import { canvasAPI } from './api';

class ImageCanvasApp {
  private canvasId: string | null = null;
  
  async initialize(): Promise<void> {
    // Create or load canvas
    const urlParams = new URLSearchParams(window.location.search);
    const canvasId = urlParams.get('canvas');
    
    if (canvasId) {
      // Load existing canvas
      await this.loadCanvas(canvasId);
    } else {
      // Create new canvas
      await this.createNewCanvas();
    }
    
    // Setup real-time collaboration
    this.setupRealTimeFeatures();
  }
}
```

### Step 2: Add Collaboration Features

```typescript
// Enable real-time features
private setupRealTimeFeatures(): void {
  canvasAPI.connectWebSocket({
    onCanvasUpdate: this.handleCanvasUpdate.bind(this),
    onChatMessage: this.handleChatMessage.bind(this),
    onUserJoined: this.handleUserJoined.bind(this)
  });
}
```

### Step 3: Enhanced File Upload

```typescript
// Add server-side file upload
private async handleFileUpload(file: File): Promise<void> {
  try {
    const dataUrl = await canvasAPI.uploadImage(file);
    await this.canvas.addImage(dataUrl);
    await this.saveCanvasState();
  } catch (error) {
    this.addChatMessage('System', `Upload failed: ${error.message}`);
  }
}
```

## 🌐 Deployment

### Development
- Frontend: `npm run dev` (http://localhost:5173)
- Backend: `python start.py` (http://localhost:8000)

### Production
- Frontend: Build with `npm run build` and serve static files
- Backend: Deploy with `gunicorn` or `uvicorn` on a server
- Add database (PostgreSQL/MongoDB) for persistent storage
- Add Redis for WebSocket scaling

## 🔧 Configuration

### Environment Variables (Backend)
```bash
# .env file
DATABASE_URL=postgresql://user:pass@localhost/canvasdb
REDIS_URL=redis://localhost:6379
CORS_ORIGINS=http://localhost:5173,https://yourapp.com
```

### Frontend Configuration
```typescript
// config.ts
export const API_CONFIG = {
  BASE_URL: process.env.NODE_ENV === 'production' 
    ? 'https://api.yourapp.com' 
    : 'http://localhost:8000',
  WS_URL: process.env.NODE_ENV === 'production'
    ? 'wss://api.yourapp.com/ws'
    : 'ws://localhost:8000/ws'
};
```

## ✨ New Features Enabled

1. **🔗 Shareable Canvas URLs**: Share canvas with `?canvas=canvas_id`
2. **💬 Persistent Chat**: Messages saved and loaded with canvas
3. **👥 Multi-user Collaboration**: See other users' changes in real-time
4. **📁 File Upload to Server**: Images stored on backend
5. **🔄 Auto-save**: Canvas state automatically synced
6. **📱 Cross-device**: Access same canvas from multiple devices

## 🚀 Ready to Integrate!

Your image canvas workspace is now ready for real-time collaboration, persistent storage, and multi-user functionality!
