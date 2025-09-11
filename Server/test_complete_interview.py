#!/usr/bin/env python3
"""
Complete Interview Test Script
Tests the full interview flow with the Python backend
"""
import asyncio
import json
import numpy as np
import websockets
from typing import Optional

# Test configuration
WS_URL = "ws://localhost:3000/ws/audio"
SAMPLE_RATE = 16000
FRAME_BYTES = 640

class InterviewTestClient:
    """Test client for complete interview flow"""
    
    def __init__(self):
        self.websocket: Optional[websockets.WebSocketServerProtocol] = None
        self.session_id = ""
        self.running = False
    
    async def connect(self):
        """Connect to WebSocket server"""
        try:
            print(f"🔗 Connecting to {WS_URL}")
            self.websocket = await websockets.connect(WS_URL)
            print("✅ Connected to WebSocket")
            return True
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    async def listen_for_messages(self):
        """Listen for messages from server"""
        try:
            while self.running and self.websocket:
                message = await self.websocket.recv()
                data = json.loads(message)
                await self.handle_message(data)
                    
        except websockets.exceptions.ConnectionClosed:
            print("🔌 Connection closed by server")
        except Exception as e:
            print(f"❌ Listen error: {e}")
    
    async def handle_message(self, data):
        """Handle incoming messages"""
        msg_type = data.get("type")
        
        if msg_type == "connection":
            self.session_id = data.get("session_id", "")
            print(f"📡 Connected with session: {self.session_id}")
            
        elif msg_type == "interview_started":
            question = data.get("question", "")
            q_num = data.get("questionNumber", 0)
            print(f"❓ Question {q_num}: {question}")
            
            # Simulate user thinking time
            await asyncio.sleep(2)
            
            # Send a test response
            test_response = self.get_test_response(q_num)
            await self.send_text_response(test_response)
            
        elif msg_type == "response_analyzed":
            question = data.get("nextQuestion", "")
            q_num = data.get("questionNumber", 0)
            print(f"❓ Question {q_num}: {question}")
            
            # Simulate user thinking time
            await asyncio.sleep(2)
            
            # Send a test response
            test_response = self.get_test_response(q_num)
            await self.send_text_response(test_response)
            
        elif msg_type == "voice_activity":
            speaking = data.get("speaking")
            print(f"🗣️ Voice activity: {'Speaking' if speaking else 'Silent'}")
            
        elif msg_type == "transcript":
            text = data.get("text", "")
            is_final = data.get("final", False)
            if is_final and text:
                print(f"📝 Transcript: {text}")
            
        elif msg_type == "interview_completed":
            print("🎉 Interview completed!")
            message = data.get("message", "")
            if message:
                print(f"💬 {message}")
            self.running = False
            
        elif msg_type == "error":
            error_msg = data.get("message", "Unknown error")
            print(f"❌ Error: {error_msg}")
            
        else:
            print(f"📨 Received: {data}")
    
    def get_test_response(self, question_number: int) -> str:
        """Get test response for each question"""
        responses = [
            "I have been working as a caregiver for over 5 years. I started because I wanted to help elderly people maintain their independence and dignity. It's very rewarding work.",
            "I once had a client who was very resistant to taking medication. I sat down with them, listened to their concerns, and explained why the medication was important. I also worked with their family to find a routine that worked better.",
            "I would first check the medication schedule and gently remind them about the importance of taking it on time. If they insisted they already took it, I would document this and contact their healthcare provider for guidance.",
            "I am CPR certified and have had to use these skills twice. The first time was when a client had difficulty breathing. I stayed calm, called 911, and was prepared to perform CPR if needed. Fortunately, the paramedics arrived quickly.",
            "Caregiving can be emotionally demanding, but I stay motivated by remembering that I'm making a real difference in someone's life. I also make sure to take care of myself and have a good support system."
        ]
        
        if question_number <= len(responses):
            return responses[question_number - 1]
        else:
            return "Thank you for the question. I believe my experience and dedication make me a good fit for this role."
    
    async def send_text_response(self, response: str):
        """Send a text response (simulates user speaking)"""
        if not self.websocket:
            return
        
        print(f"💬 Sending response: {response}")
        
        # Send as interview message
        await self.websocket.send(json.dumps({
            "type": "user_response",
            "data": {
                "response": response,
                "questionNumber": 1  # This will be updated by backend
            }
        }))
    
    async def start_interview(self):
        """Start the interview"""
        if not self.websocket:
            print("❌ Not connected")
            return
        
        print("🎬 Starting interview...")
        
        # Test user data (caregiver interview)
        user_data = {
            "firstName": "Test",
            "lastName": "Candidate",
            "email": "test@example.com",
            "phone": "+1234567890",
            "position": "Caregiver",
            "hhaExperience": True,
            "cprCertified": True,
            "driversLicense": True,
            "autoInsurance": True,
            "reliableTransport": True,
            "locationPref": "California",
            "availability": ["Mornings", "Afternoons"],
            "weeklyHours": 30
        }
        
        await self.websocket.send(json.dumps({
            "type": "start_interview",
            "data": {
                "userData": user_data,
                "interviewType": "home_care"
            }
        }))
    
    async def send_test_audio(self):
        """Send some test audio frames"""
        print("🎵 Sending test audio frames...")
        
        # Generate 2 seconds of 440Hz sine wave
        duration = 2.0
        frequency = 440.0
        total_samples = int(SAMPLE_RATE * duration)
        
        # Generate sine wave
        t = np.linspace(0, duration, total_samples, False)
        audio = np.sin(2 * np.pi * frequency * t)
        
        # Convert to Int16
        audio_int16 = (audio * 32767 * 0.3).astype(np.int16)
        audio_bytes = audio_int16.tobytes()
        
        # Send in 640-byte frames
        samples_per_frame = FRAME_BYTES // 2  # 320 samples
        
        for i in range(0, len(audio_bytes), FRAME_BYTES):
            frame = audio_bytes[i:i + FRAME_BYTES]
            
            # Pad frame if necessary
            if len(frame) < FRAME_BYTES:
                frame += b'\x00' * (FRAME_BYTES - len(frame))
            
            await self.websocket.send(frame)
            await asyncio.sleep(0.02)  # 20ms between frames
    
    async def disconnect(self):
        """Disconnect from server"""
        self.running = False
        if self.websocket:
            await self.websocket.close()
            print("🔌 Disconnected")

async def main():
    """Main test function"""
    print("🎯 AI Interviewer Complete Interview Test")
    print("=" * 50)
    
    client = InterviewTestClient()
    
    # Connect to server
    if not await client.connect():
        return
    
    client.running = True
    
    try:
        # Start listening for messages
        listen_task = asyncio.create_task(client.listen_for_messages())
        
        # Wait for connection to stabilize
        await asyncio.sleep(1.0)
        
        # Start the interview
        await client.start_interview()
        
        # Send some test audio to trigger voice activity
        await asyncio.sleep(2.0)
        await client.send_test_audio()
        
        # Wait for interview to complete
        await listen_task
        
        print("\n✅ Test completed successfully!")
        
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"❌ Test error: {e}")
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
