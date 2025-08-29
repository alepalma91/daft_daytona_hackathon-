#!/usr/bin/env python3
"""
Test script to verify Daytona connection and basic functionality
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

# Load environment variables
load_dotenv()


def test_daytona_connection():
    """Test basic Daytona connection and sandbox creation"""
    try:
        from daytona import Daytona, DaytonaConfig
        
        # Check for API key
        api_key = os.getenv("DAYTONA_API_KEY")
        if not api_key or api_key == "your-api-key-here":
            print("❌ Error: DAYTONA_API_KEY not set properly in .env file")
            print("   Please edit .env and add your actual Daytona API key")
            return False
        
        print("🔧 Initializing Daytona client...")
        
        # Initialize Daytona
        config = DaytonaConfig(api_key=api_key)
        daytona = Daytona(config)
        
        print("✓ Daytona client initialized")
        
        # Test sandbox creation
        print("\n📦 Creating test sandbox...")
        sandbox = daytona.create()
        print("✓ Sandbox created successfully")
        
        # Test code execution
        print("\n🏃 Testing code execution...")
        test_code = """
import sys
print(f"Python version: {sys.version}")
print("Hello from Daytona sandbox!")
print("✨ Everything is working!")
"""
        
        response = sandbox.process.code_run(test_code)
        
        if response.exit_code == 0:
            print("✓ Code execution successful")
            print("\n📋 Output:")
            print("-" * 40)
            print(response.result)
            print("-" * 40)
        else:
            print(f"❌ Code execution failed with exit code: {response.exit_code}")
            print(f"Error: {response.result}")
            return False
        
        # Clean up
        print("\n🧹 Cleaning up...")
        # Note: Add sandbox cleanup if available in Daytona API
        
        print("\n✅ All tests passed! Daytona is ready to use.")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Please run: pip install -r requirements.txt")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    print("🧪 Testing Daytona Connection\n")
    
    # Check if .env exists
    if not Path(".env").exists():
        print("❌ .env file not found")
        print("   Please run: python setup.py")
        sys.exit(1)
    
    # Run test
    success = test_daytona_connection()
    
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
