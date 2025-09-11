#!/usr/bin/env python3
"""
Simple WebSocket test client for AI Interviewer backend
Tests the /ws/audio endpoint with dummy audio data
"""
import asyncio
import json
import numpy as np
import websockets
from typing import Optional

# Audio constants (must match server)
SAMPLE_RATE = 16000
CHUNK_MS = 20
FRAME_BYTES = 640
FRAMES_PER_SECOND = 1000 // CHUNK_MS  # 50 FPS

class AudioTestClient:
    def __init__(self, url: str = "ws://localhost:3000/ws/audio"):
        self.url = url
        self.websocket: Optional[websockets.WebSocketServerProtocol] = None
        self.running = False
    
    async def connect(self):
        """Connect to WebSocket server"""
        try:
            print(f"🔗 Connecting to {self.url}")
            self.websocket = await websockets.connect(self.url)
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
                
                msg_type = data.get("type")
                if msg_type == "connected":
                    print(f"📡 Server connected: {data.get('session_id')}")
                elif msg_type == "voice_activity":
                    speaking = data.get("speaking")
                    print(f"🗣️ Voice activity: {'Speaking' if speaking else 'Silent'}")
                elif msg_type == "transcript":
                    text = data.get("text", "")
                    is_final = data.get("final", False)
                    print(f"📝 Transcript ({'final' if is_final else 'partial'}): {text}")
                else:
                    print(f"📨 Received: {data}")
                    
        except websockets.exceptions.ConnectionClosed:
            print("🔌 Connection closed by server")
        except Exception as e:
            print(f"❌ Listen error: {e}")
    
    def generate_test_audio(self, duration_seconds: float = 2.0, frequency: float = 440.0) -> bytes:
        """Generate test audio data (sine wave)"""
        total_samples = int(SAMPLE_RATE * duration_seconds)
        
        # Generate sine wave
        t = np.linspace(0, duration_seconds, total_samples, False)
        audio = np.sin(2 * np.pi * frequency * t)
        
        # Convert to Int16
        audio_int16 = (audio * 32767 * 0.5).astype(np.int16)
        
        return audio_int16.tobytes()
    
    def generate_silence(self, duration_seconds: float = 1.0) -> bytes:
        """Generate silence"""
        total_samples = int(SAMPLE_RATE * duration_seconds)
        silence = np.zeros(total_samples, dtype=np.int16)
        return silence.tobytes()
    
    async def send_audio_frames(self, audio_data: bytes):
        """Send audio data in 640-byte frames"""
        if not self.websocket:
            print("❌ Not connected")
            return
        
        print(f"📤 Sending {len(audio_data)} bytes of audio in {FRAME_BYTES}-byte frames")
        
        # Send in chunks of FRAME_BYTES
        for i in range(0, len(audio_data), FRAME_BYTES):
            frame = audio_data[i:i + FRAME_BYTES]
            
            # Pad last frame if necessary
            if len(frame) < FRAME_BYTES:
                frame += b'\x00' * (FRAME_BYTES - len(frame))
            
            await self.websocket.send(frame)
            
            # Simulate real-time by waiting 20ms between frames
            await asyncio.sleep(CHUNK_MS / 1000.0)
    
    async def test_sequence(self):
        """Run a test sequence with voice and silence"""
        print("\n🎯 Starting test sequence...")
        
        # Test 1: Send silence (should not trigger voice activity)
        print("\n1️⃣ Sending 1 second of silence...")
        silence = self.generate_silence(1.0)
        await self.send_audio_frames(silence)
        await asyncio.sleep(0.5)
        
        # Test 2: Send tone (should trigger voice activity and transcription)
        print("\n2️⃣ Sending 2 seconds of 440Hz tone...")
        tone = self.generate_test_audio(2.0, 440.0)
        await self.send_audio_frames(tone)
        await asyncio.sleep(0.5)
        
        # Test 3: Send silence to end voice activity
        print("\n3️⃣ Sending 1 second of silence to end voice activity...")
        silence = self.generate_silence(1.0)
        await self.send_audio_frames(silence)
        await asyncio.sleep(1.0)
        
        print("\n✅ Test sequence complete")
    
    async def disconnect(self):
        """Disconnect from server"""
        self.running = False
        if self.websocket:
            await self.websocket.close()
            print("🔌 Disconnected")

async def main():
    """Main test function"""
    print("🎤 AI Interviewer WebSocket Test Client")
    print("=" * 40)
    
    client = AudioTestClient()
    
    # Connect to server
    if not await client.connect():
        return
    
    client.running = True
    
    try:
        # Start listening for messages
        listen_task = asyncio.create_task(client.listen_for_messages())
        
        # Wait a moment for connection to stabilize
        await asyncio.sleep(1.0)
        
        # Run test sequence
        await client.test_sequence()
        
        # Wait for any final messages
        await asyncio.sleep(2.0)
        
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"❌ Test error: {e}")
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
