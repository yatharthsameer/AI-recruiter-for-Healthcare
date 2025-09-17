"""
Unified ASGI App for AI Interviewer Backend
Combines Flask-style HTTP routes with Starlette WebSocket for single-port deployment
Handles real-time audio streaming with VAD-driven turn detection and complete interview flow
"""
import os
import json
import logging
import asyncio
import webrtcvad
import uuid
import re
from typing import Dict, Optional, List
from datetime import datetime
from collections import deque

from starlette.applications import Starlette
from starlette.routing import Route, WebSocketRoute
from starlette.responses import JSONResponse
from starlette.websockets import WebSocket, WebSocketDisconnect
from starlette.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from services.gemini_audio_service import gemini_audio_service
from models.interview_session import InterviewSession, UserData
from services.gemini_service import gemini_service
from services.caregiver_evaluation_service import caregiver_evaluation_service
from utils.file_generator import file_generator

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Audio configuration constants (must match client)
SAMPLE_RATE = int(os.getenv('SAMPLE_RATE', 16000))
CHUNK_MS = int(os.getenv('CHUNK_MS', 20))
FRAME_BYTES = int(os.getenv('FRAME_BYTES', 640))
END_SIL_MS = int(os.getenv('END_SIL_MS', 2000))  # Increased to 2 seconds for thinking pauses
VOICE_START_THRESHOLD = int(os.getenv('VOICE_START_THRESHOLD', 8))  # More frames needed to start
VOICE_END_THRESHOLD = int(os.getenv('VOICE_END_THRESHOLD', 100))    # Much longer wait (2 seconds) before ending

# VAD configuration
VAD_MODE = 3  # Most aggressive VAD mode
FRAMES_PER_BUFFER = END_SIL_MS // CHUNK_MS  # Number of frames for silence detection


