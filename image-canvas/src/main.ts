import { ImageCanvas } from './canvas';
import type { ChatMessage } from './types';

class ImageCanvasApp {
  private canvas!: ImageCanvas;
  private chatMessages: ChatMessage[] = [];

  constructor() {
    console.log('Creating ImageCanvasApp...');
    this.setupDOM();
    
    // Wait for DOM to be ready before initializing canvas
    setTimeout(() => {
      this.initializeCanvas();
    }, 100);
  }

  private initializeCanvas(): void {
    const canvasElement = document.getElementById('canvas') as HTMLCanvasElement;
    if (!canvasElement) {
      console.error('Canvas element not found');
      return;
    }

    console.log('Initializing canvas...');
    this.canvas = new ImageCanvas(canvasElement);
    
    // Set up selection change callback to update group button states
    this.canvas.setSelectionChangeCallback(() => {
      this.updateGroupButtonStates();
    });
    
    this.setupEventListeners();
    this.addChatMessage('System', 'Image Canvas Workspace ready! Add images using the toolbar above.');
    console.log('Canvas initialized successfully');

    // Add a test image to verify everything is working
    this.addTestImage();
  }

  private setupDOM(): void {
    console.log('Setting up DOM...');
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
            <button id="group-btn" disabled>Group Selected</button>
            <button id="ungroup-btn" disabled>Ungroup</button>
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

    // Set up canvas sizing
    setTimeout(() => {
      this.resizeCanvas();
      window.addEventListener('resize', this.resizeCanvas.bind(this));
    }, 50);
  }

  private resizeCanvas(): void {
    const canvas = document.getElementById('canvas') as HTMLCanvasElement;
    const container = document.getElementById('canvas-container') as HTMLElement;
    
    if (!canvas || !container) return;
    
    const rect = container.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    
    // Set display size (CSS pixels)
    canvas.style.width = rect.width + 'px';
    canvas.style.height = rect.height + 'px';
    
    // Set actual size in memory (scaled up for HiDPI)
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    
    // Scale the drawing context to match the device pixel ratio
    const ctx = canvas.getContext('2d');
    if (ctx) {
      ctx.scale(dpr, dpr);
    }
  }

  private setupEventListeners(): void {
    if (!this.canvas) {
      console.error('Canvas not initialized');
      return;
    }

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
        this.updateGroupButtonStates();
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
          this.updateGroupButtonStates();
        } catch (error) {
          this.addChatMessage('System', `Failed to load ${file.name}: ${error instanceof Error ? error.message : 'Unknown error'}`);
        }
      });
      
      // Clear file input
      target.value = '';
    });

    // Group buttons
    const groupBtn = document.getElementById('group-btn') as HTMLButtonElement;
    const ungroupBtn = document.getElementById('ungroup-btn') as HTMLButtonElement;

    groupBtn.addEventListener('click', () => {
      const groupId = this.canvas.groupSelectedImages();
      if (groupId) {
        const selectedCount = this.canvas.getSelectedCount();
        this.addChatMessage('System', `Grouped ${selectedCount} images together`);
        this.updateGroupButtonStates();
      }
    });

    ungroupBtn.addEventListener('click', () => {
      const ungroupedIds = this.canvas.ungroupSelectedImages();
      if (ungroupedIds.length > 0) {
        this.addChatMessage('System', `Ungrouped ${ungroupedIds.length} images`);
        this.updateGroupButtonStates();
      }
    });

    // Clear button
    const clearBtn = document.getElementById('clear-btn') as HTMLButtonElement;
    clearBtn.addEventListener('click', () => {
      this.canvas.clearImages();
      this.addChatMessage('System', 'All images cleared');
      this.updateGroupButtonStates();
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

  private async addTestImage(): Promise<void> {
    // Add a simple test image to verify the canvas is working
    try {
      await this.canvas.addImage('https://picsum.photos/300/200?random=1');
      this.addChatMessage('System', 'Added test image from Picsum Photos');
      this.updateGroupButtonStates();
    } catch (error) {
      console.log('Test image failed to load, creating canvas test pattern instead');
      // If external image fails, we'll just rely on the grid background
    }
  }

  private updateGroupButtonStates(): void {
    const groupBtn = document.getElementById('group-btn') as HTMLButtonElement;
    const ungroupBtn = document.getElementById('ungroup-btn') as HTMLButtonElement;

    if (groupBtn && ungroupBtn) {
      groupBtn.disabled = !this.canvas.canGroup();
      ungroupBtn.disabled = !this.canvas.canUngroup();
      
      // Update button text to show how many images are selected
      const selectedCount = this.canvas.getSelectedCount();
      if (selectedCount === 0) {
        groupBtn.textContent = 'Group Selected';
        ungroupBtn.textContent = 'Ungroup';
      } else {
        groupBtn.textContent = `Group ${selectedCount} Selected`;
        ungroupBtn.textContent = this.canvas.canUngroup() ? 'Ungroup Selected' : 'Ungroup';
      }
    }
  }
}

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
  console.log('DOM loaded, initializing app...');
  
  // Remove loading screen
  const loading = document.getElementById('loading');
  if (loading) {
    loading.style.display = 'none';
  }
  
  // Initialize the app
  try {
    new ImageCanvasApp();
    console.log('App initialized successfully');
  } catch (error) {
    console.error('Failed to initialize app:', error);
    document.body.innerHTML = `
      <div style="
        padding: 2rem;
        background: #1a1a1a;
        color: white;
        font-family: Arial, sans-serif;
        min-height: 100vh;
      ">
        <h1>Error Loading Application</h1>
        <p>There was an error initializing the Image Canvas Workspace:</p>
        <pre style="background: #333; padding: 1rem; border-radius: 4px; overflow: auto;">
${error instanceof Error ? error.stack : error}
        </pre>
        <p>Please check the browser console for more details.</p>
      </div>
    `;
  }
});