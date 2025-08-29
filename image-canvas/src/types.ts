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
  img: HTMLImageElement;
  x: number;
  y: number;
  w: number;
  h: number;
  selected: boolean;
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
  timestamp: number;
}

// Event types
export interface CanvasEvents {
  imageAdded: ImageNode;
  imageDeleted: string;
  selectionChanged: string[];
  messageSent: ChatMessage;
}
