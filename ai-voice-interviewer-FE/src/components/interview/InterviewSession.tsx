import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { Settings, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useToast } from "@/hooks/use-toast";
import { useInterview } from "@/lib/store";
import { useWebRTCInterview } from "@/hooks/useWebRTCInterview";
import { AIAvatar } from "./AIAvatar";
import { SelfView } from "./SelfView";
import { DeviceSettingsModal } from "./DeviceSettingsModal";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";

export function InterviewSession() {
  const { state } = useInterview();
  const navigate = useNavigate();
  const { toast } = useToast();
  const [selectedCameraId, setSelectedCameraId] = useState<string>("");
  const [selectedSpeakerId, setSelectedSpeakerId] = useState<string>("");

  const {
    state: interviewState,
    sessionId,
    currentQuestion,
    questionNumber,
    isSessionActive,
    isMicrophoneEnabled,
    transcript,
    connect,
    startInterview,
    endInterview,
    disconnect,
    toggleMicrophone
  } = useWebRTCInterview();

  // Load saved device preferences
  useEffect(() => {
    const savedCamera = localStorage.getItem("selectedCamera");
    const savedSpeaker = localStorage.getItem("selectedSpeaker");
    
    if (savedCamera) setSelectedCameraId(savedCamera);
    if (savedSpeaker) setSelectedSpeakerId(savedSpeaker);
  }, []);

  // Connect and start interview on mount
  useEffect(() => {
    console.log('InterviewSession: Component mounted, checking application state...');
    
    if (!state.isApplicationComplete || !state.application) {
      console.log('InterviewSession: Application not complete, redirecting...');
      toast({
        title: "Application Required",
        description: "Please complete your application first.",
        variant: "destructive",
      });
      navigate("/");
      return;
    }

    console.log('InterviewSession: Application complete, initializing WebSocket connection...');
    connect();

    return () => {
      console.log('InterviewSession: Cleaning up on unmount...');
      disconnect();
    };
  }, [state.isApplicationComplete, state.application, navigate, toast, connect, disconnect]);

  // Auto-start interview when connected (with small delay to ensure WebRTC session is ready)
  useEffect(() => {
    if (isSessionActive && state.application && interviewState === "ready") {
      const userData = {
        firstName: state.application.firstName || '',
        lastName: state.application.lastName || '',
        email: state.application.email || '',
        phone: state.application.phone || '',
        caregivingExperience: state.application.caregivingExperience || false,
        hasPerId: state.application.hasPerId || false,
        perId: state.application.perId || '',
        ssn: state.application.ssn || '',
        driversLicense: state.application.driversLicense || false,
        autoInsurance: state.application.autoInsurance || false,
        availability: state.application.availability || [],
        weeklyHours: state.application.weeklyHours || 30,
        languages: state.application.languages || []
      };

      // Add small delay to ensure WebRTC session is fully ready
      setTimeout(() => {
        startInterview(userData);
      }, 100);
    }
  }, [isSessionActive, state.application, interviewState, startInterview]);

  // Update speaker device when selection changes
  useEffect(() => {
    if (selectedSpeakerId) {
      // Audio output device setting handled by browser
    }
  }, [selectedSpeakerId]);

  const handleEndInterview = () => {
    endInterview();
    toast({
      title: "Interview Ended",
      description: "Thank you for your time. You'll hear back from us soon.",
    });
    navigate("/");
  };

  const handleCameraChange = (deviceId: string) => {
    setSelectedCameraId(deviceId);
  };

  const handleSpeakerChange = (deviceId: string) => {
    setSelectedSpeakerId(deviceId);
  };

  // Redirect if no application
  if (!state.isApplicationComplete || !state.application) {
    return null;
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo placeholder */}
            <div className="flex items-center">
              <div className="w-8 h-8 bg-brand rounded-lg flex items-center justify-center">
                <span className="text-brand-foreground font-bold text-sm">AI</span>
              </div>
            </div>

            {/* End Interview Button */}
            <AlertDialog>
              <AlertDialogTrigger asChild>
                <Button variant="ghost" size="sm">
                  <X className="w-4 h-4 mr-2" />
                  End Interview
                </Button>
              </AlertDialogTrigger>
              <AlertDialogContent>
                <AlertDialogHeader>
                  <AlertDialogTitle>End Interview?</AlertDialogTitle>
                  <AlertDialogDescription>
                    Are you sure you want to end the interview? This action cannot be undone.
                  </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                  <AlertDialogCancel>Continue</AlertDialogCancel>
                  <AlertDialogAction onClick={handleEndInterview}>
                    End Interview
                  </AlertDialogAction>
                </AlertDialogFooter>
              </AlertDialogContent>
            </AlertDialog>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <motion.div
            className="flex flex-col items-center justify-center min-h-[calc(100vh-12rem)] space-y-8"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5 }}
          >
            {/* Connection Error State */}
            {interviewState === "error" && (
              <motion.div
                className="text-center space-y-4 mb-8"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
              >
                <div className="text-red-400 text-lg font-medium">Connection Error</div>
                <p className="text-muted-foreground max-w-md">
                  Unable to connect to the interview service. Please check your internet connection.
                </p>
                <Button onClick={connect} variant="outline">
                  Retry Connection
                </Button>
              </motion.div>
            )}

            {/* Session Status and Controls */}
            <motion.div
              className="text-center space-y-4"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
            >
              <div className="flex items-center justify-center space-x-4">
                <span className="text-sm text-muted-foreground">Session Status:</span>
                <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                  isSessionActive 
                    ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' 
                    : 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200'
                }`}>
                  {isSessionActive ? 'Active' : 'Inactive'}
                </span>
              </div>
              
              {!isSessionActive && interviewState === 'idle' && (
                <Button onClick={connect} className="bg-blue-600 hover:bg-blue-700">
                  Start Session
                </Button>
              )}
              
              {isSessionActive && (
                <div className="flex items-center justify-center space-x-3">
                  <Button 
                    onClick={toggleMicrophone}
                    variant={isMicrophoneEnabled ? "default" : "outline"}
                    className={isMicrophoneEnabled ? "bg-green-600 hover:bg-green-700" : ""}
                  >
                    {isMicrophoneEnabled ? "🎤 Listening (Click to Mute)" : "🎤 Click to Unmute"}
                  </Button>
                  <Button onClick={disconnect} variant="outline">
                    Stop Session
                  </Button>
                </div>
              )}
              
              {questionNumber > 0 && (
                <div className="text-sm text-muted-foreground">
                  Question {questionNumber}
                </div>
              )}
            </motion.div>

            {/* AI Avatar */}
            <AIAvatar interviewState={interviewState} />

            {/* Current Question Display (when AI is speaking) */}
            {currentQuestion && interviewState === "speaking" && (
              <motion.div
                className="max-w-2xl text-center"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
              >
                <p className="text-muted-foreground text-sm mb-2">
                  Question {questionNumber}
                </p>
                <p className="text-lg text-foreground leading-relaxed">
                  {currentQuestion}
                </p>
              </motion.div>
            )}

            {/* Transcript Display */}
            {transcript.length > 0 && (
              <motion.div
                className="w-full max-w-2xl bg-muted/50 rounded-lg p-4 max-h-60 overflow-y-auto"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
              >
                <h3 className="text-sm font-medium text-muted-foreground mb-3">Conversation</h3>
                <div className="space-y-2">
                  {transcript.map((entry, index) => (
                    <div key={index} className={`text-sm ${
                      entry.type === 'user' ? 'text-blue-600 dark:text-blue-400' :
                      entry.type === 'ai' ? 'text-green-600 dark:text-green-400' :
                      entry.type === 'system' ? 'text-gray-500 dark:text-gray-400 italic' :
                      'text-red-500 dark:text-red-400'
                    }`}>
                      <span className="font-medium">
                        {entry.type === 'user' ? 'You: ' :
                         entry.type === 'ai' ? 'Interviewer: ' :
                         entry.type === 'system' ? 'System: ' :
                         'Error: '}
                      </span>
                      {entry.message}
                    </div>
                  ))}
                </div>
              </motion.div>
            )}

            {/* Interview Type Badge */}
            <motion.div
              className="px-4 py-2 bg-muted rounded-full"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.4 }}
            >
              <span className="text-sm font-medium text-muted-foreground">
                Caregiving Interview
              </span>
            </motion.div>

            {/* Settings Button */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.5 }}
            >
              <DeviceSettingsModal
                onCameraChange={handleCameraChange}
                onSpeakerChange={handleSpeakerChange}
              >
                <Button variant="outline" size="sm">
                  <Settings className="w-4 h-4 mr-2" />
                  Settings
                </Button>
              </DeviceSettingsModal>
            </motion.div>
          </motion.div>
        </div>
      </main>

      {/* Self View */}
      <SelfView selectedCameraId={selectedCameraId} />
    </div>
  );
}