# AI Voice Interviewer Frontend

Modern React-based frontend for conducting real-time AI interviews with advanced audio processing and intelligent conversation management.

## 🚀 Features

- **🎤 Real-time Audio Capture**: High-quality microphone input with WebRTC
- **🎯 Voice Activity Detection**: Visual feedback for speech detection
- **💬 Live Transcription**: Real-time speech-to-text with Gemini integration
- **🤖 AI Interview Management**: Intelligent question generation and flow control
- **📊 Device Management**: Camera and microphone selection with testing
- **🎨 Modern UI**: Beautiful, responsive interface built with shadcn/ui
- **📱 Mobile Responsive**: Works seamlessly on desktop and mobile devices
- **🔄 Real-time Updates**: WebSocket-based communication with the backend
- **📋 Application Forms**: Comprehensive candidate data collection
- **📈 Progress Tracking**: Visual interview progress and completion status

## 🛠️ Tech Stack

- **⚛️ React 18** with TypeScript
- **⚡ Vite** for fast development and building
- **🎨 Tailwind CSS** for styling
- **🧩 shadcn/ui** for beautiful UI components
- **🔌 WebSocket** for real-time communication
- **🎵 Web Audio API** for audio processing
- **📱 Responsive Design** with mobile-first approach

## 📋 Prerequisites

- **Node.js 18+** (Node.js 20 recommended)
- **npm** or **yarn** package manager
- **Modern browser** with WebRTC support (Chrome, Firefox, Safari, Edge)

## 🛠️ Installation & Setup

### 1. Clone and Navigate
```bash
cd ai-voice-interviewer-FE
```

### 2. Install Dependencies
```bash
# Using npm
npm install

# Or using yarn
yarn install

# Or using bun (fastest)
bun install
```

### 3. Environment Configuration
Create a `.env.local` file in the root directory:

```env
# Backend API Configuration
VITE_API_BASE_URL=http://localhost:3000
VITE_WS_BASE_URL=ws://localhost:3000

# Audio Configuration (must match backend)
VITE_SAMPLE_RATE=16000
VITE_CHUNK_MS=20
VITE_FRAME_BYTES=640

# Application Settings
VITE_APP_TITLE="AI Voice Interviewer"
VITE_COMPANY_NAME="Your Company"
```

### 4. Start Development Server
```bash
# Using npm
npm run dev

# Using yarn
yarn dev

# Using bun
bun dev
```

The application will be available at `http://localhost:5173`

## 🏗️ Project Structure

```
src/
├── components/           # Reusable UI components
│   ├── ui/              # shadcn/ui components
│   ├── forms/           # Form components
│   │   └── ApplicationForm.tsx
│   ├── interview/       # Interview-specific components
│   │   ├── AIAvatar.tsx
│   │   ├── DeviceSetup.tsx
│   │   ├── InterviewSession.tsx
│   │   ├── MicrophoneTest.tsx
│   │   └── SelfView.tsx
│   ├── AppShell.tsx     # Main app layout
│   └── ProgressBar.tsx  # Progress indicator
├── hooks/               # Custom React hooks
│   ├── useSimpleInterview.tsx  # Main interview logic
│   ├── use-mobile.tsx   # Mobile detection
│   └── use-toast.ts     # Toast notifications
├── lib/                 # Utilities and configurations
│   ├── schema.ts        # Form validation schemas
│   ├── store.tsx        # Global state management
│   └── utils.ts         # Helper functions
├── pages/               # Page components
│   ├── Apply.tsx        # Application form page
│   ├── Index.tsx        # Landing page
│   ├── Interview.tsx    # Full interview page
│   ├── SimpleInterview.tsx  # Streamlined interview
│   ├── Results.tsx      # Interview results
│   ├── ThankYou.tsx     # Completion page
│   └── NotFound.tsx     # 404 page
├── assets/              # Static assets
└── styles/              # Global styles
```

## 🎯 Key Components

### 🎤 Audio Processing (`useSimpleInterview.tsx`)

The main hook that handles:
- **WebSocket connection** to backend
- **Audio capture** and streaming
- **Real-time transcription** display
- **Interview state management**
- **Voice activity detection**

```typescript
const {
  state,           // 'connecting' | 'ready' | 'interviewing' | 'listening' | 'speaking' | 'completed'
  sessionId,       // Unique session identifier
  currentQuestion, // Current AI-generated question
  isConnected,     // WebSocket connection status
  isRecording,     // Audio recording status
  connect,         // Connect to backend
  startInterview,  // Begin interview process
  endInterview,    // End interview session
  disconnect       // Disconnect from backend
} = useSimpleInterview();
```

### 📱 Device Management (`DeviceSetup.tsx`)

Comprehensive device setup with:
- **Camera selection** and preview
- **Microphone selection** and testing
- **Audio level monitoring**
- **Permission handling**
- **Device compatibility checks**

### 🎨 Interview Interface (`InterviewSession.tsx`)

