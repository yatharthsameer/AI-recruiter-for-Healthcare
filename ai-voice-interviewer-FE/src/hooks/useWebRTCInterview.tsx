import { useState, useRef, useCallback, useEffect } from 'react';
import { useToast } from '@/hooks/use-toast';

export interface UserData {
  firstName: string;
  lastName: string;
  email: string;
  phone: string;
  // Caregiving experience
  caregivingExperience: boolean;
  // PER ID questions
  hasPerId: boolean;
  perId?: string;
  ssn?: string;
  // License and insurance
  driversLicense: boolean;
  autoInsurance: boolean;
  // Availability and hours
  availability: string[];
  weeklyHours: number;
  // Languages (optional)
  languages?: string[];
}

export type InterviewState = 
  | 'idle'
  | 'connecting' 
  | 'ready' 
  | 'active'
  | 'speaking'
  | 'listening'
  | 'processing'
  | 'completed' 
  | 'error';

interface WebRTCMessage {
  type: string;
  [key: string]: any;
}

export function useWebRTCInterview(navigate?: (path: string) => void) {
  // State management
  const [state, setState] = useState<InterviewState>('idle');
  const [isSessionActive, setIsSessionActive] = useState(false);
  const [currentQuestion, setCurrentQuestion] = useState('');
  const [questionNumber, setQuestionNumber] = useState(0);
  const [transcript, setTranscript] = useState<Array<{type: 'user' | 'ai' | 'system' | 'error', message: string, timestamp: string}>>([]);
  const [sessionId, setSessionId] = useState<string>('');
  const [isMicrophoneEnabled, setIsMicrophoneEnabled] = useState(false);
  
  // WebRTC refs
  const peerConnectionRef = useRef<RTCPeerConnection | null>(null);
  const dataChannelRef = useRef<RTCDataChannel | null>(null);
  const micStreamRef = useRef<MediaStream | null>(null);
  const audioPlayerRef = useRef<HTMLAudioElement | null>(null);
  const ephemeralKeyRef = useRef<string | null>(null);
  
  // Audio recording refs
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const audioContextRef = useRef<AudioContext | null>(null);
  const mixerRef = useRef<MediaStreamAudioDestinationNode | null>(null);
  
  // Configuration
  const BACKEND_URL = 'http://localhost:8000';
  const INTERVIEWER_CHARACTER = 'carebot'; // Professional healthcare interviewer character
  const INTERVIEWER_VOICE = 'alloy'; // Professional female voice (same as chatgpt)
  const { toast } = useToast();

  // Initialize audio player
  useEffect(() => {
    audioPlayerRef.current = new Audio();
    audioPlayerRef.current.autoplay = true;
    
    return () => {
      if (audioPlayerRef.current) {
        audioPlayerRef.current.pause();
        audioPlayerRef.current.srcObject = null;
      }
    };
  }, []);

  // Add transcript message
  const addTranscriptMessage = useCallback((message: string, type: 'user' | 'ai' | 'system' | 'error') => {
    const timestamp = new Date().toISOString();
    setTranscript(prev => [...prev, { type, message, timestamp }]);
    
    // Update current question if it's an AI message
    if (type === 'ai') {
      setCurrentQuestion(message);
      setQuestionNumber(prev => prev + 1);
    }
  }, []);

  // Setup audio recording
  const setupAudioRecording = useCallback(async (micStream: MediaStream) => {
    try {
      console.log('🎙️ Setting up audio recording...');
      
      // Create audio context for mixing
      const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
      audioContextRef.current = audioContext;
      
      // Create destination for mixed audio
      const mixer = audioContext.createMediaStreamDestination();
      mixerRef.current = mixer;
      
      // Add microphone audio to mixer
      const micSource = audioContext.createMediaStreamSource(micStream);
      micSource.connect(mixer);
      
      console.log('✅ Microphone audio added to mixer');
      
      // Setup MediaRecorder with the mixed stream (initially just microphone)
      const mediaRecorder = new MediaRecorder(mixer.stream, {
        mimeType: 'audio/webm;codecs=opus'
      });
      
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];
      
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };
      
      mediaRecorder.onstop = () => {
        console.log('🎙️ Audio recording stopped');
      };
      
      console.log('✅ Audio recording setup complete (microphone ready, waiting for AI audio)');
      return true;
      
    } catch (error) {
      console.error('❌ Error setting up audio recording:', error);
      addTranscriptMessage('Failed to setup audio recording', 'error');
      return false;
    }
  }, [addTranscriptMessage]);

  // Add AI audio stream to the recording mixer
  const addAIAudioToRecording = useCallback((aiStream: MediaStream) => {
    try {
      if (!audioContextRef.current || !mixerRef.current) {
        console.warn('⚠️ Audio context or mixer not available for AI audio');
        return;
      }

      console.log('🤖 Adding AI audio to recording mixer...');
      
      // Create source from AI audio stream and connect to mixer
      const aiSource = audioContextRef.current.createMediaStreamSource(aiStream);
      aiSource.connect(mixerRef.current);
      
      console.log('✅ AI audio added to recording mixer');
      addTranscriptMessage('AI audio recording enabled', 'system');
      
    } catch (error) {
      console.error('❌ Error adding AI audio to recording:', error);
      addTranscriptMessage('Failed to add AI audio to recording', 'error');
    }
  }, [addTranscriptMessage]);

  // Start audio recording
  const startAudioRecording = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'inactive') {
      try {
        mediaRecorderRef.current.start(1000); // Record in 1-second chunks
        console.log('🎙️ Audio recording started');
        addTranscriptMessage('Audio recording started', 'system');
      } catch (error) {
        console.error('❌ Error starting audio recording:', error);
        addTranscriptMessage('Failed to start audio recording', 'error');
      }
    }
  }, [addTranscriptMessage]);

  // Stop audio recording
  const stopAudioRecording = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop();
      console.log('🎙️ Audio recording stopped');
      addTranscriptMessage('Audio recording stopped', 'system');
    }
  }, [addTranscriptMessage]);

  // Save audio recording
  const saveAudioRecording = useCallback(async (userData: UserData) => {
    try {
      if (audioChunksRef.current.length === 0) {
        console.warn('⚠️ No audio chunks to save');
        return null;
      }

      console.log('💾 Saving audio recording...');
      
      // Create audio blob
      const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
      
      // Create FormData for upload
      const formData = new FormData();
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      const candidateName = `${userData.firstName}_${userData.lastName}`.replace(/[^a-zA-Z0-9_]/g, '');
      const filename = `Interview_${candidateName}_${timestamp}.webm`;
      
      formData.append('audio', audioBlob, filename);
      formData.append('userData', JSON.stringify(userData));
      formData.append('sessionId', sessionId);
      
      // Upload to backend
      const response = await fetch(`${BACKEND_URL}/save_interview_audio`, {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      
      if (result.status === 'success') {
        console.log('✅ Audio recording saved:', result.filename);
        addTranscriptMessage(`Audio recording saved: ${result.filename}`, 'system');
        
        toast({
          title: "Audio Saved",
          description: `Interview audio saved as ${result.filename}`,
        });
        
        return result.filename;
      } else {
        throw new Error(result.message || 'Failed to save audio');
      }

    } catch (error) {
      console.error('❌ Error saving audio recording:', error);
      addTranscriptMessage('Failed to save audio recording', 'error');
      
      toast({
        title: "Audio Save Error",
        description: "Failed to save audio recording. Please contact support.",
        variant: "destructive",
      });
      
      return null;
    }
  }, [addTranscriptMessage, sessionId, toast]);

  // Evaluate interview with ChatGPT (internal use only)
  const evaluateInterview = useCallback(async (transcript: Array<{type: 'user' | 'ai' | 'system' | 'error', message: string, timestamp: string}>, userData: UserData) => {
    try {
      console.log('🤖 Starting internal interview evaluation...');
      
      const response = await fetch(`${BACKEND_URL}/evaluate_interview`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          transcript: transcript,
          userData: userData,
          sessionId: sessionId
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      
      if (result.status === 'success') {
        console.log('✅ Internal evaluation completed successfully');
        addTranscriptMessage('Interview evaluation completed (internal)', 'system');
        return result.evaluation;
      } else {
        throw new Error(result.message || 'Failed to evaluate interview');
      }

    } catch (error) {
      console.error('❌ Error in internal evaluation:', error);
      // Silent failure - don't notify user about evaluation issues
      addTranscriptMessage('Evaluation processing in background', 'system');
      return null;
    }
  }, [addTranscriptMessage, sessionId, toast]);
  
  // Get ephemeral key from backend
  const getEphemeralKey = useCallback(async (): Promise<string> => {
    console.log('🔑 Fetching ephemeral key...');
    
    const response = await fetch(`${BACKEND_URL}/openai_ephemeral_key`);
    if (!response.ok) {
      throw new Error(`Failed to get ephemeral key: ${response.status} - ${response.statusText}`);
    }
    
    const data = await response.json();
    const ephemeralKey = data.client_secret?.value;
    
    if (!ephemeralKey) {
      throw new Error('Invalid ephemeral key received from server');
    }
    
    console.log('✅ Received ephemeral key');
    return ephemeralKey;
  }, []);

  // Setup microphone
  const setupMicrophone = useCallback(async (): Promise<boolean> => {
    try {
      console.log('🎤 Setting up microphone...');
      
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        }
      });
      
      micStreamRef.current = stream;
      
      // Add audio track to peer connection
      if (peerConnectionRef.current) {
        const audioTrack = stream.getAudioTracks()[0];
        // Start with microphone enabled by default
        audioTrack.enabled = true;
        setIsMicrophoneEnabled(true);
        peerConnectionRef.current.addTrack(audioTrack, stream);
        console.log('✅ Audio track added to peer connection (microphone enabled)');
      }
      
      // Setup audio recording with microphone stream
      await setupAudioRecording(stream);
      
      return true;
    } catch (error) {
      console.error('❌ Error accessing microphone:', error);
      addTranscriptMessage(`Microphone error: ${(error as Error).message}`, 'error');
      return false;
    }
  }, [addTranscriptMessage]);

  // Setup data channel for communication
  const setupDataChannel = useCallback((dataChannel: RTCDataChannel) => {
    dataChannel.onopen = () => {
      console.log('📡 Data channel opened');
      
      // Set voice preference
      const voiceMessage = {
        event_id: `event_${Date.now()}`,
        type: "session.update",
        session: {
          voice: INTERVIEWER_VOICE
        }
      };
      dataChannel.send(JSON.stringify(voiceMessage));
      
      // Fetch and send character instructions
      fetchCharacterInstructions()
        .then(instructions => {
          const instructionsMessage = {
            type: "session.update",
            session: {
              instructions: instructions,
              input_audio_transcription: {
                model: "whisper-1"
              },
              turn_detection: {
                type: "server_vad",
                threshold: 0.5,
                prefix_padding_ms: 300,
                silence_duration_ms: 500
              }
            }
          };
          dataChannel.send(JSON.stringify(instructionsMessage));
          console.log('✅ Character instructions sent');
        })
        .catch(error => {
          console.error('❌ Error fetching character instructions:', error);
          // Use fallback instructions
          const fallbackInstructions = createInterviewerInstructions();
          const instructionsMessage = {
            type: "session.update",
            session: {
              instructions: fallbackInstructions,
              input_audio_transcription: {
                model: "whisper-1"
              },
              turn_detection: {
                type: "server_vad",
                threshold: 0.5,
                prefix_padding_ms: 300,
                silence_duration_ms: 500
              }
            }
          };
          dataChannel.send(JSON.stringify(instructionsMessage));
        });
    };

    dataChannel.onmessage = (event) => {
      try {
        const data: WebRTCMessage = JSON.parse(event.data);
        handleWebRTCMessage(data);
      } catch (error) {
        console.error('❌ Error parsing WebRTC message:', error);
      }
    };

    dataChannel.onerror = (error) => {
      console.error('❌ Data channel error:', error);
      addTranscriptMessage('Communication error occurred', 'error');
    };

    dataChannel.onclose = () => {
      console.log('📡 Data channel closed');
    };
  }, [addTranscriptMessage]);

  // Handle WebRTC messages from OpenAI
  const handleWebRTCMessage = useCallback((data: WebRTCMessage) => {
    const messageType = data.type;
    
    // Only log important messages to reduce console noise
    const importantMessages = [
      'conversation.item.created',
      'input_audio_buffer.speech_started',
      'input_audio_buffer.speech_stopped',
      'response.audio.done',
      'error',
      'session.updated'
    ];
    
    if (importantMessages.includes(data.type)) {
      console.log('📨 Received message:', data.type);
    }
    
    switch (data.type) {
      case "conversation.item.created":
        // New conversation item
        if (data.item?.type === 'message' && data.item?.role === 'assistant') {
          setState('processing');
        }
        break;
        
      case "conversation.item.input_audio_transcription.completed":
        // User speech transcribed
        const userText = data.transcript || '';
        if (userText.trim()) {
          console.log('👤 User said:', userText);
          addTranscriptMessage(userText, 'user');
          setState('processing');
        }
        break;
        
      case "input_audio_buffer.transcription.completed":
        // User input transcription completed
        const transcribedText = data.transcript || '';
        if (transcribedText.trim()) {
          console.log('👤 User transcription:', transcribedText);
          addTranscriptMessage(transcribedText, 'user');
          setState('processing');
        }
        break;
        
      case "conversation.item.created":
        // Item created - check if it's user input
        if (data.item?.type === 'message' && data.item?.role === 'user') {
          const userContent = data.item?.content?.[0]?.transcript || data.item?.content?.[0]?.text || '';
          if (userContent.trim()) {
            console.log('👤 User input (item.created):', userContent);
            addTranscriptMessage(userContent, 'user');
          }
        }
        break;
        
      case "conversation.item.input_audio_transcription.completed":
        // Another variant of user transcription
        const inputTranscript = data.transcript || '';
        if (inputTranscript.trim()) {
          console.log('👤 User input transcription:', inputTranscript);
          addTranscriptMessage(inputTranscript, 'user');
          setState('processing');
        }
        break;
        
      case "response.audio_transcript.delta":
        // AI speech transcript (incremental)
        // We can collect these to build the full transcript
        break;
        
      case "response.audio_transcript.done":
        // AI speech transcript complete
        const aiTranscript = data.transcript || '';
        if (aiTranscript.trim()) {
          addTranscriptMessage(aiTranscript, 'ai');
        }
        break;
        
      case "conversation.item.text.created":
        // AI text response (fallback)
        const aiText = data.content?.text || '';
        if (aiText.trim()) {
          addTranscriptMessage(aiText, 'ai');
        }
        break;
        
      case "output_audio_buffer.started":
        // AI started speaking
        setState('speaking');
        break;
        
      case "response.audio.done":
      case "output_audio_buffer.stopped":
        // AI finished speaking
        setState('listening');
        break;
        
      case "input_audio_buffer.speech_started":
        // User started speaking
        setState('speaking');
        break;
        
      case "input_audio_buffer.speech_stopped":
        // User stopped speaking
        setState('processing');
        break;
        
      case "input_audio_buffer.committed":
        // User audio committed for processing
        setState('processing');
        break;
        
      case "response.created":
        // AI response being generated
        setState('processing');
        break;
        
      case "response.done":
        // AI response complete
        setState('listening');
        break;
        
      case "session.updated":
        // Session configuration updated
        console.log('✅ Session updated');
        break;
        
      case "error":
        // Error from OpenAI
        const errorMessage = data.error?.message || 'Unknown error';
        console.error('❌ OpenAI error:', errorMessage);
        addTranscriptMessage(`Error: ${errorMessage}`, 'error');
        setState('error');
        break;
        
      // Silently handle common messages that don't need logging
      case "rate_limits.updated":
      case "response.output_item.added":
      case "response.output_item.done":
      case "response.content_part.added":
      case "response.content_part.done":
      case "conversation.item.truncated":
      case "output_audio_buffer.cleared":
        // These are normal operational messages - no action needed
        break;
        
      default:
        // Only log truly unknown message types
        if (!data.type.includes('audio_transcript.delta') && 
            !data.type.includes('audio.delta')) {
          console.log('ℹ️ Unknown message type:', data.type);
        }
    }
  }, [addTranscriptMessage]);

  // Fetch character instructions from backend
  const fetchCharacterInstructions = useCallback(async (): Promise<string> => {
    const response = await fetch(`${BACKEND_URL}/api/character/${INTERVIEWER_CHARACTER}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch character: ${response.status}`);
    }
    
    const data = await response.json();
    if (data.error) {
      throw new Error(data.error);
    }
    
    return data.prompt;
  }, []);

  // Create fallback interviewer instructions
  const createInterviewerInstructions = useCallback((): string => {
    return `You are CareBot, a warm, efficient, voice-first interviewer for healthcare caregiver roles at a clinic.

Your role:
- Conduct a structured 12-minute interview for caregiving positions
- Ask clear, specific questions about caregiving experience and skills
- Be warm, professional, and encouraging while maintaining focus
- Keep responses concise and conversational
- Use micro-affirmations like "Thanks for sharing" and "Got it"
- Guide candidates through the interview efficiently

Start by saying: "Hi [name], I'm CareBot. This takes about 12 minutes. Short examples help. Please avoid private patient details. Ready?"

Then ask structured questions about:
1. Previous caregiving experience
2. Important caregiver traits
3. Relevant life/work experience
4. Motivation for caregiving
5. Punctuality and reliability
6. Experience with seniors
7. Helping others emotionally
8. What coworkers would say about them

Keep responses brief, warm, and professional. This is a voice conversation for healthcare hiring.`;
  }, []);

  // Connect to WebRTC session
  const connect = useCallback(async () => {
    try {
      console.log('🔗 Starting WebRTC connection...');
      setState('connecting');
      
      // Get ephemeral key
      const ephemeralKey = await getEphemeralKey();
      ephemeralKeyRef.current = ephemeralKey;
      
      // Create peer connection
      peerConnectionRef.current = new RTCPeerConnection({
        iceServers: [
          { urls: 'stun:stun.l.google.com:19302' },
          { urls: 'stun:stun1.l.google.com:19302' }
        ]
      });
      
      // Setup audio playback
      peerConnectionRef.current.ontrack = (event) => {
        console.log('🎵 Received audio track from OpenAI:', event.track.kind);
        if (audioPlayerRef.current) {
          audioPlayerRef.current.srcObject = event.streams[0];
          console.log('🔊 AI audio connected to player');
        }
        
        // Add AI audio stream to recording
        if (event.streams[0] && event.track.kind === 'audio') {
          console.log('🎙️ Adding AI audio stream to recording...');
          addAIAudioToRecording(event.streams[0]);
        }
      };
      
      // Setup microphone
      const micSuccess = await setupMicrophone();
      if (!micSuccess) {
        throw new Error('Failed to setup microphone');
      }
      
      // Create data channel
      const dataChannel = peerConnectionRef.current.createDataChannel("oai-events");
      dataChannelRef.current = dataChannel;
      setupDataChannel(dataChannel);
      
      // Create offer
      const offer = await peerConnectionRef.current.createOffer();
      await peerConnectionRef.current.setLocalDescription(offer);
      
      // Wait for ICE gathering
      await new Promise<void>((resolve) => {
        const timeout = setTimeout(resolve, 2000); // 2 second timeout
        
        const checkState = () => {
          if (peerConnectionRef.current?.iceGatheringState === 'complete') {
            clearTimeout(timeout);
            peerConnectionRef.current?.removeEventListener('icegatheringstatechange', checkState);
            resolve();
          }
        };
        
        if (peerConnectionRef.current?.iceGatheringState === 'complete') {
          clearTimeout(timeout);
          resolve();
        } else {
          peerConnectionRef.current?.addEventListener('icegatheringstatechange', checkState);
        }
      });
      
      // Send SDP to proxy
      const sdp = peerConnectionRef.current.localDescription?.sdp;
      if (!sdp) {
        throw new Error('Failed to get SDP');
      }
      
      const response = await fetch(`${BACKEND_URL}/openai_realtime_proxy?model=gpt-4o-realtime-preview-2024-12-17`, {
        method: 'POST',
        body: sdp,
        headers: {
          'Content-Type': 'application/sdp'
        }
      });
      
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Proxy request failed: ${response.status} - ${errorText}`);
      }
      
      // Set remote description
      const answerSdp = await response.text();
      await peerConnectionRef.current.setRemoteDescription({
        type: 'answer',
        sdp: answerSdp
      });
      
      // Update state
      setIsSessionActive(true);
      setState('ready');
      setSessionId(`session_${Date.now()}`);
      
      console.log('✅ WebRTC connection established');
      addTranscriptMessage('Interview session connected. Microphone is ready.', 'system');
      
    } catch (error) {
      console.error('❌ Connection error:', error);
      setState('error');
      addTranscriptMessage(`Connection failed: ${(error as Error).message}`, 'error');
      
      toast({
        title: "Connection Error",
        description: `Failed to connect: ${(error as Error).message}`,
        variant: "destructive",
      });
    }
  }, [getEphemeralKey, setupMicrophone, setupDataChannel, addTranscriptMessage, toast, addAIAudioToRecording]);

  // Start the interview
  const startInterview = useCallback((userData: UserData) => {
    if (!isSessionActive) {
      console.warn('⚠️ Cannot start interview: No active session');
      return;
    }
    
    console.log('🎬 Starting interview...');
    setState('active');
    setQuestionNumber(1);
    
    // Store user data for transcript generation
    try {
      sessionStorage.setItem('interviewUserData', JSON.stringify(userData));
      console.log('💾 User data stored for transcript');
    } catch (error) {
      console.warn('Could not store user data:', error);
    }
    
    // Start audio recording
    startAudioRecording();
    
    // Automatically enable microphone when interview starts
    if (micStreamRef.current) {
      const audioTracks = micStreamRef.current.getAudioTracks();
      if (audioTracks.length > 0) {
        audioTracks[0].enabled = true;
        setIsMicrophoneEnabled(true);
        console.log('🎤 Microphone automatically enabled for interview');
        addTranscriptMessage('Microphone enabled. You can start speaking.', 'system');
      }
    }
    
    addTranscriptMessage('Interview started. Please introduce yourself and share what drew you to caregiving work.', 'system');
    
    // Store user data for context (you might want to send this to the AI)
    console.log('👤 User data:', userData);
    
  }, [isSessionActive, addTranscriptMessage]);

  // Toggle microphone
  const toggleMicrophone = useCallback(() => {
    if (!micStreamRef.current) {
      console.warn('⚠️ No microphone stream available');
      return;
    }
    
    const audioTracks = micStreamRef.current.getAudioTracks();
    if (audioTracks.length > 0) {
      const isEnabled = audioTracks[0].enabled;
      audioTracks[0].enabled = !isEnabled;
      setIsMicrophoneEnabled(!isEnabled);
      
      console.log(`🎤 Microphone ${!isEnabled ? 'enabled' : 'disabled'}`);
      addTranscriptMessage(`Microphone ${!isEnabled ? 'enabled' : 'disabled'}`, 'system');
    }
  }, [addTranscriptMessage]);

  // Save transcript to backend
  const saveTranscriptToBackend = useCallback(async (transcript: Array<{type: 'user' | 'ai' | 'system' | 'error', message: string, timestamp: string}>, userData: UserData) => {
    try {
      console.log('💾 Saving transcript to backend...');
      
      const response = await fetch(`${BACKEND_URL}/save_interview_transcript`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          transcript: transcript,
          userData: userData,
          sessionId: sessionId
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      
      if (result.status === 'success') {
        console.log('✅ Transcript saved successfully:', result.filename);
        addTranscriptMessage(`Interview transcript saved to server: ${result.filename}`, 'system');
        
        toast({
          title: "Interview Complete",
          description: `Transcript saved successfully as ${result.filename}`,
        });
      } else {
        throw new Error(result.message || 'Failed to save transcript');
      }

    } catch (error) {
      console.error('❌ Error saving transcript to backend:', error);
      addTranscriptMessage('Error saving transcript to server', 'error');
      
      toast({
        title: "Save Error",
        description: "Failed to save transcript to server. Please contact support.",
        variant: "destructive",
      });
    }
  }, [addTranscriptMessage, sessionId, toast]);

  // End interview
  const endInterview = useCallback(() => {
    console.log('🛑 Ending interview...');
    setState('completed');
    
    addTranscriptMessage('Interview completed. Thank you for your time!', 'system');
    
    // Stop audio recording
    stopAudioRecording();
    
    // Save transcript to backend
    if (transcript.length > 0) {
      // Get user data from the most recent interview session
      const userData: UserData = {
        firstName: sessionId.includes('_') ? 'Candidate' : 'Unknown',
        lastName: '',
        email: '',
        phone: '',
        caregivingExperience: false,
        hasPerId: false,
        driversLicense: false,
        autoInsurance: false,
        availability: [],
        weeklyHours: 0,
        languages: []
      };
      
      // Try to get user data from transcript or session storage
      try {
        const storedUserData = sessionStorage.getItem('interviewUserData');
        if (storedUserData) {
          Object.assign(userData, JSON.parse(storedUserData));
        }
      } catch (error) {
        console.warn('Could not retrieve user data for transcript');
      }
      
      saveTranscriptToBackend(transcript, userData);
      
      // Save audio recording
      saveAudioRecording(userData);
      
      // Evaluate interview (internal use only - runs in background)
      setTimeout(() => {
        evaluateInterview(transcript, userData);
      }, 2000); // Small delay to ensure transcript is saved first
    }
    
    // Navigate to thank you page after a delay
    setTimeout(() => {
      if (navigate) {
        navigate('/thank-you');
      }
    }, 3000); // Delay to allow transcript download
  }, [navigate, addTranscriptMessage, transcript, sessionId, saveTranscriptToBackend, stopAudioRecording, saveAudioRecording, evaluateInterview]);

  // Disconnect session
  const disconnect = useCallback(() => {
    console.log('🔌 Disconnecting...');
    
    // Close data channel
    if (dataChannelRef.current) {
      dataChannelRef.current.close();
      dataChannelRef.current = null;
    }
    
    // Close peer connection
    if (peerConnectionRef.current) {
      peerConnectionRef.current.close();
      peerConnectionRef.current = null;
    }
    
    // Stop microphone
    if (micStreamRef.current) {
      micStreamRef.current.getTracks().forEach(track => track.stop());
      micStreamRef.current = null;
    }
    
    // Stop audio
    if (audioPlayerRef.current) {
      audioPlayerRef.current.pause();
      audioPlayerRef.current.srcObject = null;
    }
    
    // Stop and cleanup audio recording
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop();
    }
    mediaRecorderRef.current = null;
    audioChunksRef.current = [];
    
    // Close audio context
    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }
    mixerRef.current = null;
    
    // Reset state
    setIsSessionActive(false);
    setIsMicrophoneEnabled(false);
    setState('idle');
    setCurrentQuestion('');
    setQuestionNumber(0);
    setSessionId('');
    
    console.log('✅ Disconnected');
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return {
    // State
    state,
    isSessionActive,
    currentQuestion,
    questionNumber,
    transcript,
    sessionId,
    isMicrophoneEnabled,
    
    // Actions
    connect,
    startInterview,
    endInterview,
    disconnect,
    toggleMicrophone,
    
    // Utilities
    addTranscriptMessage
  };
}
