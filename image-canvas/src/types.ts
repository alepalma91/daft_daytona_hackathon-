// Core types for the image canvas workspace

export interface Point {
  x: number;
  y: number;
}

export interface Rectangle {
  x: number;
  y: number;
  w: number;
  h: number;
}

export interface ImageNode {
  id: string;
  img?: HTMLImageElement; // Optional for API, required for canvas
  src?: string; // For API storage
  x: number;
  y: number;
  w: number;
  h: number;
  selected: boolean;
  groupId?: string;
}

export interface Viewport {
  scale: number;
  tx: number; // translation x
  ty: number; // translation y
}

export interface DragState {
  isDragging: boolean;
  startPoint: Point;
  startViewport?: Viewport;
  draggedImages?: ImageNode[];
  initialPositions?: Map<string, Point>;
}

export interface SelectionState {
  isSelecting: boolean;
  startPoint: Point;
  currentPoint: Point;
}

export interface ChatMessage {
  id: string;
  text: string;
  sender?: string;
  timestamp: string | Date;
  canvasId?: string;
}

export interface ImageGroup {
  id: string;
  imageIds: string[];
  name?: string;
}

export interface CanvasState {
  id: string;
  images: ImageNode[];
  groups: ImageGroup[];
  viewport: Viewport;
  lastModified: string | Date;
}

// Event types
export interface CanvasEvents {
  imageAdded: ImageNode;
  imageDeleted: string;
  selectionChanged: string[];
  messageSent: ChatMessage;
  imageGrouped: ImageGroup;
  imageUngrouped: string[];
}