Full interview experience featuring:
- **AI avatar** with speaking animations
- **Live transcription** display
- **Progress tracking** with question numbers
- **Device controls** and settings
- **Emergency controls** (end interview, restart)

## 🔧 Configuration

### Audio Settings

The frontend audio configuration must match the backend:

```typescript
// Audio configuration (must match Python backend)
const SAMPLE_RATE = 16000;  // 16kHz sampling rate
const CHUNK_MS = 20;        // 20ms audio chunks
const FRAME_BYTES = 640;    // 640 bytes per frame (320 samples × 2 bytes)
```

### WebSocket Communication

The app communicates with the backend via WebSocket:

```typescript
const WS_URL = 'ws://localhost:3000/ws/audio';

// Message types handled:
// - connection: Initial connection confirmation
// - voice_activity: Speech detection updates
// - transcript: Real-time transcription results
// - question: AI-generated interview questions
// - interview_complete: Interview completion notification
```

## 🎨 Styling and Theming

### Tailwind CSS Configuration

The project uses a custom Tailwind configuration with:
- **Custom color palette** for branding
- **Responsive breakpoints** for mobile-first design
- **Custom animations** for smooth interactions
- **Dark mode support** (optional)

### shadcn/ui Components

Pre-built, accessible components:
- **Forms**: Input, Select, Checkbox, Radio groups
- **Feedback**: Toast, Alert, Progress bars
- **Layout**: Card, Sheet, Dialog, Tabs
- **Navigation**: Button, Badge, Breadcrumb

## 🧪 Testing

### Manual Testing Checklist

- [ ] **Device Permissions**: Camera and microphone access
- [ ] **Audio Quality**: Clear recording and playback
- [ ] **WebSocket Connection**: Stable real-time communication
- [ ] **Interview Flow**: Complete end-to-end interview
- [ ] **Responsive Design**: Mobile and desktop compatibility
- [ ] **Error Handling**: Network issues and device failures

### Browser Compatibility

| Browser | Version | Support |
|---------|---------|---------|
| Chrome | 90+ | ✅ Full |
| Firefox | 88+ | ✅ Full |
| Safari | 14+ | ✅ Full |
| Edge | 90+ | ✅ Full |

## 🚀 Building for Production

### Build the Application
```bash
# Create production build
npm run build

# Preview production build locally
npm run preview
```

### Deployment Options

#### 1. Static Hosting (Recommended)
```bash
# Build and deploy to Netlify, Vercel, or similar
npm run build
# Upload dist/ folder to your hosting provider
```

#### 2. Docker Deployment
```dockerfile
FROM node:20-alpine as builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

#### 3. Environment-Specific Builds
```bash
# Development
VITE_API_BASE_URL=http://localhost:3000 npm run build

# Staging
VITE_API_BASE_URL=https://staging-api.yourcompany.com npm run build

# Production
VITE_API_BASE_URL=https://api.yourcompany.com npm run build
```

## 🔧 Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| **Microphone not working** | Check browser permissions and device selection |
| **WebSocket connection fails** | Verify backend is running on port 3000 |
| **Audio choppy or distorted** | Check microphone quality and background noise |
| **Interview not starting** | Ensure application form is completed |
| **Transcription not appearing** | Check WebSocket connection and backend logs |

### Debug Mode

Enable debug logging by adding to your `.env.local`:
```env
VITE_DEBUG=true
```

This will show detailed console logs for:
- WebSocket messages
- Audio processing events
- State changes
- Error details

### Performance Optimization

For better performance:
```env
# Reduce audio quality for slower devices
VITE_SAMPLE_RATE=8000
VITE_CHUNK_MS=40

# Enable production optimizations
VITE_NODE_ENV=production
```

## 📱 Mobile Considerations

### iOS Safari Specific
- **Audio Context**: Requires user interaction to start
- **WebRTC**: May need additional permissions
- **Fullscreen**: Use viewport meta tag for proper scaling

### Android Chrome Specific
- **Background Processing**: May pause audio in background
- **Memory Management**: Optimize for lower-end devices

## 🤝 Contributing

### Development Workflow
1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/amazing-feature`
3. **Make** your changes with proper TypeScript types
4. **Test** thoroughly on multiple browsers
5. **Commit** with conventional commits: `feat: add amazing feature`
6. **Push** and create a Pull Request

### Code Style
- **TypeScript**: Strict mode enabled
- **ESLint**: Configured for React and TypeScript
- **Prettier**: Automatic code formatting
- **Conventional Commits**: For clear commit history

## 📄 License

MIT License - see LICENSE file for details

## 🆘 Support

For issues and questions:
1. **Check** the troubleshooting section above
2. **Enable** debug mode and check browser console
3. **Verify** backend connection and configuration
4. **Open** an issue on GitHub with:
   - Browser and version
   - Console error messages
   - Steps to reproduce

---

**🎉 Ready to create amazing AI interview experiences!**

## 🔗 Related Projects

- **Backend**: [AI Voice Interviewer Python Backend](../ai-voice-interviewer-python-BE/README.md)
- **Documentation**: Check the project root for additional guides and troubleshooting docs