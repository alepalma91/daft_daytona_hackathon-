import { 
  ImageNode, 
  Viewport, 
  Point, 
  Rectangle, 
  DragState, 
  SelectionState 
} from './types.js';

export class ImageCanvas {
  private canvas: HTMLCanvasElement;
  private ctx: CanvasRenderingContext2D;
  private images: ImageNode[] = [];
  private viewport: Viewport = { scale: 1, tx: 0, ty: 0 };
  private dragState: DragState = { isDragging: false, startPoint: { x: 0, y: 0 } };
  private selectionState: SelectionState = { 
    isSelecting: false, 
    startPoint: { x: 0, y: 0 }, 
    currentPoint: { x: 0, y: 0 } 
  };
  private isPanning = false;
  private keys = new Set<string>();
  private needsRedraw = true;

  constructor(canvas: HTMLCanvasElement) {
    this.canvas = canvas;
    const ctx = canvas.getContext('2d');
    if (!ctx) throw new Error('Could not get 2D context');
    this.ctx = ctx;

    this.setupCanvas();
    this.setupEventListeners();
    this.setupKeyboardListeners();
    this.startRenderLoop();
  }

  private setupCanvas(): void {
    // Set up HiDPI support
    const dpr = window.devicePixelRatio || 1;
    const rect = this.canvas.getBoundingClientRect();
    
    this.canvas.width = rect.width * dpr;
    this.canvas.height = rect.height * dpr;
    this.canvas.style.width = rect.width + 'px';
    this.canvas.style.height = rect.height + 'px';
    
    this.ctx.scale(dpr, dpr);
    
    // Prevent touch gestures
    this.canvas.style.touchAction = 'none';
    
    // Make canvas focusable for keyboard events
    this.canvas.tabIndex = 0;
  }

  private setupEventListeners(): void {
    this.canvas.addEventListener('pointerdown', this.handlePointerDown.bind(this));
    this.canvas.addEventListener('pointermove', this.handlePointerMove.bind(this));
    this.canvas.addEventListener('pointerup', this.handlePointerUp.bind(this));
    this.canvas.addEventListener('wheel', this.handleWheel.bind(this));
    
    window.addEventListener('resize', this.handleResize.bind(this));
  }

  private setupKeyboardListeners(): void {
    document.addEventListener('keydown', (e) => {
      this.keys.add(e.code);
      
      // Handle delete key for selected images
      if ((e.key === 'Delete' || e.key === 'Backspace') && 
          document.activeElement === this.canvas) {
        e.preventDefault();
        this.deleteSelectedImages();
      }
    });
    
    document.addEventListener('keyup', (e) => {
      this.keys.delete(e.code);
    });
  }

  private handlePointerDown(e: PointerEvent): void {
    e.preventDefault();
    this.canvas.focus();
    this.canvas.setPointerCapture(e.pointerId);

    const screenPoint = { x: e.offsetX, y: e.offsetY };
    const worldPoint = this.screenToWorld(screenPoint);

    // Check if space is held for panning
    if (this.keys.has('Space')) {
      this.isPanning = true;
      this.dragState = {
        isDragging: true,
        startPoint: screenPoint,
        startViewport: { ...this.viewport }
      };
      return;
    }

    // Check for image hit
    const hitImage = this.getImageAt(worldPoint);
    
    if (hitImage) {
      // Handle image selection and dragging
      if (!e.shiftKey && !hitImage.selected) {
        this.clearSelection();
        hitImage.selected = true;
      } else if (e.shiftKey) {
        hitImage.selected = !hitImage.selected;
      }

      // Start dragging selected images
      const selectedImages = this.images.filter(img => img.selected);
      if (selectedImages.length > 0) {
        const initialPositions = new Map<string, Point>();
        selectedImages.forEach(img => {
          initialPositions.set(img.id, { x: img.x, y: img.y });
        });

        this.dragState = {
          isDragging: true,
          startPoint: worldPoint,
          draggedImages: selectedImages,
          initialPositions
        };
      }
    } else {
      // Start marquee selection
      if (!e.shiftKey) {
        this.clearSelection();
      }
      
      this.selectionState = {
        isSelecting: true,
        startPoint: worldPoint,
        currentPoint: worldPoint
      };
    }

    this.needsRedraw = true;
  }

