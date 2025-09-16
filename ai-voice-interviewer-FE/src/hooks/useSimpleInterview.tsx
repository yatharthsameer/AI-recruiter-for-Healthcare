import { useState, useRef, useCallback, useEffect } from 'react';
import { useToast } from '@/hooks/use-toast';

export interface UserData {
  firstName: string;
  lastName: string;
  email: string;
  phone: string;
  position: string;
  // Enhanced application data
  hhaExperience: boolean;
  cprCertified: boolean;
  driversLicense: boolean;
  autoInsurance: boolean;
  reliableTransport: boolean;
  locationPref?: string;
  availability: string[];
  weeklyHours: number;
}

export type InterviewState = 'connecting' | 'ready' | 'interviewing' | 'listening' | 'speaking' | 'completed' | 'error';

export function useSimpleInterview(navigate?: (path: string) => void) {
  const [state, setState] = useState<InterviewState>('connecting');
  const [sessionId, setSessionId] = useState<string>('');
  const [currentQuestion, setCurrentQuestion] = useState<string>('');
  const [questionNumber, setQuestionNumber] = useState<number>(0);
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [isRecording, setIsRecording] = useState<boolean>(false);
  
  const wsRef = useRef<WebSocket | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const questionNumberRef = useRef<number>(0);
  const isRecordingRef = useRef<boolean>(false);
  const { toast } = useToast();
  
  // Updated to use Python backend WebSocket endpoint (configurable). Default to IPv4 to avoid ::1 issues.
  const WS_BASE: string = (import.meta.env.VITE_WS_BASE_URL as string | undefined) ?? 'ws://127.0.0.1:3000';
  const WS_URL = `${WS_BASE.replace(/\/$/, '')}/ws/audio`;
  
  // Audio configuration (must match Python backend)
  const SAMPLE_RATE = 16000;
  const CHUNK_MS = 20;
  const FRAME_BYTES = 640;

  // Audio streaming setup
  const startAudioRecording = useCallback(async () => {
    try {
      console.log('🎤 Starting audio recording...');
      
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: SAMPLE_RATE,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          // Additional constraints to reduce feedback
          googEchoCancellation: true,
          googAutoGainControl: true,
          googNoiseSuppression: true,
          googHighpassFilter: true,
          googTypingNoiseDetection: true
        }
      });
      
      // Create audio context for processing
      audioContextRef.current = new AudioContext({ sampleRate: SAMPLE_RATE });
      const source = audioContextRef.current.createMediaStreamSource(stream);
      
      // Create script processor for real-time audio processing
      const processor = audioContextRef.current.createScriptProcessor(4096, 1, 1);
      
      processor.onaudioprocess = (event) => {
        if (!isRecordingRef.current || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
        
        const inputBuffer = event.inputBuffer.getChannelData(0);
        
        // Convert to Int16 and send in 640-byte frames
        const int16Buffer = new Int16Array(inputBuffer.length);
        for (let i = 0; i < inputBuffer.length; i++) {
          int16Buffer[i] = Math.max(-32768, Math.min(32767, inputBuffer[i] * 32768));
        }
        
        // Send in 320-sample (640-byte) chunks
        const samplesPerFrame = FRAME_BYTES / 2; // 320 samples
        for (let i = 0; i < int16Buffer.length; i += samplesPerFrame) {
          const frame = int16Buffer.slice(i, i + samplesPerFrame);
          if (frame.length === samplesPerFrame) {
            wsRef.current?.send(frame.buffer);
            console.log(`📤 Sent audio frame: ${frame.length} samples (${frame.buffer.byteLength} bytes)`);
          }
        }
      };
      
      source.connect(processor);
      processor.connect(audioContextRef.current.destination);
      
      // Set both state and ref
      isRecordingRef.current = true;
      setIsRecording(true);
      console.log('✅ Audio recording started');
      
    } catch (error) {
      console.error('❌ Failed to start audio recording:', error);
      toast({
        title: 'Microphone Error',
        description: 'Failed to access microphone. Please check permissions.',
        variant: 'destructive'
      });
    }
  }, [isRecording, toast]);
  
  const stopAudioRecording = useCallback(() => {
    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }
    
    // Set both state and ref
    isRecordingRef.current = false;
    setIsRecording(false);
    console.log('⏹️ Audio recording stopped');
  }, []);

  const connect = useCallback(() => {
    console.log('🔗 Connecting to WebSocket...');
    setState('connecting');
    
    try {
      wsRef.current = new WebSocket(WS_URL);
      
      wsRef.current.onopen = () => {
        console.log('✅ WebSocket connected');
        setIsConnected(true);
        setState('ready');
      };
      
      wsRef.current.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          handleMessage(message);
        } catch (error) {
          console.error('❌ Message parse error:', error);
        }
      };
      
      wsRef.current.onclose = () => {
        console.log('🔌 WebSocket disconnected');
        setIsConnected(false);
        setState('error');
      };
      
      wsRef.current.onerror = (error) => {
        console.error('❌ WebSocket error:', error);
        setState('error');
      };
      
    } catch (error) {
      console.error('❌ WebSocket connection failed:', error);
      setState('error');
    }
  }, []);

  const handleMessage = useCallback((message: any) => {
    console.log('📨 Received message:', message.type);
    
    switch (message.type) {
      case 'connection':
        setSessionId(message.session_id);
        console.log('🔗 Connected to Python backend:', message.session_id);
        break;
        
      case 'interview_started':
        setCurrentQuestion(message.question);
        setQuestionNumber(message.questionNumber);
        questionNumberRef.current = message.questionNumber;
        setState('speaking');
        speakQuestion(message.question);
        break;
        
      case 'response_analyzed':
        setCurrentQuestion(message.nextQuestion);
        setQuestionNumber(message.questionNumber);
        questionNumberRef.current = message.questionNumber;
        setState('speaking');
        speakQuestion(message.nextQuestion);
        break;
        
      case 'voice_activity':
        console.log('🗣️ Voice activity:', message.speaking ? 'Speaking' : 'Silent');
        break;
        
      case 'transcript':
        if (message.final && message.text) {
          console.log('📝 Final transcript:', message.text);
          // Transcript is automatically processed by backend for interview flow
        }
        break;
        
      case 'interview_completed':
        setState('completed');
        toast({
          title: 'Interview Complete',
          description: message.message || "Thank you for completing the interview!",
          duration: 5000
        });
        // Navigate to thank you page after a brief delay
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
        
      case 'pong':
        console.log('🏓 Pong received');
        break;
    }
  }, [toast, navigate]);

  const startInterview = useCallback((userData: UserData, interviewType = 'general') => {
    if (!wsRef.current || !isConnected) {
      console.warn('⚠️ WebSocket not ready');
      return;
    }
    
    console.log('🎬 Starting interview...');
    setState('interviewing');
    
    // Send interview start message to Python backend
    wsRef.current.send(JSON.stringify({
      type: 'start_interview',
      data: { userData, interviewType }
    }));
    
    // Start audio recording for continuous transcription
    startAudioRecording();
  }, [isConnected]);

  const sendResponse = useCallback((response: string) => {
    if (!wsRef.current || !response.trim()) return;
    
    console.log('📤 Sending response:', response);
    
    wsRef.current.send(JSON.stringify({
      type: 'user_response',
      data: {
        response: response.trim(),
        questionNumber: questionNumberRef.current
      }
    }));
  }, []);

  const startListening = useCallback(() => {
    // Audio is continuously streaming, so just update UI state
    console.log('👂 Listening for response...');
    setState('listening');
  }, []);

  const speakQuestion = useCallback((text: string) => {
    console.log('🔊 Speaking:', text);
    
    // Temporarily stop audio recording during AI speech
    isRecordingRef.current = false;
    console.log('🔇 Muting microphone during AI speech');
    
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 0.9;
    utterance.pitch = 1.0;
    utterance.volume = 0.8; // Slightly lower volume to reduce feedback
    
    utterance.onend = () => {
      console.log('🔊 Speech ended, starting to listen...');
      setTimeout(() => {
        // Resume audio recording after AI finishes speaking
        isRecordingRef.current = true;
        console.log('🎤 Unmuting microphone for user response');
        startListening();
      }, 1000); // Longer delay to ensure AI speech is completely finished
    };
    
    utterance.onerror = () => {
      console.error('❌ Speech synthesis error');
      // Resume recording even if speech fails
      isRecordingRef.current = true;
      startListening();
    };
    
    speechSynthesis.speak(utterance);
  }, [startListening]);

  const endInterview = useCallback(() => {
    if (!wsRef.current || !sessionId) return;
    
    console.log('🛑 Ending interview...');
    
    wsRef.current.send(JSON.stringify({
      type: 'end_interview',
      data: { sessionId }
    }));
  }, [sessionId]);

  const disconnect = useCallback(() => {
    console.log('🔌 Disconnecting...');
    
    // Stop audio recording
    stopAudioRecording();
    
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    
    speechSynthesis.cancel();
    setIsConnected(false);
    setState('connecting');
  }, [stopAudioRecording]);

  return {
    state,
    sessionId,
    currentQuestion,
    questionNumber,
    isConnected,
    isRecording,
    connect,
    startInterview,
    endInterview,
    disconnect,
    startListening,
    startAudioRecording,
    stopAudioRecording
  };
}

// Extend Window interface for speech recognition
declare global {
  interface Window {
    SpeechRecognition?: any;
    webkitSpeechRecognition?: any;
  }
}
