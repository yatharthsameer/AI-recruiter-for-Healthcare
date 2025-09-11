#!/usr/bin/env python3
"""
Start the Interview Data API server
"""
import subprocess
import sys
import os

def install_requirements():
    """Install required packages"""
    try:
        import fastapi
        import uvicorn
        print("✅ FastAPI and Uvicorn already installed")
    except ImportError:
        print("📦 Installing FastAPI and Uvicorn...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "fastapi", "uvicorn[standard]"])
        print("✅ Installation complete")

def start_server():
    """Start the API server"""
    print("🚀 Starting Interview Data API server...")
    print("📍 Server will be available at: http://localhost:8000")
    print("📊 API documentation at: http://localhost:8000/docs")
    print("🔄 Press Ctrl+C to stop the server\n")
    
    try:
        # Change to the directory containing the API server
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        
        # Start the server
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "api_server:app", 
            "--host", "0.0.0.0", 
            "--port", "8000", 
            "--reload"
        ])
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
    except Exception as e:
        print(f"❌ Error starting server: {e}")

if __name__ == "__main__":
    install_requirements()
    start_server()
