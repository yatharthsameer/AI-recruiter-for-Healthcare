# 🎤 AI Voice Interviewer

A comprehensive AI-powered interview platform with real-time speech recognition, intelligent conversation management, and advanced candidate evaluation using Google's Gemini multimodal capabilities.

## 🌟 Overview

This platform revolutionizes the interview process by combining:
- **Real-time speech recognition** with natural pause tolerance
- **AI-powered question generation** tailored to candidate responses  
- **Intelligent conversation flow** with contextual follow-ups
- **Comprehensive candidate evaluation** with detailed scoring
- **Professional transcript generation** for hiring decisions

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           AI Voice Interviewer Platform                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────────────┐ │
│  │  Admin Panel    │    │ Interview FE    │    │        Server           │ │
│  │                 │    │                 │    │                         │ │
│  │ • React + TS    │    │ • React + TS    │    │ • Python FastAPI       │ │
│  │ • TanStack      │    │ • WebRTC Audio  │    │ • WebSocket Server      │ │
│  │ • shadcn/ui     │    │ • Real-time UI  │    │ • Admin REST APIs       │ │
│  │ • Analytics     │    │ • Device Mgmt   │    │ • Interview WebSocket   │ │
│  └─────────────────┘    └─────────────────┘    └─────────────────────────┘ │
│          │                        │                         │               │
│          │                        │                         │               │
│          └────────HTTP API────────┼─────────────────────────┘               │
│                                   │                                         │
│                                   └──WebSocket Audio Stream─────┐           │
│                                                                 │           │
│                                                                 ▼           │
│                                                   ┌─────────────────────┐   │
│                                                   │    Gemini AI        │   │
│                                                   │                     │   │
│                                                   │ • Multimodal API    │   │
│                                                   │ • Speech-to-Text    │   │
│                                                   │ • Question Gen      │   │
│                                                   │ • Response Analysis │   │
│                                                   │ • Final Evaluation  │   │
│                                                   └─────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- **Node.js 18+** for frontend components
- **Python 3.8+** (Python 3.12 recommended) for server
- **Google Gemini API Key** ([Get one here](https://ai.google.dev/))

### 1. Server Setup (Required First) 🖥️

The server handles both the interview WebSocket connections and admin panel API endpoints.

```bash
# Navigate to server directory
cd Server

# Install dependencies (using conda recommended)
conda activate usualenv  # or your environment
pip install -r requirements.txt

# Configure environment
cp env.example .env
# Edit .env with your GEMINI_API_KEY

# Start server (handles both interview and admin APIs)
uvicorn asgi_app:app --host 0.0.0.0 --port 3000 --reload
```

### 2. Admin Panel Setup 👨‍💼

Modern admin dashboard for managing interviews, candidates, and system settings.

```bash
# Navigate to admin panel directory (new terminal)
cd Admin_Panel

# Install dependencies
npm install
# or
pnpm install
# or
yarn install

# Start admin panel
npm run dev
```

### 3. Interview Frontend Setup 🎤

The candidate-facing interview interface with real-time audio processing.

```bash
# Navigate to interview frontend directory (new terminal)
cd ai-voice-interviewer-FE

# Install dependencies
npm install

# Configure environment (optional)
echo "VITE_API_BASE_URL=http://localhost:3000" > .env.local
echo "VITE_WS_BASE_URL=ws://localhost:3000" >> .env.local

# Start interview frontend
npm run dev
```

### 4. Access All Components

- **🎤 Interview Frontend**: http://localhost:5173 (candidates use this)
- **👨‍💼 Admin Panel**: http://localhost:5174 (admins use this)
- **🖥️ Server API**: http://localhost:3000 (backend for both)
- **📊 Health Check**: http://localhost:3000/health

## 📁 Project Structure

```
ai-voice-interviewer/
├── 📂 Admin_Panel/                       # Admin Dashboard (React + TanStack)
│   ├── src/
│   │   ├── components/                   # UI Components (shadcn/ui)
│   │   ├── features/                     # Feature-based modules
│   │   │   ├── candidates/              # Candidate management
│   │   │   ├── dashboard/               # Analytics dashboard
│   │   │   ├── settings/                # System settings
│   │   │   └── users/                   # User management
│   │   ├── routes/                       # TanStack Router routes
│   │   └── lib/                          # Utilities & Config
│   ├── package.json
│   └── README.md                         # Admin Panel Documentation
│
├── 📂 ai-voice-interviewer-FE/          # Interview Frontend (React + Vite)
│   ├── src/
│   │   ├── components/                   # UI Components
│   │   │   ├── interview/               # Interview-specific components
│   │   │   ├── forms/                   # Application forms
│   │   │   └── ui/                      # Reusable UI components
│   │   ├── hooks/                        # Custom React Hooks
│   │   ├── pages/                        # Page Components
│   │   └── lib/                          # Utilities & Config
│   ├── package.json
│   └── README.md                         # Interview Frontend Documentation
│
├── 📂 Server/                            # Python Server (FastAPI + WebSocket)
│   ├── services/                         # Core Services
│   │   ├── gemini_audio_service.py      # Speech Recognition (Gemini)
│   │   ├── gemini_service.py            # AI Conversation Management
│   │   └── caregiver_evaluation_service.py # Specialized Evaluations
│   ├── models/                           # Data Models & Schemas
│   ├── utils/                            # Utilities & Helpers
│   ├── interview-outputs/               # Generated Interview Files
│   ├── requirements.txt                  # Python Dependencies
│   ├── asgi_app.py                      # Main ASGI Application
│   ├── api_server.py                    # Admin API Endpoints
│   └── README.md                         # Server Documentation
│
├── 📄 README.md                          # This file (Main Documentation)
├── 📄 MIGRATION_GUIDE.md                # Whisper → Gemini Migration Guide
├── 📄 AUDIO_FEEDBACK_FIX.md            # Audio Issues Troubleshooting
└── 📄 FRONTEND_BACKEND_TEST.md          # Comprehensive Testing Guide
```

## ✨ Key Features

### 🎤 Advanced Audio Processing
- **Real-time Speech Recognition** using Gemini multimodal API
- **Natural Pause Tolerance** - supports thinking time up to 2 seconds
- **Response Continuation** - automatically combines speech segments
- **Noise Filtering** - intelligent filtering of background noise
- **Voice Activity Detection** - visual feedback for speech detection

### 🧠 AI-Powered Intelligence
- **Dynamic Question Generation** - contextual follow-up questions
- **Real-time Response Analysis** - immediate candidate feedback
- **Comprehensive Evaluation** - detailed scoring across competencies
- **Professional Reports** - generated transcripts and evaluations
- **Interview Type Support** - customizable for different roles

### 🎨 Modern User Experience
- **Responsive Design** - works on desktop and mobile
- **Device Management** - camera/microphone selection and testing
- **Real-time Feedback** - live transcription and progress tracking
- **Accessibility** - WCAG compliant interface
- **Professional UI** - built with shadcn/ui components

## 🧩 Component Overview

### 👨‍💼 Admin Panel (`Admin_Panel/`)
**Modern administrative dashboard for managing the interview platform**

- **🎯 Purpose**: Centralized management interface for HR teams and administrators
- **⚡ Tech Stack**: React 19, TanStack Router, TanStack Query, shadcn/ui, Tailwind CSS
- **🔧 Features**:
  - **Candidate Management**: View, filter, and manage candidate applications
  - **Interview Analytics**: Real-time dashboards and performance metrics
  - **User Management**: Admin user roles and permissions
  - **System Settings**: Platform configuration and customization
  - **Report Generation**: Export interview data and analytics
- **🌐 Access**: http://localhost:5174
- **📦 Package Manager**: npm, pnpm, or yarn

### 🎤 Interview Frontend (`ai-voice-interviewer-FE/`)
**Candidate-facing interview interface with real-time audio processing**

- **🎯 Purpose**: Interactive interview experience for candidates
- **⚡ Tech Stack**: React 18, Vite, WebRTC, shadcn/ui, Tailwind CSS
- **🔧 Features**:
  - **Real-time Audio Capture**: High-quality microphone input with WebRTC
  - **Live Transcription**: Real-time speech-to-text display
  - **Device Setup**: Camera/microphone testing and selection
  - **Interview Flow**: Guided interview process with AI questions
  - **Progress Tracking**: Visual progress indicators and completion status
- **🌐 Access**: http://localhost:5173
- **📦 Package Manager**: npm (recommended)

### 🖥️ Server (`Server/`)
**Python backend handling both interview WebSocket connections and admin APIs**

- **🎯 Purpose**: Core server providing APIs for both admin panel and interview frontend
- **⚡ Tech Stack**: Python 3.8+, FastAPI, WebSocket, Gemini AI, Starlette
- **🔧 Features**:
  - **WebSocket Server**: Real-time audio processing for interviews
  - **REST APIs**: Admin panel endpoints for data management
  - **Gemini Integration**: AI-powered speech recognition and conversation
  - **Interview Management**: Session handling and state management
  - **File Generation**: Automatic transcript and evaluation reports
- **🌐 Access**: http://localhost:3000
- **🐍 Environment**: conda or virtualenv recommended

## 🔧 Configuration

### Server Configuration (`Server/.env`)
```env
# Required
GEMINI_API_KEY=your-gemini-api-key-here

# Audio Settings (Enhanced for Natural Speech)
END_SIL_MS=2000          # 2 seconds for thinking pauses
VOICE_START_THRESHOLD=8   # More frames needed to start
VOICE_END_THRESHOLD=100   # 2 seconds before ending speech

# Server Settings
PORT=3000
DEBUG=true
```

### Frontend Configuration (`.env.local`)
```env
# Backend Connection
VITE_API_BASE_URL=http://localhost:3000
VITE_WS_BASE_URL=ws://localhost:3000

# Branding (Optional)
VITE_APP_TITLE="AI Voice Interviewer"
VITE_COMPANY_NAME="Your Company"
```

## 🎯 Usage Flow

1. **📝 Application Form** - Candidate fills out detailed application
2. **🔧 Device Setup** - Camera/microphone testing and configuration
3. **🎤 Interview Session** - AI-conducted interview with real-time transcription
4. **📊 Evaluation** - Comprehensive AI analysis and scoring
5. **📄 Results** - Professional transcript and evaluation report

## 🧪 Testing

### Server Testing
```bash
cd Server

# Health check
curl http://localhost:3000/health

# WebSocket test
pip install websockets
python test_websocket.py

# Complete interview test
python test_complete_interview.py
```

### Admin Panel Testing
```bash
cd Admin_Panel

# Build test
npm run build

# Type checking (if available)
npm run type-check

# Linting
npm run lint

# Format check
npm run format:check
```

### Interview Frontend Testing
```bash
cd ai-voice-interviewer-FE

# Build test
npm run build

# Development build
npm run build:dev

# Linting
npm run lint

# Preview production build
npm run preview
```

### Integration Testing
```bash
# 1. Start all components (3 terminals)
# Terminal 1: Server
cd Server && conda activate usualenv && uvicorn asgi_app:app --reload

# Terminal 2: Admin Panel  
cd Admin_Panel && npm run dev

# Terminal 3: Interview Frontend
cd ai-voice-interviewer-FE && npm run dev

# 2. Test complete flow
# - Access admin panel: http://localhost:5174
# - Access interview: http://localhost:5173
# - Check server health: http://localhost:3000/health
```

## 🚀 Deployment

### Production Server
```bash
cd Server

# Direct deployment
pip install -r requirements.txt
uvicorn asgi_app:app --host 0.0.0.0 --port $PORT --workers 2

# Using Heroku
git push heroku main
```

### Production Admin Panel
```bash
cd Admin_Panel

# Build for production
npm run build

# Deploy to Netlify/Vercel
# Upload dist/ folder or connect Git repository

# Environment variables for production
VITE_API_BASE_URL=https://your-server-domain.com
```

### Production Interview Frontend
```bash
cd ai-voice-interviewer-FE

# Build for production
npm run build

# Deploy to Netlify/Vercel
# Upload dist/ folder or connect Git repository

# Environment variables for production
VITE_API_BASE_URL=https://your-server-domain.com
VITE_WS_BASE_URL=wss://your-server-domain.com
```


## 🔧 Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| **Server won't start** | Check Python version (3.8+) and install requirements in `Server/` |
| **Admin panel connection fails** | Ensure server is running on port 3000 |
| **Interview frontend connection fails** | Ensure server WebSocket is accessible on port 3000 |
| **Audio not working** | Check browser permissions and device selection |
| **Gemini API errors** | Verify API key and check quota limits |
| **WebSocket disconnects** | Normal behavior - improved handling implemented |
| **Port conflicts** | Admin panel (5174), Interview (5173), Server (3000) |
| **CORS issues** | Check server CORS settings for frontend domains |

### Debug Mode

Enable detailed logging:
```bash
# Server
cd Server
DEBUG=true uvicorn asgi_app:app --reload

# Admin Panel
cd Admin_Panel
VITE_DEBUG=true npm run dev

# Interview Frontend
cd ai-voice-interviewer-FE
VITE_DEBUG=true npm run dev
```

## 📊 Performance

### Optimized for Real-time Performance
- **Low Latency**: ~100ms audio processing
- **Efficient Streaming**: 20ms audio chunks
- **Smart Buffering**: Prevents audio dropouts
- **Resource Management**: Automatic cleanup and memory management

### Scalability
- **Concurrent Sessions**: Supports multiple simultaneous interviews
- **Load Balancing**: Ready for horizontal scaling
- **Database Ready**: Easily integrate with your preferred database
- **API Integration**: RESTful APIs for external system integration

## 🤝 Contributing

We welcome contributions! Please see individual README files for:
- [Backend Contributing Guide](ai-voice-interviewer-python-BE/README.md#contributing)
- [Frontend Contributing Guide](ai-voice-interviewer-FE/README.md#contributing)

### Development Setup
1. Fork the repository
2. Set up both backend and frontend (see Quick Start)
3. Make your changes with proper testing
4. Submit a pull request with clear description

## 📄 Documentation

- **[Backend Documentation](ai-voice-interviewer-python-BE/README.md)** - Detailed Python backend guide
- **[Frontend Documentation](ai-voice-interviewer-FE/README.md)** - Complete React frontend guide
- **[Migration Guide](MIGRATION_GUIDE.md)** - Whisper to Gemini migration details
- **[Audio Troubleshooting](AUDIO_FEEDBACK_FIX.md)** - Audio issues and solutions
- **[Testing Guide](FRONTEND_BACKEND_TEST.md)** - Comprehensive testing instructions

## 🔒 Security & Privacy

- **Data Protection**: No audio data stored permanently
- **Secure Communication**: WebSocket with proper error handling
- **API Security**: Rate limiting and input validation
- **Privacy Compliant**: GDPR-ready with data minimization

## 📈 Roadmap

- [ ] **Multi-language Support** - Support for multiple languages
- [ ] **Video Analysis** - Facial expression and body language analysis
- [ ] **Integration APIs** - Connect with ATS and HR systems
- [ ] **Advanced Analytics** - Interview performance dashboards
- [ ] **Mobile App** - Native mobile applications

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details

## 🆘 Support

For support and questions:

1. **Documentation**: Check the comprehensive guides above
2. **Issues**: Open a GitHub issue with detailed information
3. **Discussions**: Use GitHub Discussions for questions and ideas

**Include in your issue:**
- Operating system and browser version
- Error messages and console logs
- Steps to reproduce the problem
- Configuration details (without sensitive keys)

---

**🎉 Transform your hiring process with AI-powered interviews!**

*Built with ❤️ using React, Python, and Google Gemini AI*
