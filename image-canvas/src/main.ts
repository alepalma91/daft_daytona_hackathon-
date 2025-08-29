import { ImageCanvas } from './canvas.js';
import { ChatMessage } from './types.js';

class ImageCanvasApp {
  private canvas: ImageCanvas;
  private chatMessages: ChatMessage[] = [];

  constructor() {
    this.setupDOM();
    this.canvas = new ImageCanvas(document.getElementById('canvas') as HTMLCanvasElement);
    this.setupEventListeners();
  }

  private setupDOM(): void {
    document.body.innerHTML = `
      <div id="app">
        <div id="toolbar">
          <div class="toolbar-group">
            <input type="text" id="url-input" placeholder="Paste image URL..." />
            <button id="add-url-btn">Add URL</button>
          </div>
          <div class="toolbar-group">
            <input type="file" id="file-input" multiple accept="image/*" />
            <label for="file-input" class="file-input-label">Add Files</label>
          </div>
          <div class="toolbar-group">
            <button id="clear-btn">Clear All</button>
          </div>
        </div>
        
        <div id="canvas-container">
          <canvas id="canvas"></canvas>
        </div>
        
        <div id="chat-bar">
          <div id="chat-log" aria-live="polite" aria-label="Chat messages"></div>
          <div id="chat-input-container">
            <input type="text" id="chat-input" placeholder="Type a message..." />
            <button id="send-btn">Send</button>
          </div>
        </div>
      </div>
    `;

    // Resize canvas to fill container
    this.resizeCanvas();
    window.addEventListener('resize', this.resizeCanvas.bind(this));
  }

  private resizeCanvas(): void {
    const canvas = document.getElementById('canvas') as HTMLCanvasElement;
    const container = document.getElementById('canvas-container') as HTMLElement;
    
    canvas.width = container.clientWidth;
    canvas.height = container.clientHeight;
    canvas.style.width = container.clientWidth + 'px';
    canvas.style.height = container.clientHeight + 'px';
  }

  private setupEventListeners(): void {
    // URL input handling
    const urlInput = document.getElementById('url-input') as HTMLInputElement;
    const addUrlBtn = document.getElementById('add-url-btn') as HTMLButtonElement;
    
    const addFromUrl = async () => {
      const url = urlInput.value.trim();
      if (!url) return;
      
      try {
        addUrlBtn.disabled = true;
        addUrlBtn.textContent = 'Loading...';
        
        await this.canvas.addImage(url);
        urlInput.value = '';
        
        this.addChatMessage('System', `Image added from URL: ${url}`);
      } catch (error) {
        this.addChatMessage('System', `Failed to load image: ${error instanceof Error ? error.message : 'Unknown error'}`);
      } finally {
        addUrlBtn.disabled = false;
        addUrlBtn.textContent = 'Add URL';
      }
    };

    addUrlBtn.addEventListener('click', addFromUrl);
    urlInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        addFromUrl();
      }
    });

    // File input handling
    const fileInput = document.getElementById('file-input') as HTMLInputElement;
    fileInput.addEventListener('change', (e) => {
      const target = e.target as HTMLInputElement;
      if (!target.files) return;

      Array.from(target.files).forEach(async (file) => {
        try {
          const url = URL.createObjectURL(file);
          await this.canvas.addImage(url);
          this.addChatMessage('System', `Image added: ${file.name}`);
        } catch (error) {
          this.addChatMessage('System', `Failed to load ${file.name}: ${error instanceof Error ? error.message : 'Unknown error'}`);
        }
      });
      
      // Clear file input
      target.value = '';
    });

    // Clear button
    const clearBtn = document.getElementById('clear-btn') as HTMLButtonElement;
    clearBtn.addEventListener('click', () => {
      this.canvas.clearImages();
      this.addChatMessage('System', 'All images cleared');
    });

    // Chat functionality
    const chatInput = document.getElementById('chat-input') as HTMLInputElement;
    const sendBtn = document.getElementById('send-btn') as HTMLButtonElement;

    const sendMessage = () => {
      const text = chatInput.value.trim();
      if (!text) return;

      this.addChatMessage('You', text);
      chatInput.value = '';
      
      // Focus back to chat input
      chatInput.focus();
    };

    sendBtn.addEventListener('click', sendMessage);
    chatInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        sendMessage();
      }
    });

    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
      // Prevent space from scrolling page when canvas has focus
      if (e.code === 'Space' && document.activeElement?.id === 'canvas') {
        e.preventDefault();
      }
      
      // Paste URL support (Ctrl+V)
      if ((e.ctrlKey || e.metaKey) && e.key === 'v' && 
          document.activeElement?.id === 'canvas') {
        navigator.clipboard.readText().then(text => {
          if (text && this.isValidUrl(text)) {
            urlInput.value = text;
            addFromUrl();
          }
        }).catch(() => {
          // Ignore clipboard errors
        });
      }
    });

    // Drag and drop support
    const canvasContainer = document.getElementById('canvas-container') as HTMLElement;
    
    canvasContainer.addEventListener('dragover', (e) => {
      e.preventDefault();
      e.dataTransfer!.dropEffect = 'copy';
    });

    canvasContainer.addEventListener('drop', (e) => {
      e.preventDefault();
      
      const files = Array.from(e.dataTransfer?.files || []);
      const urls = e.dataTransfer?.getData('text/plain');
      
      // Handle dropped files
      files.forEach(async (file) => {
        if (file.type.startsWith('image/')) {
          try {
            const url = URL.createObjectURL(file);
            await this.canvas.addImage(url);
            this.addChatMessage('System', `Image dropped: ${file.name}`);
          } catch (error) {
            this.addChatMessage('System', `Failed to load dropped image: ${error instanceof Error ? error.message : 'Unknown error'}`);
          }
        }
      });

      // Handle dropped URLs
      if (urls && this.isValidUrl(urls)) {
        this.canvas.addImage(urls).then(() => {
          this.addChatMessage('System', `Image added from dropped URL: ${urls}`);
        }).catch((error) => {
          this.addChatMessage('System', `Failed to load dropped image: ${error instanceof Error ? error.message : 'Unknown error'}`);
        });
      }
    });
  }

  private addChatMessage(sender: string, text: string): void {
    const message: ChatMessage = {
      id: crypto.randomUUID(),
      text,
      timestamp: Date.now()
    };

    this.chatMessages.push(message);
    this.updateChatDisplay();
  }

  private updateChatDisplay(): void {
    const chatLog = document.getElementById('chat-log') as HTMLElement;
    
    // Keep only last 100 messages for performance
    if (this.chatMessages.length > 100) {
      this.chatMessages = this.chatMessages.slice(-100);
    }

    chatLog.innerHTML = this.chatMessages
      .slice(-10) // Show only last 10 messages
      .map(msg => {
        const time = new Date(msg.timestamp).toLocaleTimeString();
        return `<div class="chat-message">
          <span class="chat-time">[${time}]</span>
          <span class="chat-text">${this.escapeHtml(msg.text)}</span>
        </div>`;
      })
      .join('');
    
    // Scroll to bottom
    chatLog.scrollTop = chatLog.scrollHeight;
  }

  private escapeHtml(text: string): string {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  private isValidUrl(string: string): boolean {
    try {
      const url = new URL(string);
      return url.protocol === 'http:' || url.protocol === 'https:';
    } catch {
      return false;
    }
  }
}

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
  new ImageCanvasApp();
});