# Voice Chat AI Integration Test Guide

## Pre-requisites

1. **Voice Chat AI Backend Running**
   - Navigate to `../voice-chat-ai/`
   - Install dependencies: `pip install -r requirements.txt`
   - Set environment variables (OpenAI API key)
   - Start server: `python app/main.py`
   - Verify server is running on `http://localhost:8000`

2. **Frontend Environment**
   - Create `.env.local` with voice-chat-ai configuration
   - Install dependencies: `npm install`
   - Start frontend: `npm run dev`

## Test Checklist

### ✅ Backend Connection Test
- [ ] Backend server starts without errors
- [ ] WebSocket endpoint accessible at `ws://localhost:8000/ws`
- [ ] API responds to health checks

### ✅ Frontend Integration Test
- [ ] Frontend loads without console errors
- [ ] Environment variables loaded correctly
- [ ] WebSocket connection established
- [ ] Audio permissions requested and granted

### ✅ Interview Flow Test
- [ ] Application form submission works
- [ ] Device setup completes successfully
- [ ] Interview starts and WebSocket connects
- [ ] Audio streaming begins (check browser dev tools)
- [ ] AI responds with interview questions
- [ ] Transcription appears in real-time
- [ ] Interview progresses through multiple questions
- [ ] Interview completion and navigation to thank you page

### ✅ Audio Quality Test
- [ ] Microphone input detected
- [ ] Audio chunks sent to backend (check network tab)
- [ ] Transcription accuracy acceptable
- [ ] AI speech synthesis works
- [ ] No audio feedback or echo

### ✅ Error Handling Test
- [ ] Connection retry on WebSocket failure
- [ ] Graceful handling of microphone permission denial
- [ ] Error messages displayed appropriately
- [ ] Recovery from temporary network issues

## Debug Information

### WebSocket Messages
Monitor these message types in browser console:
- `config` - Initial configuration sent to backend
- `start_conversation` - Interview initiation
- `ai_response` - AI questions and responses
- `transcription` - Real-time speech-to-text
- `conversation_ended` - Interview completion

### Audio Configuration
Verify these settings match voice-chat-ai backend:
- Sample Rate: 16000 Hz
- Chunk Size: 1024 samples
- Channels: 1 (mono)
- Format: Int16Array

### Common Issues

1. **WebSocket Connection Failed**
   - Check backend is running on port 8000
   - Verify no firewall blocking connections
   - Check browser console for CORS errors

2. **No Audio Streaming**
   - Verify microphone permissions granted
   - Check audio context initialization
   - Monitor network tab for binary WebSocket messages

3. **No AI Responses**
   - Verify OpenAI API key is set in backend
   - Check backend logs for API errors
   - Ensure character configuration is correct

4. **Transcription Issues**
   - Check audio quality and background noise
   - Verify proper audio format conversion
   - Monitor backend logs for transcription errors

## Success Criteria

The integration is successful when:
1. ✅ User can complete full interview flow
2. ✅ Audio is captured and streamed correctly
3. ✅ AI responds with relevant interview questions
4. ✅ Transcription is accurate and real-time
5. ✅ Interview completes and navigates properly
6. ✅ No critical errors in console or backend logs
