#!/usr/bin/env python3
"""
Development startup script for AI Interviewer Python Backend
"""
import os
import sys
import subprocess
from pathlib import Path

def check_python_version():
    """Ensure we're running Python 3.8+"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        sys.exit(1)
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}")

def install_dependencies():
    """Install required packages"""
    print("📦 Installing dependencies...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True, capture_output=True)
        print("✅ Dependencies installed")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        sys.exit(1)

def setup_environment():
    """Setup environment variables"""
    env_file = Path(".env")
    if not env_file.exists():
        print("⚠️  .env file not found, copying from env.example")
        example_file = Path("env.example")
        if example_file.exists():
            env_file.write_text(example_file.read_text())
            print("✅ Created .env file from example")
        else:
            print("❌ env.example not found")
            sys.exit(1)

def start_server():
    """Start the development server"""
    print("🚀 Starting AI Interviewer Backend...")
    print("📊 Server will run on http://localhost:3000")
    print("🎤 WebSocket endpoint: ws://localhost:3000/ws/audio")
    print("🔗 Health check: http://localhost:3000/health")
    print("\nPress Ctrl+C to stop the server\n")
    
    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "asgi_app:app", 
            "--host", "0.0.0.0", 
            "--port", "3000", 
            "--reload"
        ])
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")

def main():
    """Main startup sequence"""
    print("🎯 AI Interviewer Python Backend Setup")
    print("=" * 40)
    
    check_python_version()
    install_dependencies()
    setup_environment()
    start_server()

if __name__ == "__main__":
    main()