  private handlePointerMove(e: PointerEvent): void {
    const screenPoint = { x: e.offsetX, y: e.offsetY };
    const worldPoint = this.screenToWorld(screenPoint);

    if (this.isPanning && this.dragState.isDragging && this.dragState.startViewport) {
      // Pan the viewport
      const dx = screenPoint.x - this.dragState.startPoint.x;
      const dy = screenPoint.y - this.dragState.startPoint.y;
      
      this.viewport.tx = this.dragState.startViewport.tx + dx;
      this.viewport.ty = this.dragState.startViewport.ty + dy;
      
      this.needsRedraw = true;
    } else if (this.dragState.isDragging && this.dragState.draggedImages && this.dragState.initialPositions) {
      // Drag selected images
      const dx = worldPoint.x - this.dragState.startPoint.x;
      const dy = worldPoint.y - this.dragState.startPoint.y;

      this.dragState.draggedImages.forEach(img => {
        const initialPos = this.dragState.initialPositions!.get(img.id)!;
        img.x = initialPos.x + dx;
        img.y = initialPos.y + dy;
      });

      this.needsRedraw = true;
    } else if (this.selectionState.isSelecting) {
      // Update marquee selection
      this.selectionState.currentPoint = worldPoint;
      this.updateMarqueeSelection();
      this.needsRedraw = true;
    }
  }

  private handlePointerUp(e: PointerEvent): void {
    this.canvas.releasePointerCapture(e.pointerId);

    if (this.selectionState.isSelecting) {
      this.selectionState.isSelecting = false;
      this.needsRedraw = true;
    }

    this.dragState = { isDragging: false, startPoint: { x: 0, y: 0 } };
    this.isPanning = false;
    this.needsRedraw = true;
  }

  private handleWheel(e: WheelEvent): void {
    // Only zoom if Ctrl/Cmd is held
    if (e.ctrlKey || e.metaKey) {
      e.preventDefault();
      
      const screenPoint = { x: e.offsetX, y: e.offsetY };
      const worldPoint = this.screenToWorld(screenPoint);
      
      // Zoom factor
      const zoomFactor = e.deltaY > 0 ? 0.9 : 1.1;
      const newScale = Math.max(0.1, Math.min(5, this.viewport.scale * zoomFactor));
      
      // Adjust translation to keep the cursor position stable
      const scaleDiff = newScale - this.viewport.scale;
      this.viewport.tx -= (worldPoint.x * scaleDiff);
      this.viewport.ty -= (worldPoint.y * scaleDiff);
      
      this.viewport.scale = newScale;
      this.needsRedraw = true;
    }
  }

  private handleResize(): void {
    this.setupCanvas();
    this.needsRedraw = true;
  }

  private updateMarqueeSelection(): void {
    const rect = this.getMarqueeRect();
    
    this.images.forEach(img => {
      const imgRect = { x: img.x, y: img.y, w: img.w, h: img.h };
      if (this.rectanglesIntersect(rect, imgRect)) {
        img.selected = true;
      }
    });
  }

  private getMarqueeRect(): Rectangle {
    const start = this.selectionState.startPoint;
    const current = this.selectionState.currentPoint;
    
    return {
      x: Math.min(start.x, current.x),
      y: Math.min(start.y, current.y),
      w: Math.abs(current.x - start.x),
      h: Math.abs(current.y - start.y)
    };
  }

  private rectanglesIntersect(a: Rectangle, b: Rectangle): boolean {
    return !(a.x + a.w < b.x || b.x + b.w < a.x || 
             a.y + a.h < b.y || b.y + b.h < a.y);
  }