class AudioSession:
    """Manages audio processing state and interview session for a WebSocket connection"""

    def __init__(self, websocket: WebSocket):
        self.websocket = websocket
        self.vad = webrtcvad.Vad(VAD_MODE)
        self.is_speaking = False
        self.voice_frames = 0
        self.silence_frames = 0
        self.audio_buffer = bytearray()
        self.session_id = str(uuid.uuid4())

        # Ring buffer for recent frames (for context)
        self.frame_buffer = deque(maxlen=FRAMES_PER_BUFFER * 2)

        # Interview session management
        self.interview_session = InterviewSession(self.session_id)
        self.interview_started = False
        self.current_transcript = ""

        # Enhanced pause tolerance for natural conversation
        self.last_transcription_time = None
        self.response_continuation_window = 10.0  # 10 seconds to continue a response
        self.accumulated_response = ""  # Store partial responses
        self.waiting_for_continuation = False

        # Audio capture for multimodal evaluation
        self.current_response_audio = bytearray()  # Capture audio for current response
        self.response_audio_chunks = []  # Store audio for each response

        # Natural conversation tracking
        self.conversation_history = []  # Full conversation history

        # Topic coverage tracking for comprehensive evaluation
        from services.topic_coverage_tracker import TopicCoverageTracker

        self.topic_tracker = TopicCoverageTracker()

        logger.info(f"🎤 New audio session created: {self.session_id}")

    async def cleanup(self) -> None:
        """Clean up session resources"""
        try:
            # Process any remaining accumulated response
            if self.accumulated_response and self.interview_started:
                await self._send_final_response(self.accumulated_response)

            # Clear buffers
            self.audio_buffer.clear()
            self.frame_buffer.clear()

            logger.info(f"🧹 Session cleaned up: {self.session_id}")
        except Exception as e:
            logger.error(f"❌ Error during session cleanup: {e}")

    async def _send_error(self, error_message: str) -> None:
        """Send error message to client"""
        try:
            message = {
                "type": "error",
                "message": error_message,
                "session_id": self.session_id,
                "timestamp": datetime.now().isoformat()
            }
            await self.websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"❌ Error sending error message: {e}")

    async def process_audio_frame(self, frame_data: bytes) -> None:
        """Process a single audio frame with VAD and transcription logic"""
        try:
            # Validate frame size
            if len(frame_data) != FRAME_BYTES:
                logger.warning(f"Invalid frame size: {len(frame_data)} != {FRAME_BYTES}")
                return

            logger.debug(f"📥 Received audio frame: {len(frame_data)} bytes")

            # Add frame to ring buffer
            self.frame_buffer.append(frame_data)

            # Run VAD on this frame
            is_voice = self.vad.is_speech(frame_data, SAMPLE_RATE)

            # Update voice activity state machine
            await self._update_voice_activity(is_voice, frame_data)

        except Exception as e:
            logger.error(f"❌ Error processing audio frame: {e}")

    async def _update_voice_activity(self, is_voice: bool, frame_data: bytes) -> None:
        """Update voice activity state and handle transcription"""

        if is_voice:
            self.voice_frames += 1
            self.silence_frames = 0

            # Add frame to transcription buffer
            self.audio_buffer.extend(frame_data)

            # Also capture for multimodal evaluation if interview started
            if self.interview_started:
                self.current_response_audio.extend(frame_data)

            # Start speaking if we cross the threshold
            if not self.is_speaking and self.voice_frames >= VOICE_START_THRESHOLD:
                self.is_speaking = True
                await self._send_voice_activity(True)
                logger.debug(f"🗣️ Voice activity started (session: {self.session_id})")

        else:
            self.silence_frames += 1
            self.voice_frames = 0

            # Continue buffering during short pauses
            if self.is_speaking:
                self.audio_buffer.extend(frame_data)

                # Also capture silence for complete response audio
                if self.interview_started:
                    self.current_response_audio.extend(frame_data)

            # End speaking if we have enough silence
            if self.is_speaking and self.silence_frames >= VOICE_END_THRESHOLD:
                await self._end_voice_activity()

    async def _end_voice_activity(self) -> None:
        """End voice activity and transcribe accumulated audio"""
        self.is_speaking = False
        await self._send_voice_activity(False)

        logger.debug(f"🔇 Voice activity ended (session: {self.session_id})")

        # Transcribe the accumulated audio
        if len(self.audio_buffer) > 0:
            await self._transcribe_buffer()

        # Reset for next utterance
        self.audio_buffer.clear()
        self.voice_frames = 0
        self.silence_frames = 0

    async def _transcribe_buffer(self) -> None:
        """Transcribe the current audio buffer"""
        try:
            # Require minimum audio length to avoid transcribing short sounds/feedback
            min_audio_bytes = FRAME_BYTES * 50  # At least 1 second of audio (50 frames)
            if len(self.audio_buffer) < min_audio_bytes:
                logger.debug(f"Audio buffer too small for transcription: {len(self.audio_buffer)} < {min_audio_bytes} bytes")
                return

            logger.info(f"🎯 Transcribing {len(self.audio_buffer)} bytes of audio")

            # Transcribe using Gemini Audio service
            transcript, is_final = gemini_audio_service.transcribe_int16_pcm(bytes(self.audio_buffer))

            if transcript and is_final and len(transcript.strip()) > 5:  # Require meaningful text
                await self._send_transcript(transcript, is_final)
            else:
                logger.debug(f"Transcript too short or empty: '{transcript}'")

        except Exception as e:
            logger.error(f"❌ Transcription error: {e}")

    async def _send_voice_activity(self, speaking: bool) -> None:
        """Send voice activity status to client"""
        try:
            message = {
                "type": "voice_activity",
                "speaking": speaking,
                "session_id": self.session_id,
                "timestamp": datetime.now().isoformat()
            }
            await self.websocket.send_text(json.dumps(message))

        except Exception as e:
            logger.error(f"❌ Error sending voice activity: {e}")

    async def _send_transcript(self, text: str, is_final: bool) -> None:
        """Send transcript to client and handle interview logic with response continuation"""
        try:
            current_time = datetime.now()

            # Check if this might be a continuation of a previous response
            if (self.last_transcription_time and 
                (current_time - self.last_transcription_time).total_seconds() < self.response_continuation_window and
                self.accumulated_response):

                # This is likely a continuation - append to accumulated response
                self.accumulated_response += " " + text
                logger.info(f"📝 Continuing response: {text} (Full: {self.accumulated_response})")
                self.waiting_for_continuation = True

            else:
                # This is a new response or the first part
                if self.accumulated_response and self.waiting_for_continuation:
                    # Send the completed accumulated response first
                    await self._send_final_response(self.accumulated_response)

                # Start new response
                self.accumulated_response = text
                logger.info(f"📝 New response started: {text}")
                self.waiting_for_continuation = False

            # Store timing
            self.last_transcription_time = current_time

            # Send transcript to client (always send the accumulated version)
            message = {
                "type": "transcript",
                "text": self.accumulated_response,
                "final": is_final,
                "session_id": self.session_id,
                "timestamp": current_time.isoformat()
            }
            await self.websocket.send_text(json.dumps(message))

            # Handle interview logic if interview has started and this seems like a complete response
            if self.interview_started and is_final and not self.waiting_for_continuation:
                # Wait a bit to see if there's a continuation
                await asyncio.sleep(1.0)
                if not self.waiting_for_continuation:
                    await self._send_final_response(self.accumulated_response)
                    self.accumulated_response = ""  # Reset for next response

        except Exception as e:
            logger.error(f"❌ Error sending transcript: {e}")

    async def _send_final_response(self, complete_response: str) -> None:
        """Send a completed response to the interview handler"""
        try:
            if self.interview_started and self.interview_session.is_active():
                await self._handle_user_response(complete_response)
                logger.info(f"📋 Processed complete response: {complete_response}")
        except Exception as e:
            logger.error(f"❌ Error processing final response: {e}")

    async def start_interview(self, user_data: Dict, interview_type: str = "general") -> None:
        """Start the interview process"""
        try:
            # Initialize interview session
            self.interview_session.start_interview(user_data, interview_type)
            self.interview_started = True

            # Start natural conversation
            first_name = user_data.get("firstName", "")

            # Generate natural opening question
            first_question = await gemini_service.start_natural_interview(
                candidate_name=first_name,
                interview_type=interview_type,
                user_data=user_data,
            )

            # Add to conversation history
            self.conversation_history.append(
                {
                    "role": "interviewer",
                    "content": first_question,
                    "timestamp": datetime.now().isoformat(),
                }
            )

            question_number = self.interview_session.add_question(first_question)

            # Send interview started message
            await self.websocket.send_text(json.dumps({
                "type": "interview_started",
                "session_id": self.session_id,
                "question": first_question,
                "questionNumber": question_number,
                "totalQuestions": self.interview_session.total_questions,
                "timestamp": datetime.now().isoformat()
            }))

            logger.info(f"Interview started for session: {self.session_id}")

        except Exception as e:
            logger.error(f"Error starting interview: {e}")
            await self._send_error("Failed to start interview")

    async def _handle_user_response(self, response_text: str) -> None:
        """Handle user response and generate next question or end interview"""
        try:
            current_q_num = len(self.interview_session.questions)

            # Capture audio data for this response
            audio_data = None
            if len(self.current_response_audio) > 0:
                audio_data = bytes(self.current_response_audio)
                self.response_audio_chunks.append(audio_data)
                logger.info(
                    f"🎵 Captured {len(audio_data)} bytes of audio for response {current_q_num}"
                )

                # Reset for next response
                self.current_response_audio.clear()

            # Add user response with audio data
            self.interview_session.add_user_response(
                response_text, current_q_num, audio_data
            )

            # Add candidate response to conversation history
            self.conversation_history.append(
                {
                    "role": "candidate",
                    "content": response_text,
                    "timestamp": datetime.now().isoformat(),
                }
            )

            # Analyze what topics this response might have covered
            last_question = ""
            if len(self.conversation_history) >= 2:
                last_question = self.conversation_history[-2].get("content", "")

            covered_topics = self.topic_tracker.analyze_response_coverage(
                response_text, last_question
            )
            if covered_topics:
                logger.info(f"📋 Response covered topics: {covered_topics}")

            # Enhanced caregiver scoring
            if self.interview_session.interview_type == 'home_care':
                await self._score_caregiver_response(response_text, current_q_num)

            # Check if we should end the interview (natural completion)
            coverage_summary = self.topic_tracker.get_coverage_summary()
            should_end = await self._should_end_interview_naturally(
                coverage_summary, current_q_num
            )

            if should_end:
                # Send closing message and wait for user to click "End Interview"
                await self._send_closing_message()
                return

            # Generate natural next response using Gemini
            next_response = await gemini_service.continue_natural_interview(
                conversation_history=self.conversation_history,
                coverage_summary=coverage_summary,
                interview_type=self.interview_session.interview_type,
                user_data=(
                    self.interview_session.user_data.__dict__
                    if self.interview_session.user_data
                    else None
                ),
            )

            if not next_response:
                next_response = "Thanks for sharing that. Could you tell me more about your experience?"

            # Add interviewer response to conversation history
            self.conversation_history.append(
                {
                    "role": "interviewer",
                    "content": next_response,
                    "timestamp": datetime.now().isoformat(),
                }
            )

            question_number = self.interview_session.add_question(next_response)

            # Send next question
            await self.websocket.send_text(
                json.dumps(
                    {
                        "type": "response_analyzed",
                        "session_id": self.session_id,
                        "nextQuestion": next_response,
                        "questionNumber": question_number,
                        "totalQuestions": self.interview_session.total_questions,
                        "timestamp": datetime.now().isoformat(),
                    }
                )
            )

            logger.info(f"Next question sent for session: {self.session_id}")

        except Exception as e:
            logger.error(f"Error handling user response: {e}")
            await self._send_error("Failed to process response")

    async def _score_caregiver_response(self, response: str, question_number: int) -> None:
        """Score caregiver response using keyword analysis"""
        try:
            txt = response.lower()
            delta = 0

            # Scoring patterns (same as Node.js version)
            patterns = {
                'empathy': (r'(empathy|empathetic|understand|understanding|compassion|compassionate|feel|feeling|emotional|emotions)', 3),
                'patience': (r'(patient|patience|calm|calmly|wait|waiting|slow|slowly|gentle|gently|take time)', 3),
                'care': (r'(care|caring|help|helping|support|supporting|assist|assisting|comfort|comforting)', 2),
                'safety': (r'(safe|safety|secure|protocol|procedure|emergency|alert|careful|cautious|report|reporting)', 4),
                'communication': (r'(listen|listening|talk|talking|explain|explaining|communicate|communication|discuss|conversation)', 2),
                'respect': (r'(respect|respectful|dignity|privacy|rights|boundaries|professional|appropriate)', 2),
                'problem_solving': (r'(solve|solution|problem|challenge|difficult|handle|manage|approach|strategy|plan)', 2),
                'experience': (r'(experience|experienced|worked|years|trained|training|certified|certification|learn|learning)', 1),
                'commitment': (r'(committed|dedication|dedicated|reliable|dependable|responsible|motivated|passion|passionate)', 2),
                'negative': (r'(angry|hate|can\'t|won\'t|never|rude|unsafe|ignore|delay|lazy|argue|frustrated|annoyed|impatient)', -3),
                'concerns': (r'(difficult|hard|struggle|struggling|stress|stressed|overwhelmed|tired|exhausted)', -1)
            }

            breakdown = {}
            for category, (pattern, weight) in patterns.items():
                matches = len(re.findall(pattern, txt, re.IGNORECASE))
                breakdown[category] = matches
                delta += matches * weight

            # Update session scoring
            self.interview_session.metadata["score"] = self.interview_session.metadata.get("score", 0) + delta
            self.interview_session.metadata["scoredResponses"] = self.interview_session.metadata.get("scoredResponses", 0) + 1

            # Store detailed breakdown
            if "scoringBreakdown" not in self.interview_session.metadata:
                self.interview_session.metadata["scoringBreakdown"] = []

            self.interview_session.metadata["scoringBreakdown"].append({
                "questionNumber": question_number,
                "delta": delta,
                "breakdown": breakdown
            })

        except Exception as e:
            logger.error(f"Error scoring caregiver response: {e}")

    async def _should_end_interview_naturally(
        self, coverage_summary: dict, current_q_num: int
    ) -> bool:
        """Determine if interview should end naturally based on coverage and conversation flow"""

        # Always ensure we have enough conversation (minimum questions)
        if current_q_num < 5:  # At least 5 exchanges
            return False

        # Check if all topics are covered
        if coverage_summary["is_complete"]:
            logger.info(f"🎯 All topics covered! Interview can end naturally.")
            return True

        # If we have a lot of questions but still missing topics, continue
        if current_q_num < 15:  # Maximum 15 exchanges to prevent endless interviews
            missing_count = coverage_summary["missing_count"]
            if missing_count <= 2:  # Only 1-2 topics missing, try to wrap up soon
                logger.info(
                    f"📋 {missing_count} topics remaining, continuing interview"
                )
            return False

        # Force end if we've gone too long (15+ questions)
        logger.info(
            f"⏰ Interview reached maximum length ({current_q_num} questions), ending"
        )
        return True

    async def _send_closing_message(self) -> None:
        """Send closing message and wait for user to manually end interview"""
        try:
            closing_message = "Thanks for taking the time to interview, please leave the call by clicking the end interview button on your screen, we will reach out to you if you are a good fit."

            # Add closing message to conversation history
            self.conversation_history.append(
                {
                    "role": "interviewer",
                    "content": closing_message,
                    "timestamp": datetime.now().isoformat(),
                }
            )

            question_number = self.interview_session.add_question(closing_message)

            # Send closing message
            await self.websocket.send_text(
                json.dumps(
                    {
                        "type": "interview_closing",
                        "session_id": self.session_id,
                        "closingMessage": closing_message,
                        "questionNumber": question_number,
                        "totalQuestions": self.interview_session.total_questions,
                        "timestamp": datetime.now().isoformat(),
                    }
                )
            )

            logger.info(f"Closing message sent for session: {self.session_id}")

        except Exception as e:
            logger.error(f"Error sending closing message: {e}")
            await self._send_error("Failed to send closing message")

    async def _end_interview(self) -> None:
        """End the interview and generate final evaluation"""
        try:
            # Build full transcript
            transcript = self.interview_session.get_full_transcript()
            transcript_text = "\n".join([
                f"Q{t['questionNumber']}: {t['question']}\nA{t['questionNumber']}: {t['userResponse']}\n"
                for t in transcript
            ])

            # Generate AI summary
            final_feedback = await gemini_service.generate_transcript_summary(
                transcript_text,
                self.interview_session.interview_type,
                self.interview_session.user_data.__dict__ if self.interview_session.user_data else None
            )

            # Generate caregiver evaluation if applicable
            caregiver_evaluation = None
            if self.interview_session.interview_type == 'home_care':
                try:
                    # Prepare interview data for evaluation with audio
                    responses_with_audio = []
                    for response in self.interview_session.user_responses:
                        response_dict = {
                            "response": response.response,
                            "questionNumber": response.questionNumber,
                            "timestamp": response.timestamp.isoformat(),
                            "audioData": response.audioData,
                            "audioMime": response.audioMime,
                        }
                        responses_with_audio.append(response_dict)

                    interview_data = {
                        "transcript": transcript_text,
                        "userData": (
                            self.interview_session.user_data.__dict__
                            if self.interview_session.user_data
                            else {}
                        ),
                        "sessionId": self.session_id,
                        "responses": responses_with_audio,
                        "audioData": self.response_audio_chunks,  # List of audio chunks
                    }

                    # Get simple evaluation from Gemini
                    caregiver_evaluation = await caregiver_evaluation_service.evaluate_candidate(interview_data)
                    logger.info(
                        f"🎯 Simple evaluation completed - Overall Score: {caregiver_evaluation.get('overallScore')}"
                    )

                    # Save evaluation as JSON file
                    try:
                        json_path = await file_generator.save_evaluation_json(
                            self.session_id, caregiver_evaluation
                        )
                        logger.info(f"💾 Evaluation JSON saved: {json_path}")
                    except Exception as json_error:
                        logger.error(f"❌ Failed to save evaluation JSON: {json_error}")

                except Exception as eval_error:
                    logger.error(f"❌ Evaluation failed: {eval_error}")
                    caregiver_evaluation = None

            # Complete interview session
            self.interview_session.complete_interview(final_feedback)
            if caregiver_evaluation:
                self.interview_session.caregiver_evaluation = caregiver_evaluation

            # Generate output files
            try:
                await file_generator.generate_interview_files(
                    self.session_id,
                    transcript,
                    self.interview_session.user_data.__dict__ if self.interview_session.user_data else {},
                    self.interview_session.get_summary(),
                    caregiver_evaluation
                )
            except Exception as file_error:
                logger.error(f"Failed to generate output files: {file_error}")

            # Send completion message
            await self.websocket.send_text(json.dumps({
                "type": "interview_completed",
                "session_id": self.session_id,
                "message": "Thank you for completing the interview. We'll be in touch soon!",
                "timestamp": datetime.now().isoformat()
            }))

            logger.info(f"Interview completed for session: {self.session_id}")

        except Exception as e:
            logger.error(f"Error ending interview: {e}")
            await self._send_error("Failed to complete interview")

    def _build_conversation_history(self) -> List[Dict]:
        """Build conversation history for AI context"""
        history = []

        questions_dict = {q.questionNumber: q.question for q in self.interview_session.questions}
        responses_dict = {r.questionNumber: r.response for r in self.interview_session.user_responses}

        for i in range(1, len(self.interview_session.questions) + 1):
            if i in questions_dict and i in responses_dict:
                history.append({
                    "question": questions_dict[i],
                    "response": responses_dict[i]
                })

        return history

    async def _send_error(self, message: str) -> None:
        """Send error message to client"""
        try:
            await self.websocket.send_text(json.dumps({
                "type": "error",
                "message": message,
                "session_id": self.session_id,
                "timestamp": datetime.now().isoformat()
            }))
        except Exception as e:
            logger.error(f"Failed to send error message: {e}")


