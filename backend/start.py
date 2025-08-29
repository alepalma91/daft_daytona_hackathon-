#!/usr/bin/env python3
"""
Startup script for Image Canvas Workspace API with Style Analysis
"""

import uvicorn
import os
import sys

def main():
    """Start the FastAPI server"""
    try:
        print("🚀 Starting Image Canvas Workspace API with Style Analysis...")
        print("📍 Server will be available at: http://localhost:8001")
        print("📖 API docs available at: http://localhost:8001/docs")
        print("🔌 WebSocket endpoint: ws://localhost:8001/ws/{canvas_id}")
        print("🎨 Style analysis with Daft + LLM integration")
        
        # Check if HF_TOKEN is available
        if os.getenv("HF_TOKEN"):
            print("✅ HF_TOKEN found in environment")
        else:
            print("⚠️ HF_TOKEN not found - some models may not be accessible")
        
        print("\n⚡ Starting server...")
        
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8001,  # Use different port to avoid conflicts
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
