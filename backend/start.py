#!/usr/bin/env python3
"""
Startup script for Image Canvas Workspace API
"""

import uvicorn
import os
import sys

def main():
    """Start the FastAPI server"""
    try:
        print("🚀 Starting Image Canvas Workspace API...")
        print("📍 Server will be available at: http://localhost:8000")
        print("📖 API docs available at: http://localhost:8000/docs")
        print("🔌 WebSocket endpoint: ws://localhost:8000/ws/{canvas_id}")
        print("\n⚡ Starting server...")
        
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,  # Auto-reload on file changes
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 Shutting down server...")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