# Global session storage
active_sessions: Dict[str, AudioSession] = {}


# HTTP Routes
async def health_check(request):
    """Health check endpoint"""
    gemini_audio_status = gemini_audio_service.health_check()
    
    return JSONResponse({
        "status": "OK",
        "timestamp": datetime.now().isoformat(),
        "service": "ai-interviewer-backend",
        "audio_config": {
            "sample_rate": SAMPLE_RATE,
            "chunk_ms": CHUNK_MS,
            "frame_bytes": FRAME_BYTES,
            "end_silence_ms": END_SIL_MS
        },
        "gemini_audio": gemini_audio_status,
        "active_sessions": len(active_sessions)
    })


async def api_status(request):
    """API status endpoint"""
    return JSONResponse({
        "active_sessions": len(active_sessions),
        "gemini_audio_status": gemini_audio_service.health_check(),
        "uptime": "N/A"  # TODO: Add actual uptime tracking
    })


async def interview_types(request):
    """Get available interview types"""
    interview_types_list = [
        {
            "id": "general",
            "name": "General Behavioral",
            "description": "Standard behavioral interview questions",
            "questionCount": 5,
            "duration": "15-20 minutes"
        },
        {
            "id": "technical",
            "name": "Technical",
            "description": "Software engineering and technical skills",
            "questionCount": 5,
            "duration": "20-25 minutes"
        },
        {
            "id": "sales",
            "name": "Sales & Business",
            "description": "Sales techniques and business development",
            "questionCount": 5,
            "duration": "15-20 minutes"
        },
        {
            "id": "leadership",
            "name": "Leadership & Management",
            "description": "Team leadership and management skills",
            "questionCount": 5,
            "duration": "20-25 minutes"
        },
        {
            "id": "customer_service",
            "name": "Customer Service",
            "description": "Customer interaction and service skills",
            "questionCount": 5,
            "duration": "15-20 minutes"
        },
        {
            "id": "home_care",
            "name": "Home Care / Caregiver",
            "description": "Caregiving skills, empathy, and patient care scenarios",
            "questionCount": 5,
            "duration": "10-15 minutes"
        }
    ]
    
    return JSONResponse({
        "interviewTypes": interview_types_list,
        "total": len(interview_types_list)
    })


