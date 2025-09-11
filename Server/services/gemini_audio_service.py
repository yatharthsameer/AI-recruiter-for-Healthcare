"""
Gemini Audio Service for Real-time Audio Transcription
Handles multimodal audio processing using Google's Gemini API
"""
import os
import io
import wave
import logging
import tempfile
from typing import Optional, Tuple
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class GeminiAudioService:
    """Service for audio transcription using Gemini's multimodal capabilities"""
    
    def __init__(self):
        self.api_key = os.getenv('GEMINI_API_KEY')
        self.model_name = os.getenv('GEMINI_AUDIO_MODEL', 'gemini-1.5-flash')
        self.model = None
        self.initialized = False
        
        # Audio processing settings
        self.sample_rate = int(os.getenv('SAMPLE_RATE', 16000))
        self.min_audio_length = 0.5  # Minimum seconds of audio to transcribe
        self.max_audio_length = 30.0  # Maximum seconds to avoid memory issues
        
        logger.info(f"Initializing Gemini Audio service with model: {self.model_name}")
        
        if self.api_key:
            self._initialize_model()
        else:
            logger.error("GEMINI_API_KEY not set")
    
    def _initialize_model(self):
        """Initialize the Gemini model with specified configuration"""
        try:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(self.model_name)
            self.initialized = True
            logger.info(f"✅ Gemini Audio model '{self.model_name}' loaded successfully")
        except Exception as e:
            logger.error(f"❌ Failed to load Gemini Audio model: {e}")
            self.initialized = False
            raise
    
    def transcribe_int16_pcm(self, audio_buffer: bytes) -> Tuple[str, bool]:
        """
        Transcribe Int16 PCM audio buffer using Gemini multimodal API
        
        Args:
            audio_buffer: Raw PCM audio bytes (Int16, mono, 16kHz)
            
        Returns:
            Tuple of (transcribed_text, is_final)
        """
        try:
            if not self.initialized:
                logger.error("Gemini Audio model not initialized")
                return "", False
            
            # Check audio length
            audio_length = len(audio_buffer) / (2 * self.sample_rate)  # 2 bytes per sample
            if audio_length < self.min_audio_length:
                logger.debug(f"Audio too short: {audio_length:.2f}s < {self.min_audio_length}s")
                return "", False
            
            if audio_length > self.max_audio_length:
                logger.warning(f"Audio too long: {audio_length:.2f}s > {self.max_audio_length}s, truncating")
                max_samples = int(self.max_audio_length * self.sample_rate)
                max_bytes = max_samples * 2  # 2 bytes per sample
                audio_buffer = audio_buffer[:max_bytes]
            
            # Convert PCM to WAV format for Gemini
            wav_data = self._pcm_to_wav(audio_buffer)
            
            # Create temporary file for audio upload
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_file.write(wav_data)
                temp_file_path = temp_file.name
            
            try:
                # Upload audio file to Gemini
                audio_file = genai.upload_file(temp_file_path, mime_type='audio/wav')
                
                # Create prompt for transcription
                prompt = """
                Please transcribe this audio accurately. Return only the spoken text without any additional formatting, 
                explanations, or metadata. If no clear speech is detected, return an empty string.
                """
                
                # Generate transcription using multimodal model
                response = self.model.generate_content([prompt, audio_file])
                
                # Clean up uploaded file
                genai.delete_file(audio_file.name)
                
                # Extract transcribed text
                transcribed_text = response.text.strip() if response.text else ""
                
                # Filter out common noise/artifacts
                if self._is_meaningful_text(transcribed_text):
                    logger.info(f"✅ Transcribed: '{transcribed_text}'")
                    return transcribed_text, True
                else:
                    logger.debug(f"Filtered out noise: '{transcribed_text}'")
                    return "", False
                    
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_file_path)
                except OSError:
                    pass
            
        except Exception as e:
            logger.error(f"❌ Gemini transcription error: {e}")
            return "", False
    
    def _pcm_to_wav(self, pcm_data: bytes) -> bytes:
        """Convert PCM audio data to WAV format"""
        try:
            # Create WAV file in memory
            wav_buffer = io.BytesIO()
            
            with wave.open(wav_buffer, 'wb') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit (2 bytes per sample)
                wav_file.setframerate(self.sample_rate)
                wav_file.writeframes(pcm_data)
            
            wav_buffer.seek(0)
            return wav_buffer.read()
            
        except Exception as e:
            logger.error(f"❌ PCM to WAV conversion error: {e}")
            raise
    
    def _is_meaningful_text(self, text: str) -> bool:
        """Check if transcribed text is meaningful (not noise/artifacts)"""
        if not text:
            return False
        
        # Filter out common noise patterns
        noise_patterns = [
            "thank you",
            "thanks for watching",
            "subscribe",
            "like and subscribe",
            "music",
            "[music]",
            "(music)",
            "applause",
            "[applause]",
            "(applause)",
            "laughter",
            "[laughter]",
            "(laughter)",
            "silence",
            "...",
            "um",
            "uh",
            "hmm"
        ]
        
        text_lower = text.lower().strip()
        
        # Check if it's just noise
        if text_lower in noise_patterns:
            return False
        
        # Check minimum length and word count
        if len(text.strip()) < 3:
            return False
        
        words = text.split()
        if len(words) < 1:
            return False
        
        # Check for repeated single characters (artifacts)
        if len(set(text.replace(' ', ''))) == 1 and len(text) > 3:
            return False
        
        return True
    
    def health_check(self) -> dict:
        """Check Gemini Audio service health"""
        try:
            if not self.api_key:
                return {
                    "status": "error",
                    "message": "GEMINI_API_KEY not configured"
                }
            
            if not self.initialized:
                return {
                    "status": "error", 
                    "message": "Gemini Audio model not initialized"
                }
            
            return {
                "status": "healthy",
                "message": "Gemini Audio service ready",
                "model": self.model_name,
                "sample_rate": self.sample_rate
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Gemini Audio service error: {str(e)}"
            }

# Global instance
gemini_audio_service = GeminiAudioService()
