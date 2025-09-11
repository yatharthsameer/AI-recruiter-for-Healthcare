# AI Interviewer Python Backend

Real-time AI interviewer backend with **Gemini multimodal integration** for advanced speech recognition and intelligent conversation management.

## 🚀 Features

- **🎤 Real-time Audio Processing**: WebSocket-based continuous transcription with enhanced pause tolerance
- **🧠 Gemini Multimodal Integration**: Advanced speech recognition using Google's Gemini API
- **🎯 Voice Activity Detection (VAD)**: Intelligent speech segmentation with thinking pause support
- **💬 Smart Interview Management**: AI-powered question generation and response analysis
- **🔄 Response Continuation**: Handles natural speech patterns with pauses and thinking time
- **📊 Comprehensive Evaluation**: Detailed candidate assessment and transcript generation
- **🌐 Single Port Deployment**: HTTP + WebSocket on same port for stability
- **🛡️ Production Ready**: ASGI-based with proper error handling and disconnect management

## 📋 Prerequisites

- **Python 3.8+** (Python 3.12 recommended)
- **Conda** (recommended) or pip
- **Google Gemini API Key** ([Get one here](https://ai.google.dev/))

## 🛠️ Installation & Setup

### Option 1: Using Conda (Recommended)

1. **Navigate to the backend directory**:
   ```bash
   cd ai-voice-interviewer-python-BE
   ```

2. **Activate your conda environment**:
   ```bash
   conda activate usualenv  # or your preferred environment
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   ```bash
   cp env.example .env
   ```

5. **Edit `.env` with your API keys**:
   ```bash
   nano .env  # or use your preferred editor
   ```

6. **Start the server**:
   ```bash
   uvicorn asgi_app:app --host 0.0.0.0 --port 3000 --reload
   ```

### Option 2: Using Virtual Environment

1. **Create and activate virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Follow steps 4-6 from Option 1**

## ⚙️ Configuration

Edit your `.env` file with the following settings:

```env
# Server Configuration
PORT=3000
HOST=0.0.0.0
DEBUG=true

# 🔑 AI API Keys (REQUIRED)
GEMINI_API_KEY=your-gemini-api-key-here
GEMINI_MODEL=gemini-1.5-flash

# 🎵 Audio Configuration (Enhanced for Natural Speech)
SAMPLE_RATE=16000
CHUNK_MS=20
FRAME_BYTES=640
END_SIL_MS=2000          # 2 seconds for thinking pauses
VOICE_START_THRESHOLD=8   # More frames needed to start
VOICE_END_THRESHOLD=100   # 2 seconds before ending speech

# 🎯 Gemini Audio Configuration
GEMINI_AUDIO_MODEL=gemini-1.5-flash

# 🔐 Security (Optional)
JWT_SECRET=your-jwt-secret-key-here

# 📊 Rate Limiting (Optional)
RATE_LIMIT_WINDOW_MS=900000
RATE_LIMIT_MAX_REQUESTS=100

# 🌐 CORS Configuration
CORS_ORIGIN=http://localhost:3000
```

### 🔑 Getting Your Gemini API Key

1. Visit [Google AI Studio](https://ai.google.dev/)
2. Sign in with your Google account
3. Create a new API key
4. Copy the key to your `.env` file

## 🌐 API Endpoints

### HTTP Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check with system status |
| `/api/status` | GET | API status and active sessions |
| `/api/interview/types` | GET | Available interview types |
| `/api/interview/files` | GET | List generated interview files |

### WebSocket Endpoint

- **`WS /ws/audio`** - Real-time audio streaming and interview management

#### WebSocket Protocol

**Client → Server**: 
- **Binary audio frames**: Int16 PCM, mono, 16kHz, 640 bytes (20ms)
- **JSON messages**: Interview control and user data

**Server → Client**:
```json
// Connection established
{
  "type": "connection",
  "session_id": "uuid",
  "message": "Connected to AI Interviewer",
  "config": {"sample_rate": 16000, "frame_bytes": 640}
}

// Voice activity detection
{
  "type": "voice_activity",
  "speaking": true,
  "session_id": "uuid",
  "timestamp": "2025-09-10T14:02:03.519Z"
}

// Transcript (with continuation support)
{
  "type": "transcript",
  "text": "Hello, my name is John and I have experience...",
  "final": true,
  "session_id": "uuid",
  "timestamp": "2025-09-10T14:02:03.519Z"
}

// Interview question
{
  "type": "question",
  "question": "Tell me about your experience in caregiving.",
  "question_number": 1,
  "session_id": "uuid"
}

// Interview completion
{
  "type": "interview_complete",
  "session_id": "uuid",
  "transcript_file": "transcript_uuid_timestamp.txt",
  "evaluation_file": "evaluation_uuid_timestamp.txt"
}
```

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │   ASGI App       │    │  Gemini Audio   │
│                 │    │                  │    │  Service        │
│ Audio Capture   │───▶│  WebSocket       │───▶│                 │
│ (20ms frames)   │    │  /ws/audio       │    │ Multimodal API  │
│                 │    │                  │    │ + Smart Filter  │
│ Interview UI    │◀───│  JSON Messages   │◀───│                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  Gemini Service  │
                    │                  │
                    │ Question Gen     │
                    │ Response Analysis│
                    │ Final Evaluation │
                    └──────────────────┘
```

### 🧩 Key Components

1. **`asgi_app.py`**: Main ASGI application with enhanced WebSocket handling
2. **`services/gemini_audio_service.py`**: Gemini multimodal transcription service
3. **`services/gemini_service.py`**: AI conversation and evaluation management
4. **`models/interview_session.py`**: Interview state and data management
5. **`AudioSession`**: Per-connection state with advanced pause tolerance

## 🎯 Enhanced Features

### 🤔 Natural Speech Support

The system now supports natural human speech patterns:

- **Thinking Pauses**: Up to 2 seconds of silence without ending transcription
- **Response Continuation**: Automatically combines speech segments separated by pauses
- **Noise Filtering**: Intelligent filtering of background noise and artifacts
- **Smart Timing**: 10-second window for response continuation

### 📊 Interview Intelligence

- **Dynamic Question Generation**: AI-powered questions based on candidate responses
- **Real-time Analysis**: Immediate feedback on candidate answers
- **Comprehensive Evaluation**: Detailed scoring across multiple competencies
- **Professional Reports**: Generated transcript and evaluation files

## 🧪 Testing

### Quick Health Check
```bash
curl http://localhost:3000/health
```

### WebSocket Test
```bash
# Install wscat if needed
npm install -g wscat

# Test WebSocket connection
wscat -c ws://localhost:3000/ws/audio
```

### Run Test Suite
```bash
pytest test_*.py -v
```

## 🚀 Production Deployment

### Using Docker (Recommended)
```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 3000

CMD ["uvicorn", "asgi_app:app", "--host", "0.0.0.0", "--port", "3000", "--workers", "2"]
```

### Using Heroku
```bash
# Procfile is included
git push heroku main
```

### Environment Variables for Production
```env
DEBUG=false
GEMINI_API_KEY=your-production-key
CORS_ORIGIN=https://yourdomain.com
```

## 🔧 Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| **WebSocket connection fails** | Check server port (3000) and CORS settings |
| **Audio frames rejected** | Verify 640-byte frames, Int16 PCM, 16kHz |
| **Gemini API errors** | Verify API key and check quota limits |
| **Poor transcription** | Check microphone levels and background noise |
| **Disconnect errors** | Normal behavior - improved handling implemented |

### 🎛️ Performance Tuning

```env
# For better performance
END_SIL_MS=1500          # Faster response (1.5s)
VOICE_END_THRESHOLD=75   # Quicker detection

# For more accuracy
END_SIL_MS=3000          # More thinking time (3s)
VOICE_END_THRESHOLD=150  # Longer wait
```

### 📊 Monitoring

Check system health:
```bash
curl http://localhost:3000/health | jq
```

View active sessions:
```bash
curl http://localhost:3000/api/status | jq
```

## 📁 Generated Files

Interview outputs are saved in `interview-outputs/`:
- `transcript_[session-id]_[timestamp].txt` - Complete interview transcript
- `evaluation_[session-id]_[timestamp].txt` - AI-generated candidate evaluation

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section above
2. Review the logs with `DEBUG=true`
3. Open an issue on GitHub with logs and configuration

---

**🎉 Ready to conduct intelligent AI interviews with natural speech support!**