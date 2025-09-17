# AI Voice Interviewer

A streamlined setup for an AI-powered interview system.

- Backend: FastAPI in `voice-chat-ai` (serves interviews, transcripts, audio files, and admin APIs)
- Admin Panel: React app in `Admin_Panel` (view interviews, transcript, waveform playback)
- Candidate Frontend (optional): `ai-voice-interviewer-FE`

The old `Server/` folder is no longer used.

## Quick Start

### Prerequisites
- Node.js 18+
- Python 3.10+ (conda optional; commonly `usualenv`)

### 1) Start backend (FastAPI)
```bash
cd voice-chat-ai
# optional if you use conda
conda activate usualenv
pip install -r requirements.txt

# Run FastAPI backend (admin APIs + interview outputs)
python -m app.main
# Server at http://localhost:8000
```

Admin API endpoints:
- `GET /api/interviews` — list completed interviews
- `GET /api/interviews/{sessionId}/transcript` — transcript + audio filename
- `GET /api/interviews/{sessionId}/evaluation` — evaluation details
- `GET /interview-outputs/{filename}` — serve audio/JSON artifacts

Interview artifacts are saved in `voice-chat-ai/interview-outputs/`.

### 2) Start Admin Panel
```bash
cd Admin_Panel
npm install
npm run dev
# http://localhost:5174
```
The Admin Panel expects the backend at `http://localhost:8000`.

### 3) (Optional) Start Candidate Frontend
```bash
cd ai-voice-interviewer-FE
npm install
# Configure frontend to talk to backend
printf "VITE_API_BASE_URL=http://localhost:8000\nVITE_WS_BASE_URL=ws://localhost:8000\n" > .env.local
npm run dev
# http://localhost:5173
```

## Project Structure
```
.
├── Admin_Panel/                # Admin dashboard (React + TS)
├── ai-voice-interviewer-FE/    # Candidate-facing UI (optional)
├── voice-chat-ai/              # FastAPI backend and interview outputs
│   └── interview-outputs/      # Session JSON, audio (.webm), metadata JSON
└── README.md                   # This file
```

## Configuration

Backend env (`voice-chat-ai/.env` example):
```
OPENAI_API_KEY=...
# other provider keys optional depending on your setup
```

Frontend env (`ai-voice-interviewer-FE/.env.local`):
```
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_BASE_URL=ws://localhost:8000
```

## Notes
- Clicking a transcript entry plays from that entry’s timestamp to the next entry; a single highlight region is shown.
- Sentiment UI is removed for a clean transcript display.
- Admin Panel depends on files in `voice-chat-ai/interview-outputs/` and the endpoints above.

## Troubleshooting
- Admin Panel not loading data: ensure backend is running on port 8000 and files exist in `voice-chat-ai/interview-outputs/`.
- Waveform not visible: verify transcript response includes a valid `audio_filename` that exists and is served by `/interview-outputs/{filename}`.

## License
MIT

## Setup Instructions

### Backend: voice-chat-ai (FastAPI)

1) Navigate and create/activate environment
```bash
cd voice-chat-ai

# Option A: conda (recommended if you already use it)
conda activate usualenv  # use your env if different

# Option B: venv
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
```

2) Install dependencies
```bash
pip install -r requirements.txt
```

3) Configure environment (optional unless you run full interview flow)
```bash
cp .env.example .env 2>/dev/null || true
# In .env, set keys as needed, e.g.
# OPENAI_API_KEY=your_key
# ELEVENLABS_API_KEY=your_key
```

4) Start the server
```bash
python -m app.main
# Server runs on http://localhost:8000
```

5) Verify endpoints
```bash
curl http://localhost:8000/api/interviews | jq .
```

Interview artifacts (JSON, .webm, metadata) are read from and written to `voice-chat-ai/interview-outputs/`.

### Interviewer Frontend: ai-voice-interviewer-FE (optional)

1) Navigate and install
```bash
cd ai-voice-interviewer-FE
npm install
```

2) Configure API endpoints
```bash
printf "VITE_API_BASE_URL=http://localhost:8000\nVITE_WS_BASE_URL=ws://localhost:8000\n" > .env.local
```

3) Start dev server
```bash
npm run dev
# App runs on http://localhost:5173
```

### Ports
- Backend (FastAPI): 8000
- Admin Panel: 5174
- Interviewer Frontend (optional): 5173