async def gemini_status(request):
    """Get Gemini AI service status"""
    return JSONResponse(gemini_service.health_check())


async def interview_files(request):
    """List generated interview files"""
    files = file_generator.list_output_files()
    return JSONResponse({
        "files": files,
        "total": len(files)
    })


# WebSocket Handler
async def websocket_audio_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time audio streaming and interview management
    Handles both binary audio frames and JSON interview messages
    """
    await websocket.accept()
    
    session = AudioSession(websocket)
    session_key = f"ws_{id(websocket)}"
    active_sessions[session_key] = session
    
    logger.info(f"🔗 WebSocket connected: {session.session_id}")
    
    try:
        # Send initial connection confirmation
        await websocket.send_text(json.dumps({
            "type": "connection",
            "session_id": session.session_id,
            "message": "Connected to AI Interviewer",
            "config": {
                "sample_rate": SAMPLE_RATE,
                "frame_bytes": FRAME_BYTES,
                "chunk_ms": CHUNK_MS
            }
        }))
        
        # Main message loop
        while True:
            try:
                # Receive any message (text or binary)
                message = await websocket.receive()
                
                # Check for disconnect messages
                if message['type'] == 'websocket.disconnect':
                    logger.info(f"🔌 Client disconnected: {session.session_id}")
                    break
                elif message['type'] == 'websocket.receive':
                    if 'text' in message:
                        # Handle JSON text message
                        try:
                            data = json.loads(message['text'])
                            await handle_interview_message(session, data)
                        except json.JSONDecodeError as e:
                            logger.error(f"Invalid JSON message: {e}")
                            await session._send_error("Invalid message format")
                    elif 'bytes' in message:
                        # Handle binary audio data
                        await session.process_audio_frame(message['bytes'])
                        
            except WebSocketDisconnect:
                logger.info(f"🔌 WebSocket disconnected gracefully: {session.session_id}")
                break
            except Exception as e:
                # Check if it's a disconnect-related error
                if "disconnect" in str(e).lower() or "receive" in str(e).lower():
                    logger.info(f"🔌 Connection closed: {session.session_id}")
                    break
                else:
                    logger.error(f"❌ Message handling error: {e}")
                    break
            
    except WebSocketDisconnect:
        logger.info(f"🔌 WebSocket disconnected: {session.session_id}")
    except Exception as e:
        logger.error(f"❌ WebSocket error: {e}")
    finally:
        # Cleanup session properly
        try:
            await session.cleanup()
        except Exception as cleanup_error:
            logger.error(f"❌ Error during final cleanup: {cleanup_error}")
        
        # Remove from active sessions
        if session_key in active_sessions:
            del active_sessions[session_key]


async def handle_interview_message(session: AudioSession, message: Dict) -> None:
    """Handle interview-related WebSocket messages"""
    try:
        message_type = message.get("type")
        data = message.get("data", {})
        
        logger.info(f"Received message type: {message_type} from session: {session.session_id}")
        
        if message_type == "start_interview":
            user_data = data.get("userData", {})
            interview_type = data.get("interviewType", "general")
            await session.start_interview(user_data, interview_type)
            
        elif message_type == "user_response":
            response = data.get("response", "")
            if response.strip():
                await session._handle_user_response(response.strip())
            
        elif message_type == "next_question":
            # Handle explicit next question request
            question_number = data.get("questionNumber", 0)
            if question_number >= session.interview_session.total_questions:
                await session._end_interview()
            
        elif message_type == "end_interview":
            await session._end_interview()
            
        elif message_type == "ping":
            await session.websocket.send_text(json.dumps({
                "type": "pong", 
                "timestamp": datetime.now().isoformat()
            }))
            
        else:
            await session._send_error(f"Unknown message type: {message_type}")
            
    except Exception as e:
        logger.error(f"Error handling interview message: {e}")
        await session._send_error("Failed to process message")


# Define routes
routes = [
    Route("/health", health_check, methods=["GET"]),
    Route("/api/status", api_status, methods=["GET"]),
    Route("/api/interview/types", interview_types, methods=["GET"]),
    Route("/api/gemini-status", gemini_status, methods=["GET"]),
    Route("/api/interview/files", interview_files, methods=["GET"]),
    WebSocketRoute("/ws/audio", websocket_audio_endpoint),
]

# Create ASGI application
app = Starlette(routes=routes)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("🚀 AI Interviewer Backend starting up...")
    logger.info(f"📊 Audio config: {SAMPLE_RATE}Hz, {CHUNK_MS}ms chunks, {FRAME_BYTES} bytes/frame")
    
    # Test Gemini Audio service
    gemini_audio_status = gemini_audio_service.health_check()
    if gemini_audio_status["status"] == "healthy":
        logger.info("✅ Gemini Audio service ready")
    else:
        logger.error(f"❌ Gemini Audio service error: {gemini_audio_status['message']}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("🛑 AI Interviewer Backend shutting down...")
    
    # Close all active WebSocket sessions
    for session_key in list(active_sessions.keys()):
        try:
            session = active_sessions[session_key]
            await session.websocket.close()
            del active_sessions[session_key]
        except Exception as e:
            logger.error(f"Error closing session {session_key}: {e}")
    
    logger.info("✅ Shutdown complete")


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 3000))
    host = os.getenv("HOST", "0.0.0.0")
    debug = os.getenv("DEBUG", "false").lower() == "true"
    
    logger.info(f"🌐 Starting server on {host}:{port}")
    
    uvicorn.run(
        "asgi_app:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info"
    )
