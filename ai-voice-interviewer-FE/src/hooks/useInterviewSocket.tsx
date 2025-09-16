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
  | 'connecting' 
  | 'ready' 
  | 'interviewing' 
  | 'listening' 
  | 'aiSpeaking'
  | 'sending'
  | 'waitingBackend'
  | 'completed' 
  | 'error';

interface VoiceChatMessage {
  type: string;
  [key: string]: any;
}

export function useInterviewSocket(navigate?: (path: string) => void) {
  const [state, setState] = useState<InterviewState>('connecting');
  const [sessionId, setSessionId] = useState<string>('');
  const [currentQuestion, setCurrentQuestion] = useState<string>('');
  const [questionNumber, setQuestionNumber] = useState<number>(0);
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [isRecording, setIsRecording] = useState<boolean>(false);
  const [transcript, setTranscript] = useState<string>('');
  
  const wsRef = useRef<WebSocket | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const processorRef = useRef<ScriptProcessorNode | null>(null);
  const isRecordingRef = useRef<boolean>(false);
  const { toast } = useToast();
  
  // Voice Chat AI backend configuration
  const WS_URL = import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8000';
  const SAMPLE_RATE = parseInt(import.meta.env.VITE_SAMPLE_RATE) || 16000;
  const CHUNK_SIZE = parseInt(import.meta.env.VITE_CHUNK_SIZE) || 1024;
  
  // Hardcoded character for AI interviewer (using chatgpt for professional interviews)
  const INTERVIEWER_CHARACTER = 'chatgpt';

  const setupAudioCapture = useCallback(async () => {
    try {
      console.log('🎤 Setting up audio capture...');
      
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: SAMPLE_RATE,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        }
      });
      
      mediaStreamRef.current = stream;
      audioContextRef.current = new AudioContext({ sampleRate: SAMPLE_RATE });
      
      const source = audioContextRef.current.createMediaStreamSource(stream);
      const processor = audioContextRef.current.createScriptProcessor(CHUNK_SIZE, 1, 1);
      
      processor.onaudioprocess = (event) => {
        if (!isRecordingRef.current || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
          return;
        }
        
        const inputBuffer = event.inputBuffer.getChannelData(0);
        
        // Convert to Int16Array for voice-chat-ai backend
        const int16Buffer = new Int16Array(inputBuffer.length);
        for (let i = 0; i < inputBuffer.length; i++) {
          int16Buffer[i] = Math.max(-32768, Math.min(32767, inputBuffer[i] * 32768));
        }
        
        // Send audio data as binary
        wsRef.current.send(int16Buffer.buffer);
      };
      
      source.connect(processor);
      processor.connect(audioContextRef.current.destination);
      processorRef.current = processor;
      
      console.log('✅ Audio capture setup complete');
      
    } catch (error) {
      console.error('❌ Failed to setup audio capture:', error);
      toast({
        title: 'Microphone Error',
        description: 'Failed to access microphone. Please check permissions.',
        variant: 'destructive'
      });
    }
  }, [SAMPLE_RATE, CHUNK_SIZE, toast]);

  const startRecording = useCallback(() => {
    if (audioContextRef.current && audioContextRef.current.state === 'suspended') {
      audioContextRef.current.resume();
    }
    isRecordingRef.current = true;
    setIsRecording(true);
    console.log('🎤 Recording started');
  }, []);

  const stopRecording = useCallback(() => {
    isRecordingRef.current = false;
    setIsRecording(false);
    console.log('⏹️ Recording stopped');
  }, []);

  const cleanupAudio = useCallback(() => {
    if (processorRef.current) {
      processorRef.current.disconnect();
      processorRef.current = null;
    }
    
    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }
    
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach(track => track.stop());
      mediaStreamRef.current = null;
    }
    
    isRecordingRef.current = false;
    setIsRecording(false);
  }, []);

  const connect = useCallback(async () => {
    console.log('🔗 Connecting to Voice Chat AI backend...');
    setState('connecting');
    
    try {
      // Note: voice-chat-ai handles audio internally, so we don't need to setup audio capture
      // Connect to WebSocket
      wsRef.current = new WebSocket(`${WS_URL}/ws`);
      
      wsRef.current.onopen = () => {
        console.log('✅ WebSocket connected to Voice Chat AI');
        setIsConnected(true);
        setState('ready');
        
        // Set character for the interview (using chatgpt for professional interviews)
        if (wsRef.current) {
          wsRef.current.send(JSON.stringify({
            action: 'set_character',
            character: INTERVIEWER_CHARACTER
          }));
        }
      };
      
      wsRef.current.onmessage = (event) => {
        try {
          // Handle both text and binary messages
          if (typeof event.data === 'string') {
            const message: VoiceChatMessage = JSON.parse(event.data);
            handleMessage(message);
          } else {
            // Handle binary audio data (TTS response)
            handleAudioResponse(event.data);
          }
        } catch (error) {
          console.error('❌ Message parse error:', error);
        }
      };
      
      wsRef.current.onclose = () => {
        console.log('🔌 WebSocket disconnected');
        setIsConnected(false);
        setState('error');
        cleanupAudio();
      };
      
      wsRef.current.onerror = (error) => {
        console.error('❌ WebSocket error:', error);
        setState('error');
        cleanupAudio();
      };
      
    } catch (error) {
      console.error('❌ Connection failed:', error);
      setState('error');
    }
  }, [setupAudioCapture, cleanupAudio, WS_URL, SAMPLE_RATE, CHUNK_SIZE]);

  const handleMessage = useCallback((message: VoiceChatMessage) => {
    console.log('📨 Received message:', message.type, message);
    
    switch (message.type) {
      case 'session_started':
        setSessionId(message.session_id || '');
        console.log('🔗 Session started:', message.session_id);
        break;
        
      case 'ai_response':
        if (message.text) {
          setCurrentQuestion(message.text);
          setState('aiSpeaking');
          console.log('🤖 AI Response:', message.text);
          
          // If audio is provided, it will be handled separately
          // Otherwise, use text-to-speech
          if (!message.audio) {
            speakText(message.text);
          }
        }
        break;
        
      case 'transcription':
        if (message.text) {
          setTranscript(message.text);
          console.log('📝 Transcription:', message.text);
          
          if (message.is_final) {
            setState('waitingBackend');
            stopRecording();
          }
        }
        break;
        
      case 'conversation_ended':
        setState('completed');
        stopRecording();
        toast({
          title: 'Interview Complete',
          description: message.message || "Thank you for completing the interview!",
          duration: 5000
        });
        
        if (navigate) {
          setTimeout(() => {
            navigate('/thank-you');
          }, 2000);
        }
        break;
        
      case 'error':
        console.error('❌ Server error:', message.message);
        setState('error');
        toast({
          title: 'Interview Error',
          description: message.message,
          variant: 'destructive'
        });
        break;
        
      case 'audio_level':
        // Handle voice activity detection
        console.log('🔊 Audio level:', message.level);
        break;
        
      default:
        console.log('📨 Unknown message type:', message.type);
    }
  }, [toast, navigate, stopRecording]);

  const handleAudioResponse = useCallback((audioData: ArrayBuffer) => {
    console.log('🔊 Received audio response');
    
    // Play the audio response from the AI
    if (audioContextRef.current) {
      audioContextRef.current.decodeAudioData(audioData.slice(0))
        .then(audioBuffer => {
          const source = audioContextRef.current!.createBufferSource();
          source.buffer = audioBuffer;
          source.connect(audioContextRef.current!.destination);
          
          source.onended = () => {
            console.log('🔊 AI speech ended, ready for user input');
            setState('listening');
            startRecording();
          };
          
          source.start();
        })
        .catch(error => {
          console.error('❌ Audio decode error:', error);
          // Fallback to listening state
          setState('listening');
          startRecording();
        });
    }
  }, [startRecording]);

  const speakText = useCallback((text: string) => {
    console.log('🔊 Speaking text:', text);
    
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 0.9;
    utterance.pitch = 1.0;
    utterance.volume = 0.8;
    
    utterance.onend = () => {
      console.log('🔊 Speech ended, ready for user input');
      setState('listening');
      startRecording();
    };
    
    utterance.onerror = () => {
      console.error('❌ Speech synthesis error');
      setState('listening');
      startRecording();
    };
    
    speechSynthesis.speak(utterance);
  }, [startRecording]);

  const startInterview = useCallback((userData: UserData) => {
    if (!wsRef.current || !isConnected) {
      console.warn('⚠️ WebSocket not ready');
      return;
    }
    
    console.log('🎬 Starting interview...');
    setState('interviewing');
    setQuestionNumber(1);
    
    // Start the conversation with voice-chat-ai backend
    wsRef.current.send(JSON.stringify({
      action: 'start',
      character: INTERVIEWER_CHARACTER
    }));
    
    // Note: voice-chat-ai handles audio recording internally
    // For now, we'll work with text input instead of audio streaming
    console.log('🎤 Interview started - voice-chat-ai will handle audio internally');
  }, [isConnected, startRecording]);

  const sendTextMessage = useCallback((text: string) => {
    if (!wsRef.current || !text.trim()) return;
    
    console.log('📤 Sending text message:', text);
    setState('sending');
    
    // For now, we'll simulate the conversation by sending a message
    // The voice-chat-ai backend expects to handle audio internally
    // So we'll need to work with its existing flow
    wsRef.current.send(JSON.stringify({
      action: 'message',
      text: text.trim()
    }));
  }, []);

  const endInterview = useCallback(() => {
    if (!wsRef.current) return;
    
    console.log('🛑 Ending interview...');
    stopRecording();
    
    wsRef.current.send(JSON.stringify({
      action: 'stop'
    }));
  }, [stopRecording]);

  const disconnect = useCallback(() => {
    console.log('🔌 Disconnecting...');
    
    cleanupAudio();
    
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    
    speechSynthesis.cancel();
    setIsConnected(false);
    setState('connecting');
    setTranscript('');
    setCurrentQuestion('');
    setQuestionNumber(0);
  }, [cleanupAudio]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return {
    state,
    sessionId,
    currentQuestion,
    questionNumber,
    isConnected,
    isRecording,
    transcript,
    connect,
    startInterview,
    endInterview,
    disconnect,
    sendTextMessage,
    startRecording,
    stopRecording
  };
}
