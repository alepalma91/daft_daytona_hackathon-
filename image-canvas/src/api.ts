import type { ImageNode, ImageGroup, CanvasState, ChatMessage } from './types';

const API_BASE_URL = 'http://localhost:8000/api';
const WS_BASE_URL = 'ws://localhost:8000/ws';

export class CanvasAPI {
  private canvasId: string | null = null;
  private websocket: WebSocket | null = null;
  private onCanvasUpdate?: (canvasState: CanvasState) => void;
  private onChatMessage?: (message: ChatMessage) => void;
  private onUserJoined?: (message: string) => void;

  // Canvas Management
  async createCanvas(): Promise<CanvasState> {
    const response = await fetch(`${API_BASE_URL}/canvas`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const canvasState = await response.json() as CanvasState;
    this.canvasId = canvasState.id;
    return canvasState;
  }

  async getCanvas(canvasId: string): Promise<CanvasState> {
    const response = await fetch(`${API_BASE_URL}/canvas/${canvasId}`);

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const canvasState = await response.json() as CanvasState;
    this.canvasId = canvasId;
    return canvasState;
  }

  async updateCanvas(canvasState: CanvasState): Promise<CanvasState> {
    if (!this.canvasId) {
      throw new Error('No canvas loaded');
    }

    const response = await fetch(`${API_BASE_URL}/canvas/${this.canvasId}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(canvasState),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  }

  // Image Management
  async addImage(imageData: Omit<ImageNode, 'id'>): Promise<ImageNode> {
    if (!this.canvasId) {
      throw new Error('No canvas loaded');
    }

    const response = await fetch(`${API_BASE_URL}/canvas/${this.canvasId}/images`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(imageData),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  }

  async deleteImage(imageId: string): Promise<void> {
    if (!this.canvasId) {
      throw new Error('No canvas loaded');
    }

    const response = await fetch(`${API_BASE_URL}/canvas/${this.canvasId}/images/${imageId}`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
  }

  // Group Management
  async createGroup(imageIds: string[]): Promise<ImageGroup> {
    if (!this.canvasId) {
      throw new Error('No canvas loaded');
    }

    const response = await fetch(`${API_BASE_URL}/canvas/${this.canvasId}/groups`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(imageIds),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  }

  async deleteGroup(groupId: string): Promise<string[]> {
    if (!this.canvasId) {
      throw new Error('No canvas loaded');
    }

    const response = await fetch(`${API_BASE_URL}/canvas/${this.canvasId}/groups/${groupId}`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const result = await response.json();
    return result.imageIds;
  }

  // Chat System
  async getMessages(limit: number = 50): Promise<ChatMessage[]> {
    if (!this.canvasId) {
      throw new Error('No canvas loaded');
    }

    const response = await fetch(`${API_BASE_URL}/canvas/${this.canvasId}/messages?limit=${limit}`);

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  }

  async sendMessage(text: string, sender: string = 'User'): Promise<ChatMessage> {
    if (!this.canvasId) {
      throw new Error('No canvas loaded');
    }

    const response = await fetch(`${API_BASE_URL}/canvas/${this.canvasId}/messages`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ text, sender }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  }

  // File Upload
  async uploadImage(file: File): Promise<string> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE_URL}/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const result = await response.json();
    return result.dataUrl;
  }

  // WebSocket Real-time Collaboration
  connectWebSocket(callbacks: {
    onCanvasUpdate?: (canvasState: CanvasState) => void;
    onChatMessage?: (message: ChatMessage) => void;
    onUserJoined?: (message: string) => void;
    onUserLeft?: (message: string) => void;
    onImageAdded?: (image: ImageNode) => void;
    onImageDeleted?: (imageId: string) => void;
    onImagesGrouped?: (group: ImageGroup) => void;
    onImagesUngrouped?: (data: { groupId: string; imageIds: string[] }) => void;
  }): void {
    if (!this.canvasId) {
      throw new Error('No canvas loaded');
    }

    this.onCanvasUpdate = callbacks.onCanvasUpdate;
    this.onChatMessage = callbacks.onChatMessage;
    this.onUserJoined = callbacks.onUserJoined;

    this.websocket = new WebSocket(`${WS_BASE_URL}/${this.canvasId}`);

    this.websocket.onopen = () => {
      console.log('WebSocket connected');
    };

    this.websocket.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        
        switch (message.type) {
          case 'canvas_state':
          case 'canvas_update':
            callbacks.onCanvasUpdate?.(message.data);
            break;
          
          case 'chat_message':
            callbacks.onChatMessage?.(message.data);
            break;
          
          case 'user_joined':
            callbacks.onUserJoined?.(message.data.message);
            break;
          
          case 'user_left':
            callbacks.onUserLeft?.(message.data.message);
            break;
          
          case 'image_added':
            callbacks.onImageAdded?.(message.data);
            break;
          
          case 'image_deleted':
            callbacks.onImageDeleted?.(message.data.imageId);
            break;
          
          case 'images_grouped':
            callbacks.onImagesGrouped?.(message.data);
            break;
          
          case 'images_ungrouped':
            callbacks.onImagesUngrouped?.(message.data);
            break;
        }
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    this.websocket.onclose = () => {
      console.log('WebSocket disconnected');
    };

    this.websocket.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  }

  disconnectWebSocket(): void {
    if (this.websocket) {
      this.websocket.close();
      this.websocket = null;
    }
  }

  // Send real-time updates through WebSocket
  sendWebSocketMessage(type: string, data: any): void {
    if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
      this.websocket.send(JSON.stringify({
        type,
        data,
        canvasId: this.canvasId
      }));
    }
  }

  // Utility methods
  getCurrentCanvasId(): string | null {
    return this.canvasId;
  }

  setCanvasId(canvasId: string): void {
    this.canvasId = canvasId;
  }

  // Health check
  async healthCheck(): Promise<{ status: string; canvases: number }> {
    const response = await fetch(`${API_BASE_URL.replace('/api', '')}/health`);
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  }
}

// Export singleton instance
export const canvasAPI = new CanvasAPI();
