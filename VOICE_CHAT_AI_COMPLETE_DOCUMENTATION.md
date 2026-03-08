# Voice Chat AI - Complete System Documentation

## Table of Contents
1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Core Components](#core-components)
4. [Database Schema](#database-schema)
5. [API Endpoints](#api-endpoints)
6. [Configuration](#configuration)
7. [Installation & Setup](#installation--setup)
8. [Character System](#character-system)
9. [Enhanced Features](#enhanced-features)
10. [ML & RAG System](#ml--rag-system)
11. [Frontend Implementation](#frontend-implementation)
12. [Deployment](#deployment)
13. [Troubleshooting](#troubleshooting)

---

## System Overview

Voice Chat AI is a sophisticated conversational AI system that enables voice-based interactions with various AI characters. The system supports multiple AI providers (OpenAI, Anthropic, xAI, Ollama), various TTS providers (OpenAI TTS, ElevenLabs, XTTS, Kokoro), and includes advanced features like RAG-based interview scoring, ML predictions, and real-time rankings.

### Key Features
- **Multi-Provider Support**: OpenAI, Anthropic, xAI, Ollama for chat models
- **Flexible TTS**: OpenAI TTS, ElevenLabs, XTTS, Kokoro TTS
- **Character System**: 300+ built-in characters with unique personalities
- **Enhanced Mode**: Emotional TTS with voice instructions
- **WebRTC Realtime**: Direct OpenAI Realtime API integration
- **Interview System**: AI-powered caregiver interview evaluation
- **RAG System**: Semantic answer evaluation using vector databases
- **ML Predictions**: Hiring success prediction models
- **Real-time Rankings**: Live candidate leaderboards

---

## Architecture

### High-Level Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   External      │
│   (HTML/JS)     │◄──►│   (FastAPI)     │◄──►│   Services      │
│                 │    │                 │    │                 │
│ • Web UI        │    │ • API Endpoints │    │ • OpenAI API    │
│ • WebSocket     │    │ • WebSocket     │    │ • ElevenLabs    │
│ • Audio Capture │    │ • Audio Process │    │ • Ollama        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                       ┌─────────────────┐
                       │   Data Layer    │
                       │                 │
                       │ • PostgreSQL    │
                       │ • Redis Cache   │
                       │ • Elasticsearch │
                       │ • File Storage  │
                       └─────────────────┘
```

### Technology Stack
- **Backend**: Python 3.10+, FastAPI, asyncio
- **Database**: PostgreSQL, Redis, Elasticsearch
- **ML/AI**: scikit-learn, sentence-transformers, OpenAI API
- **Audio**: PyAudio, faster-whisper, TTS libraries
- **Frontend**: HTML5, JavaScript, WebSocket, WebRTC
- **Deployment**: Docker, uvicorn, nginx

---

## Core Components

### 1. Main Application (`app/main.py`)
The central FastAPI application that handles:
- HTTP routes and WebSocket connections
- API endpoint definitions
- Request/response handling
- Client management
- File serving

### 2. Core Logic (`app/app.py`)
Contains the fundamental conversation logic:
- Audio recording and playback
- Speech-to-text transcription
- Text-to-speech synthesis
- Mood analysis and sentiment detection
- Character prompt loading
- Multi-provider AI chat integration

### 3. Application Logic (`app/app_logic.py`)
Manages conversation flow and state:
- Conversation loop management
- Character switching
- History management
- Provider initialization
- Settings management

### 4. Enhanced Logic (`app/enhanced_logic.py`)
Implements advanced features:
- Enhanced TTS with voice instructions
- Emotional voice synthesis
- Advanced conversation management
- Character-specific voice instructions

### 5. Enhanced Scoring Engine (`app/enhanced_scoring_engine.py`)
AI-powered interview evaluation:
- Multi-dimensional scoring
- RAG-based answer evaluation
- Contextual adjustments
- Performance analytics

### 6. RAG System (`app/rag_system.py`)
Semantic answer evaluation:
- Vector database integration
- Similarity matching
- Caregiver-specific bonuses
- Confidence scoring

### 7. ML Predictions (`app/ml_predictions.py`)
Machine learning components:
- Hiring success prediction
- Performance forecasting
- Risk factor analysis
- Model training and updates

### 8. Ranking Engine (`app/ranking_engine.py`)
Real-time candidate rankings:
- Live leaderboards
- Tier classification
- Cohort analysis
- Performance metrics

---

## Database Schema

### Core Tables

#### `candidates`
```sql
CREATE TABLE candidates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20),
    caregiving_experience BOOLEAN DEFAULT FALSE,
    availability JSONB,
    weekly_hours INTEGER,
    languages JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB
);
```

#### `interview_sessions`
```sql
CREATE TABLE interview_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    candidate_id UUID REFERENCES candidates(id),
    session_status VARCHAR(20) DEFAULT 'in_progress',
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    total_score DECIMAL(5,2),
    recommendation VARCHAR(20),
    experience_avg DECIMAL(5,2),
    motivation_score DECIMAL(5,2),
    punctuality_avg DECIMAL(5,2),
    empathy_avg DECIMAL(5,2),
    communication_score DECIMAL(5,2),
    audio_filename VARCHAR(255),
    metadata JSONB
);
```

#### `question_responses`
```sql
CREATE TABLE question_responses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES interview_sessions(id),
    question_id VARCHAR(50) NOT NULL,
    question_text TEXT NOT NULL,
    candidate_answer TEXT NOT NULL,
    transcription_confidence DECIMAL(3,2),
    semantic_similarity_score DECIMAL(5,2),
    completeness_score DECIMAL(5,2),
    empathy_score DECIMAL(5,2),
    behavioral_score DECIMAL(5,2),
    rag_best_match_score DECIMAL(3,2),
    rag_match_quality VARCHAR(20),
    empathy_bonus DECIMAL(3,2) DEFAULT 1.0,
    patient_story_bonus DECIMAL(3,2) DEFAULT 1.0,
    final_question_score DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### `candidate_rankings`
```sql
CREATE TABLE candidate_rankings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    candidate_id UUID REFERENCES candidates(id),
    overall_rank INTEGER NOT NULL,
    percentile_rank DECIMAL(5,2),
    tier VARCHAR(5) NOT NULL,
    total_weighted_score DECIMAL(5,2),
    hiring_probability DECIMAL(3,2),
    expected_performance DECIMAL(5,2),
    risk_factors JSONB,
    confidence_level VARCHAR(20),
    last_updated TIMESTAMP DEFAULT NOW()
);
```

#### `expected_answers`
```sql
CREATE TABLE expected_answers (
    id VARCHAR(50) PRIMARY KEY,
    question_id VARCHAR(50) NOT NULL,
    answer_text TEXT NOT NULL,
    quality_level VARCHAR(20) NOT NULL,
    score_range_min INTEGER,
    score_range_max INTEGER,
    empathy_indicators JSONB,
    experience_indicators JSONB,
    behavioral_patterns JSONB,
    embedding_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## API Endpoints

### Core Endpoints

#### `GET /`
Main dashboard interface
- **Response**: HTML page with conversation interface
- **Features**: Character selection, provider settings, conversation controls

#### `POST /start_conversation`
Start a voice conversation
- **Request**: JSON with conversation parameters
- **Response**: `{"status": "started"}`
- **Function**: Initiates conversation loop with selected character

#### `POST /stop_conversation`
Stop active conversation
- **Response**: `{"status": "stopped"}`
- **Function**: Terminates conversation loop and cleans up resources

#### `WebSocket /ws`
Main WebSocket connection for real-time communication
- **Messages**: 
  - `{"action": "start", "character": "character_name"}`
  - `{"action": "stop"}`
  - `{"action": "set_character", "character": "name"}`
  - `{"action": "set_provider", "provider": "openai"}`

### Character Management

#### `GET /characters`
Get available characters
- **Response**: `{"characters": ["character1", "character2", ...]}`
- **Function**: Lists all available character folders

#### `POST /set_character`
Set active character
- **Request**: `{"character": "character_name"}`
- **Response**: `{"status": "success", "message": "Character set"}`

#### `GET /api/character/{character_name}`
Get character prompt
- **Response**: `{"prompt": "character prompt text"}`
- **Function**: Returns character's system prompt

### Enhanced Features

#### `GET /enhanced`
Enhanced conversation interface
- **Response**: HTML page with enhanced features
- **Features**: Emotional TTS, advanced voice controls

#### `POST /start_enhanced_conversation`
Start enhanced conversation
- **Request**: 
```json
{
    "character": "character_name",
    "speed": "1.0",
    "model": "gpt-4o",
    "voice": "coral",
    "ttsModel": "gpt-4o-mini-tts",
    "transcriptionModel": "gpt-4o-mini-transcribe"
}
```

#### `WebSocket /ws_enhanced`
Enhanced WebSocket connection
- **Features**: Real-time status updates, enhanced audio controls

### Interview System

#### `POST /save_interview_transcript`
Save interview transcript
- **Request**: 
```json
{
    "transcript": [{"type": "user", "message": "...", "timestamp": "..."}],
    "userData": {"firstName": "...", "lastName": "...", ...},
    "sessionId": "session_id"
}
```

#### `POST /save_interview_audio`
Save interview audio recording
- **Request**: Multipart form with audio file and metadata
- **Response**: `{"status": "success", "filename": "...", "filepath": "..."}`

#### `POST /evaluate_interview`
Evaluate interview using ChatGPT
- **Request**: Interview transcript and candidate data
- **Response**: Detailed evaluation with scores and recommendations

#### `GET /api/interviews`
Get all completed interviews
- **Response**: List of interview summaries with metadata

#### `GET /api/interviews/{session_id}/transcript`
Get specific interview transcript
- **Response**: Complete transcript with metadata

### Voice and TTS

#### `GET /elevenlabs_voices`
Get ElevenLabs voice options
- **Response**: `{"voices": [{"id": "...", "name": "..."}]}`

#### `GET /kokoro_voices`
Get Kokoro TTS voice options
- **Response**: Organized list of available voices by language

#### `POST /set_transcription_model`
Set transcription model
- **Request**: `{"model": "gpt-4o-mini-transcribe"}`
- **Response**: `{"status": "success"}`

### WebRTC Realtime

#### `GET /webrtc_realtime`
WebRTC realtime interface
- **Response**: HTML page with WebRTC implementation
- **Features**: Direct OpenAI Realtime API connection

#### `GET /openai_ephemeral_key`
Get OpenAI ephemeral key for WebRTC
- **Response**: `{"client_secret": {"value": "api_key"}}`

#### `POST /openai_realtime_proxy`
Proxy WebRTC connection to OpenAI
- **Function**: Handles CORS and proxies WebRTC signaling

### Utility Endpoints

#### `GET /ollama_models`
Get available Ollama models
- **Response**: `{"models": ["llama3.2", "llama3.1", ...]}`

#### `POST /clear_history`
Clear conversation history
- **Response**: `{"status": "cleared"}`

#### `GET /download_history`
Download conversation history
- **Response**: Text file with conversation history

---

## Configuration

### Environment Variables

#### Core Configuration
```bash
# Model Provider: openai, ollama, xai, anthropic
MODEL_PROVIDER=openai

# Character Configuration
CHARACTER_NAME=bigfoot

# TTS Provider: xtts, openai, elevenlabs, kokoro
TTS_PROVIDER=openai
VOICE_SPEED=1.0

# OpenAI Configuration
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4o
OPENAI_MODEL_TTS=gpt-4o-mini-tts
OPENAI_TRANSCRIPTION_MODEL=gpt-4o-mini-transcribe
OPENAI_TTS_VOICE=onyx
OPENAI_REALTIME_MODEL=gpt-4o-realtime-preview-2024-12-17

# Audio Configuration
MAX_CHAR_LENGTH=1000
XTTS_NUM_CHARS=1000

# Local Transcription
FASTER_WHISPER_LOCAL=false

# Debug Settings
DEBUG=false
DEBUG_AUDIO_LEVELS=false
```

#### Enhanced System Configuration
```bash
# Database Configuration
DATABASE_URL=postgresql://interview_admin:secure_password@localhost:5432/interview_bot
REDIS_URL=redis://localhost:6379/0
ELASTICSEARCH_URL=http://localhost:9200

# Enhanced Features
RAG_SYSTEM_ENABLED=true
ML_PREDICTIONS_ENABLED=true
REAL_TIME_RANKINGS_ENABLED=true

# Scoring Configuration
SCORING_SCALE=100
EMPATHY_BONUS_MULTIPLIER=1.12
PATIENT_STORY_BONUS_MULTIPLIER=1.08

# Question Weights
EXPERIENCE_WEIGHT=0.30
MOTIVATION_WEIGHT=0.20
PUNCTUALITY_WEIGHT=0.15
EMPATHY_WEIGHT=0.25
COMMUNICATION_WEIGHT=0.10

# Tier Thresholds
TIER_A_PLUS_SCORE=90
TIER_A_PLUS_PERCENTILE=95
TIER_A_SCORE=85
TIER_A_PERCENTILE=85
```

### Configuration Manager (`app/config.py`)
Centralized configuration management with validation and export capabilities.

---

## Installation & Setup

### Prerequisites
- Python 3.10+
- PostgreSQL 12+
- Redis 6+
- Elasticsearch 8+ (optional, for RAG features)
- FFmpeg
- Microphone access

### Basic Installation

1. **Clone Repository**
```bash
git clone https://github.com/bigsk1/voice-chat-ai.git
cd voice-chat-ai
```

2. **Create Virtual Environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install Dependencies**
```bash
# For CPU-only installation
pip install -r requirements_cpu.txt

# For GPU installation (CUDA)
pip install -r requirements.txt
```

4. **Configure Environment**
```bash
cp .env.sample .env
# Edit .env with your API keys and settings
```

5. **Setup Database** (for enhanced features)
```bash
# Create PostgreSQL database
createdb interview_bot

# Run schema
psql -d interview_bot -f database/schema.sql

# Seed reference answers (optional)
psql -d interview_bot -f database/seed_reference_answers.sql
```

6. **Start Application**
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Docker Installation

1. **Basic Docker Run**
```bash
docker run -d \
  --env-file .env \
  --name voice-chat-ai \
  -p 8000:8000 \
  bigsk1/voice-chat-ai:latest
```

2. **Docker Compose**
```yaml
version: '3.8'
services:
  voice-chat-ai:
    image: bigsk1/voice-chat-ai:latest
    container_name: voice-chat-ai
    env_file: .env
    ports:
      - "8000:8000"
    volumes:
      - ./elevenlabs_voices.json:/app/elevenlabs_voices.json
    restart: unless-stopped
```

### Enhanced System Setup

1. **Database Setup**
```bash
# PostgreSQL
docker run -d \
  --name postgres-interview \
  -e POSTGRES_DB=interview_bot \
  -e POSTGRES_USER=interview_admin \
  -e POSTGRES_PASSWORD=secure_password \
  -p 5432:5432 \
  postgres:15

# Redis
docker run -d \
  --name redis-interview \
  -p 6379:6379 \
  redis:7-alpine

# Elasticsearch (optional)
docker run -d \
  --name elasticsearch-interview \
  -e "discovery.type=single-node" \
  -e "xpack.security.enabled=false" \
  -p 9200:9200 \
  elasticsearch:8.11.0
```

2. **Initialize Enhanced System**
```bash
python setup_enhanced_system.py
```

---

## Character System

### Character Structure
Each character is defined by files in the `characters/` directory:

```
characters/
├── character_name/
│   ├── character_name.txt      # System prompt
│   ├── prompts.json           # Mood-specific prompts
│   └── character_name.wav     # Voice sample (for XTTS)
```

### Character Prompt Format (`character_name.txt`)
```
You are a wise and ancient wizard who speaks with a mystical tone.

VOICE INSTRUCTIONS:
- Voice Quality: Rich and resonant with age-weathered gravitas
- Pacing: Thoughtful and measured with meaningful pauses
- Tone: Authoritative wisdom mixed with approachable warmth
- Inflection: Classic pattern emphasizing cosmic truths
```

### Mood Prompts (`prompts.json`)
```json
{
    "happy": "RESPOND WITH JOY AND ENTHUSIASM. Voice: Brightest and vibrant. Pacing: Energetic with excited pauses.",
    "sad": "RESPOND WITH KINDNESS AND COMFORT. Voice: Deep and warm. Pacing: Slow and deliberate.",
    "angry": "RESPOND CALMLY AND WISELY. Voice: Controlled and steady. Tone: Ancient perspective.",
    "neutral": "KEEP RESPONSES SHORT YET PROFOUND. Voice: Balanced scholarly timbre.",
    "fearful": "RESPOND WITH REASSURANCE. Voice: Initially commanding then softening.",
    "surprised": "RESPOND WITH AMAZEMENT. Voice: Higher with excitement then scholarly.",
    "disgusted": "RESPOND WITH UNDERSTANDING. Voice: Crisp then warming to pleasant topics.",
    "joyful": "RESPOND WITH EXUBERANCE. Voice: Most radiant with magical energy."
}
```

### Creating New Characters

1. **Create Character Directory**
```bash
mkdir characters/new_character
```

2. **Create System Prompt**
```bash
# characters/new_character/new_character.txt
echo "You are [character description]..." > characters/new_character/new_character.txt
```

3. **Create Mood Prompts**
```bash
# characters/new_character/prompts.json
cat > characters/new_character/prompts.json << EOF
{
    "happy": "Response instructions for happy mood...",
    "sad": "Response instructions for sad mood...",
    ...
}
EOF
```

4. **Add Voice Sample** (optional, for XTTS)
```bash
# Add 6-second voice sample
cp voice_sample.wav characters/new_character/new_character.wav
```

---

## Enhanced Features

### Enhanced TTS with Voice Instructions

The enhanced mode supports emotional voice synthesis using OpenAI's `gpt-4o-mini-tts` model with voice instructions.

#### Voice Instruction Categories
- **Voice Quality**: Timbre, resonance, age characteristics
- **Pacing**: Speed, pauses, rhythm
- **Tone**: Emotional coloring, mood
- **Inflection**: Pitch patterns, emphasis
- **Pronunciation**: Articulation, clarity
- **Delivery**: Speaking style, formality
- **Emphasis**: Stress patterns, focus
- **Pauses**: Timing, dramatic effect
- **Emotion**: Emotional expression level

#### Implementation
```python
async def enhanced_text_to_speech(text, detected_mood=None):
    # Load character prompt and extract voice instructions
    character_prompt = load_character_prompt(character_name)
    base_instructions = parse_voice_instructions(character_prompt)
    
    # Load mood-specific instructions
    mood_instructions = load_mood_instructions(character_name, detected_mood)
    
    # Combine instructions with priority to mood-specific
    final_instructions = combine_instructions(base_instructions, mood_instructions)
    
    # Make TTS request with voice instructions
    payload = {
        "model": "gpt-4o-mini-tts",
        "input": text,
        "voice": voice,
        "voice_instructions": final_instructions
    }
```

### WebRTC Realtime Integration

Direct integration with OpenAI's Realtime API for low-latency conversations.

#### Features
- Zero turn-taking delay
- Natural interruption handling
- Character personality integration
- Real-time audio streaming

#### Implementation
```javascript
// WebRTC connection setup
const pc = new RTCPeerConnection();

// Create data channel for character instructions
const dataChannel = pc.createDataChannel('character_instructions');

// Send character context
dataChannel.send(JSON.stringify({
    character_name: selectedCharacter,
    system_prompt: characterPrompt,
    voice_instructions: voiceInstructions
}));

// Handle audio streams
pc.ontrack = (event) => {
    const audioElement = document.getElementById('ai-audio');
    audioElement.srcObject = event.streams[0];
};
```

---

## ML & RAG System

### RAG System Architecture

The RAG (Retrieval-Augmented Generation) system provides semantic evaluation of interview answers.

#### Components
1. **Vector Database**: Elasticsearch with sentence-transformers embeddings
2. **Expected Answers**: Curated high-quality reference answers
3. **Similarity Matching**: Cosine similarity with quality mapping
4. **Contextual Bonuses**: Caregiver-specific scoring adjustments

#### RAG Evaluation Process
```python
async def evaluate_answer(question_id: str, candidate_answer: str) -> RAGEvaluationResult:
    # Generate embedding for candidate answer
    candidate_embedding = embedding_model.encode(candidate_answer)
    
    # Search for similar answers in vector database
    search_results = await elasticsearch_search(question_id, candidate_embedding)
    
    # Get best match and calculate similarity score
    best_match = search_results[0]
    similarity_score = best_match.score
    
    # Map similarity to quality-based score
    quality_score = map_similarity_to_score(similarity_score, best_match.quality_level)
    
    # Calculate caregiver-specific bonuses
    empathy_bonus = calculate_empathy_bonus(candidate_answer)
    patient_story_bonus = calculate_patient_story_bonus(candidate_answer)
    care_experience_bonus = calculate_care_experience_bonus(candidate_answer)
    dignity_mention_bonus = calculate_dignity_mention_bonus(candidate_answer)
    
    # Calculate final score with bonuses
    final_score = min(
        quality_score * empathy_bonus * patient_story_bonus * 
        care_experience_bonus * dignity_mention_bonus,
        100.0
    )
    
    return RAGEvaluationResult(...)
```

### ML Prediction System

Machine learning models predict hiring success and job performance.

#### Features
- **Hiring Probability**: Likelihood of successful hire
- **Performance Prediction**: Expected job performance rating
- **Risk Analysis**: Identification of potential concerns
- **Similar Candidates**: Historical comparison data

#### Model Training
```python
async def train_models():
    # Get historical training data
    training_data = await get_training_data()
    
    # Prepare features and targets
    X = prepare_features(training_data)
    y_hiring = [d['hired'] for d in training_data]
    y_performance = [d['performance_rating'] for d in training_data]
    
    # Train models
    hiring_model = RandomForestClassifier(n_estimators=100, class_weight='balanced')
    performance_model = RandomForestRegressor(n_estimators=100)
    
    hiring_model.fit(X_scaled, y_hiring)
    performance_model.fit(X_scaled, y_performance)
    
    # Save models
    joblib.dump(hiring_model, 'hiring_success_model.pkl')
    joblib.dump(performance_model, 'performance_prediction_model.pkl')
```

### Ranking Engine

Real-time candidate ranking and tier classification system.

#### Tier System
- **A+**: Score ≥90, Percentile ≥95
- **A**: Score ≥85, Percentile ≥85  
- **A-**: Score ≥80, Percentile ≥75
- **B+**: Score ≥75, Percentile ≥60
- **B**: Score ≥70, Percentile ≥40
- **B-**: Score ≥65, Percentile ≥25
- **C**: Below B- thresholds

#### Ranking Updates
```python
async def update_candidate_ranking(evaluation: InterviewEvaluation):
    # Store evaluation results
    await store_evaluation_results(evaluation)
    
    # Recalculate all rankings
    await recalculate_all_rankings()
    
    # Update Redis cache for live leaderboard
    await update_redis_cache()
    
    # Trigger ML model updates if needed
    await check_retrain_trigger()
```

---

## Frontend Implementation

### Main Interface (`templates/index.html`)

The main dashboard provides:
- Character selection dropdown
- Model provider selection (OpenAI, Ollama, xAI, Anthropic)
- TTS provider selection (OpenAI, ElevenLabs, XTTS, Kokoro)
- Voice and speed controls
- Conversation controls (Start, Stop, Clear)
- Real-time message display
- Voice animation indicators

### Enhanced Interface (`templates/enhanced.html`)

Advanced features interface with:
- Emotional TTS controls
- Voice instruction customization
- Advanced model selection
- Real-time conversation management
- Character-specific settings

### WebRTC Interface (`templates/webrtc_realtime.html`)

Direct OpenAI Realtime API integration:
- WebRTC connection management
- Real-time audio streaming
- Character context integration
- Low-latency conversation handling

### JavaScript Components

#### Main Script (`static/js/scripts.js`)
- WebSocket connection management
- Audio recording and playback
- UI state management
- Settings synchronization

#### Enhanced Script (`static/js/enhanced.js`)
- Enhanced conversation management
- Emotional TTS controls
- Advanced audio handling
- Real-time status updates

#### WebRTC Script (`static/js/webrtc_realtime.js`)
- WebRTC connection setup
- OpenAI Realtime API integration
- Audio stream handling
- Character context management

### CSS Styling (`static/css/styles.css`)

Responsive design with:
- Dark/light theme support
- Mobile-responsive layout
- Voice animation effects
- Modern UI components
- Accessibility features

---

## Deployment

### Production Deployment

#### Docker Compose Setup
```yaml
version: '3.8'
services:
  voice-chat-ai:
    image: bigsk1/voice-chat-ai:latest
    container_name: voice-chat-ai
    env_file: .env
    ports:
      - "8000:8000"
    volumes:
      - ./elevenlabs_voices.json:/app/elevenlabs_voices.json
      - ./interview-outputs:/app/interview-outputs
    depends_on:
      - postgres
      - redis
    restart: unless-stopped

  postgres:
    image: postgres:15
    container_name: postgres-interview
    environment:
      POSTGRES_DB: interview_bot
      POSTGRES_USER: interview_admin
      POSTGRES_PASSWORD: secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./database/schema.sql:/docker-entrypoint-initdb.d/schema.sql
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    container_name: redis-interview
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  elasticsearch:
    image: elasticsearch:8.11.0
    container_name: elasticsearch-interview
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    ports:
      - "9200:9200"
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data

volumes:
  postgres_data:
  redis_data:
  elasticsearch_data:
```

#### Nginx Configuration
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Monitoring Setup

#### Prometheus Configuration
```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'voice-chat-ai'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: /metrics
```

#### Health Checks
```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "components": {
            "database": await check_database_health(),
            "redis": await check_redis_health(),
            "elasticsearch": await check_elasticsearch_health()
        }
    }
```

---

## Troubleshooting

### Common Issues

#### Audio Issues

**Problem**: `OSError: [Errno -9999] Unanticipated host error`
**Solution**: 
- Install FFmpeg: `winget install ffmpeg` (Windows)
- Check microphone permissions
- Set microphone as default device
- Restart application

**Problem**: `OSError: [Errno -9996] Invalid input device`
**Solution**:
- Check PulseAudio configuration (Linux)
- Verify Docker volume mapping for audio
- Install required audio packages:
```bash
sudo apt-get install -y gcc python3-dev portaudio19-dev pulseaudio
```

#### CUDA/GPU Issues

**Problem**: `Could not locate cudnn_ops64_9.dll`
**Solutions**:
1. Disable cuDNN in config:
```json
// ~/.cache/tts/tts_models--multilingual--multi-dataset--xtts_v2/config.json
{"cudnn_enable": false}
```

2. Install cuDNN and add to PATH:
```bash
# Add to PATH
C:\Program Files\NVIDIA\CUDNN\v9.5\bin\12.6
```

#### Python Environment Issues

**Problem**: Import errors or missing dependencies
**Solution**:
```bash
# For Conda environments with libstdc++ issues
conda remove libstdcxx-ng --force

# For PyAudio compilation issues
sudo apt-get install -y gcc python3-dev portaudio19-dev libstdc++6
```

#### Database Connection Issues

**Problem**: Cannot connect to PostgreSQL/Redis
**Solutions**:
1. Check connection strings in `.env`
2. Verify services are running:
```bash
docker ps
systemctl status postgresql redis
```
3. Check firewall settings
4. Verify credentials and permissions

#### API Key Issues

**Problem**: Authentication errors with AI providers
**Solutions**:
1. Verify API keys in `.env` file
2. Check API key permissions and quotas
3. Test API keys with curl:
```bash
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
     https://api.openai.com/v1/models
```

### Performance Optimization

#### Database Optimization
```sql
-- Add indexes for better query performance
CREATE INDEX CONCURRENTLY idx_interview_sessions_completed 
ON interview_sessions(completed_at) WHERE session_status = 'completed';

CREATE INDEX CONCURRENTLY idx_question_responses_final_score 
ON question_responses(final_question_score DESC);

-- Analyze tables for query planning
ANALYZE candidates, interview_sessions, question_responses;
```

#### Redis Optimization
```bash
# Increase memory limit
redis-cli CONFIG SET maxmemory 1gb
redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

#### Application Optimization
```python
# Use connection pooling
import asyncpg

async def create_db_pool():
    return await asyncpg.create_pool(
        DATABASE_URL,
        min_size=5,
        max_size=20,
        command_timeout=60
    )

# Implement caching
from functools import lru_cache

@lru_cache(maxsize=128)
def get_character_prompt(character_name: str):
    return load_character_prompt(character_name)
```

### Logging and Debugging

#### Enable Debug Mode
```bash
# In .env file
DEBUG=true
DEBUG_AUDIO_LEVELS=true
```

#### Logging Configuration
```python
import logging

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('voice_chat_ai.log'),
        logging.StreamHandler()
    ]
)
```

#### Monitor Resource Usage
```bash
# Monitor system resources
htop
nvidia-smi  # For GPU usage
docker stats  # For container resources
```

---

## Conclusion

This documentation provides a comprehensive guide to understanding, implementing, and deploying the Voice Chat AI system. The modular architecture allows for easy customization and extension, while the detailed configuration options enable adaptation to various use cases.

Key implementation points:
1. **Modular Design**: Each component can be developed and deployed independently
2. **Multi-Provider Support**: Flexible integration with various AI and TTS services
3. **Scalable Architecture**: Database-backed with caching for performance
4. **Enhanced Features**: Advanced ML/RAG capabilities for specialized use cases
5. **Production Ready**: Docker deployment with monitoring and health checks

For any LLM attempting to replicate this functionality, focus on:
1. Understanding the conversation flow and state management
2. Implementing proper audio handling and WebSocket communication
3. Integrating multiple AI providers with consistent interfaces
4. Building the character system with mood-based responses
5. Adding the enhanced features incrementally based on requirements

The system is designed to be both powerful for advanced use cases and simple enough for basic voice chat functionality.