  private getImageAt(worldPoint: Point): ImageNode | null {
    // Search from top to bottom (last in array = on top)
    for (let i = this.images.length - 1; i >= 0; i--) {
      const img = this.images[i];
      if (worldPoint.x >= img.x && worldPoint.x <= img.x + img.w &&
          worldPoint.y >= img.y && worldPoint.y <= img.y + img.h) {
        return img;
      }
    }
    return null;
  }

  private screenToWorld(screenPoint: Point): Point {
    return {
      x: (screenPoint.x - this.viewport.tx) / this.viewport.scale,
      y: (screenPoint.y - this.viewport.ty) / this.viewport.scale
    };
  }

  private worldToScreen(worldPoint: Point): Point {
    return {
      x: worldPoint.x * this.viewport.scale + this.viewport.tx,
      y: worldPoint.y * this.viewport.scale + this.viewport.ty
    };
  }

  private clearSelection(): void {
    this.images.forEach(img => img.selected = false);
  }

  private deleteSelectedImages(): void {
    const before = this.images.length;
    this.images = this.images.filter(img => !img.selected);
    if (this.images.length < before) {
      this.needsRedraw = true;
    }
  }

  private startRenderLoop(): void {
    const render = () => {
      if (this.needsRedraw) {
        this.draw();
        this.needsRedraw = false;
      }
      requestAnimationFrame(render);
    };
    render();
  }

  private draw(): void {
    const rect = this.canvas.getBoundingClientRect();
    this.ctx.clearRect(0, 0, rect.width, rect.height);

    // Apply viewport transform
    this.ctx.save();
    this.ctx.translate(this.viewport.tx, this.viewport.ty);
    this.ctx.scale(this.viewport.scale, this.viewport.scale);

    // Draw images
    this.images.forEach(img => {
      this.ctx.drawImage(img.img, img.x, img.y, img.w, img.h);
      
      // Draw selection highlight
      if (img.selected) {
        this.ctx.save();
        this.ctx.strokeStyle = '#4A90E2';
        this.ctx.lineWidth = 2 / this.viewport.scale;
        this.ctx.setLineDash([5 / this.viewport.scale, 5 / this.viewport.scale]);
        this.ctx.strokeRect(img.x, img.y, img.w, img.h);
        this.ctx.restore();
      }
    });

    // Draw marquee selection
    if (this.selectionState.isSelecting) {
      const rect = this.getMarqueeRect();
      this.ctx.save();
      this.ctx.strokeStyle = '#4A90E2';
      this.ctx.lineWidth = 1 / this.viewport.scale;
      this.ctx.setLineDash([5 / this.viewport.scale, 5 / this.viewport.scale]);
      this.ctx.strokeRect(rect.x, rect.y, rect.w, rect.h);
      this.ctx.restore();
    }

    this.ctx.restore();
  }

  // Public methods
  public addImage(src: string): Promise<ImageNode> {
    return new Promise((resolve, reject) => {
      const img = new Image();
      img.crossOrigin = 'anonymous';
      
      img.onload = () => {
        // Calculate size with max width of 320px
        const maxWidth = 320;
        let width = img.width;
        let height = img.height;
        
        if (width > maxWidth) {
          height = (height * maxWidth) / width;
          width = maxWidth;
        }

        // Place at center of current view
        const centerWorld = this.screenToWorld({ 
          x: this.canvas.width / (2 * (window.devicePixelRatio || 1)), 
          y: this.canvas.height / (2 * (window.devicePixelRatio || 1))
        });

        const imageNode: ImageNode = {
          id: crypto.randomUUID(),
          img,
          x: centerWorld.x - width / 2,
          y: centerWorld.y - height / 2,
          w: width,
          h: height,
          selected: false
        };

        this.images.push(imageNode);
        this.needsRedraw = true;
        resolve(imageNode);
      };

      img.onerror = () => reject(new Error('Failed to load image'));
      img.src = src;
    });
  }

  public clearImages(): void {
    this.images = [];
    this.needsRedraw = true;
  }

  public getSelectedCount(): number {
    return this.images.filter(img => img.selected).length;
  }
}
