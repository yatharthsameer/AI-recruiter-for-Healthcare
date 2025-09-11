#!/bin/bash

# AI Interviewer Python Backend Setup Script

echo "🎯 AI Interviewer Python Backend Setup"
echo "======================================"

# Check if Python 3.8+ is available
python_version=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
if [[ $(echo "$python_version >= 3.8" | bc -l) -eq 0 ]]; then
    echo "❌ Python 3.8+ required. Found: $python_version"
    exit 1
fi
echo "✅ Python $python_version detected"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Copy environment file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "⚙️ Creating .env file..."
    cp env.example .env
    echo "✅ Created .env file from example"
    echo "⚠️  Please edit .env and add your API keys"
else
    echo "✅ .env file already exists"
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "To start the server:"
echo "  source venv/bin/activate"
echo "  python asgi_app.py"
echo ""
echo "Or use the start script:"
echo "  python start.py"
echo ""
echo "To test WebSocket connection:"
echo "  python test_websocket.py"
echo ""
echo "Server will run on: http://localhost:3000"
echo "WebSocket endpoint: ws://localhost:3000/ws/audio"
echo "Health check: http://localhost:3000/health"
