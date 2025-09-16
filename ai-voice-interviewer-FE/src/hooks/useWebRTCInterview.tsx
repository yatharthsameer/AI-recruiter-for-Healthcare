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
  const [transcript, setTranscript] = useState<Array<{type: 'user' | 'ai' | 'system' | 'error', message: string}>>([]);
  const [sessionId, setSessionId] = useState<string>('');
  const [isMicrophoneEnabled, setIsMicrophoneEnabled] = useState(false);
  
  // WebRTC refs
  const peerConnectionRef = useRef<RTCPeerConnection | null>(null);
  const dataChannelRef = useRef<RTCDataChannel | null>(null);
  const micStreamRef = useRef<MediaStream | null>(null);
  const audioPlayerRef = useRef<HTMLAudioElement | null>(null);
  const ephemeralKeyRef = useRef<string | null>(null);
  
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
    setTranscript(prev => [...prev, { type, message }]);
    
    // Update current question if it's an AI message
    if (type === 'ai') {
      setCurrentQuestion(message);
      setQuestionNumber(prev => prev + 1);
    }
  }, []);

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
              instructions: instructions
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
              instructions: fallbackInstructions
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
    console.log('📨 Received message:', data.type);
    
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
          addTranscriptMessage(userText, 'user');
          setState('processing');
        }
        break;
        
      case "conversation.item.text.created":
        // AI text response
        const aiText = data.content?.text || '';
        if (aiText.trim()) {
          addTranscriptMessage(aiText, 'ai');
        }
        break;
        
      case "conversation.item.text.delta":
        // Incremental text updates (we can ignore these for now)
        break;
        
      case "response.audio.delta":
        // AI is speaking
        setState('speaking');
        break;
        
      case "response.audio.done":
        // AI finished speaking
        setState('listening');
        break;
        
      case "input_audio_buffer.speech_started":
        // User started speaking
        setState('speaking');
        break;
        
      case "input_audio_buffer.speech_stopped":
        // User stopped speaking
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
        
      default:
        console.log('ℹ️ Unhandled message type:', data.type);
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
        console.log('🎵 Received audio track from OpenAI');
        if (audioPlayerRef.current) {
          audioPlayerRef.current.srcObject = event.streams[0];
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
  }, [getEphemeralKey, setupMicrophone, setupDataChannel, addTranscriptMessage, toast]);

  // Start the interview
  const startInterview = useCallback((userData: UserData) => {
    if (!isSessionActive) {
      console.warn('⚠️ Cannot start interview: No active session');
      return;
    }
    
    console.log('🎬 Starting interview...');
    setState('active');
    setQuestionNumber(1);
    
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

  // End interview
  const endInterview = useCallback(() => {
    console.log('🛑 Ending interview...');
    setState('completed');
    
    addTranscriptMessage('Interview completed. Thank you for your time!', 'system');
    
    // Navigate to results page after a delay
    setTimeout(() => {
      if (navigate) {
        navigate('/results');
      }
    }, 2000);
  }, [navigate, addTranscriptMessage]);

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
