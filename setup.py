#!/usr/bin/env python3
"""
Setup script for Daft-Daytona Hackathon PoC
This script helps you set up your environment properly.
"""
import os
import sys
from pathlib import Path


def create_env_file():
    """Create .env file if it doesn't exist"""
    env_path = Path(".env")
    
    if env_path.exists():
        print("✓ .env file already exists")
        return
    
    print("Creating .env file...")
    
    # Read from .env.example
    example_path = Path(".env.example")
    if example_path.exists():
        with open(example_path, 'r') as f:
            content = f.read()
        
        with open(env_path, 'w') as f:
            f.write(content)
        
        print("✓ Created .env file from .env.example")
        print("\n⚠️  IMPORTANT: Edit .env and add your actual Daytona API key!")
    else:
        # Create basic .env
        with open(env_path, 'w') as f:
            f.write("# Daytona Configuration\n")
            f.write("DAYTONA_API_KEY=your-api-key-here\n")
        
        print("✓ Created basic .env file")
        print("\n⚠️  IMPORTANT: Edit .env and add your actual Daytona API key!")


def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 9):
        print("❌ Python 3.9 or higher is required")
        sys.exit(1)
    print(f"✓ Python {sys.version.split()[0]} is compatible")


def create_directories():
    """Create necessary project directories"""
    directories = [
        "data",
        "output",
        "logs",
        "models",
        "infrastructure/daytona",
        "infrastructure/daft",
        "api",
        "notebooks"
    ]
    
    for dir_path in directories:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    print("✓ Created project directories")


def main():
    print("🚀 Setting up Daft-Daytona Hackathon PoC\n")
    
    # Check Python version
    check_python_version()
    
    # Create directories
    create_directories()
    
    # Create .env file
    create_env_file()
    
    print("\n📋 Next steps:")
    print("1. Edit .env and add your Daytona API key")
    print("2. Run: pip install -r requirements.txt")
    print("3. Test Daytona connection: python infrastructure/sandbox/test_connection.py")
    print("\n✨ Setup complete!")


if __name__ == "__main__":
    main()
