#!/usr/bin/env python3
"""
Setup script for Image Canvas Workspace API with Style Analysis
"""

import os
import sys
import shutil

def main():
    """Set up the backend environment"""
    print("🔧 Setting up Image Canvas Workspace Backend...")
    
    # Check if we're in the backend directory
    if not os.path.exists('main.py'):
        print("❌ Error: Please run this script from the backend/ directory")
        sys.exit(1)
    
    # Create .env file from template if it doesn't exist
    if not os.path.exists('.env'):
        if os.path.exists('env.config'):
            try:
                shutil.copy('env.config', '.env')
                print("✅ Created .env file from env.config template")
            except Exception as e:
                print(f"⚠️ Could not create .env file: {e}")
                print("💡 You can manually copy env.config to .env")
        else:
            print("⚠️ env.config template not found")
    else:
        print("✅ .env file already exists")
    
    # Check Python dependencies
    try:
        import daft
        print("✅ Daft is installed")
    except ImportError:
        print("❌ Daft not installed - run: pip install -r requirements.txt")
        
    try:
        import transformers
        print("✅ Transformers is installed")
    except ImportError:
        print("❌ Transformers not installed - run: pip install -r requirements.txt")
        
    try:
        import fastapi
        print("✅ FastAPI is installed")
    except ImportError:
        print("❌ FastAPI not installed - run: pip install -r requirements.txt")
    
    print("\n🚀 Setup complete!")
    print("📍 To start the server: python start.py")
    print("📖 Documentation: http://localhost:8001/docs")
    
if __name__ == "__main__":
    main()
