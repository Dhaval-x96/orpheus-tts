import os
import json
import time
import wave
import requests
import tempfile
import logging
from io import BytesIO
from typing import Dict, Generator, Optional, Union

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Try to import snac - it's required for audio generation
try:
    from snac import SNAC
    snac_available = True
except ImportError:
    logger.warning("SNAC package not found. Installing it now...")
    os.system("pip install snac")
    try:
        from snac import SNAC
        snac_available = True
    except ImportError:
        logger.error("Failed to install SNAC. Audio conversion will not work.")
        snac_available = False

# Available voices
AVAILABLE_VOICES = [
    "tara", "leah", "jess", "leo", 
    "dan", "mia", "zac", "zoe"
]

class OrpheusOllama:
    """Orpheus TTS implementation using Ollama as the backend LLM server"""
    
    def __init__(self, 
                 model_name: str = "orpheus",
                 api_url: Optional[str] = None,
                 api_timeout: int = 120,
                 temperature: float = 0.6,
                 top_p: float = 0.9,
                 repeat_penalty: float = 1.1,
                 sample_rate: int = 24000):
        """Initialize Orpheus TTS with Ollama backend."""
        # Ollama connection settings
        self.model_name = model_name
        self.api_url = api_url or os.getenv("OLLAMA_API_URL", "http://localhost:11434/api/generate")
        self.api_timeout = api_timeout
        
        # Generation parameters
        self.temperature = temperature
        self.top_p = top_p
        self.repeat_penalty = repeat_penalty
        self.sample_rate = sample_rate
        
        # Initialize SNAC for audio conversion
        if snac_available:
            try:
                self.snac_model = SNAC()
                logger.info("SNAC model initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize SNAC model: {str(e)}")
                self.snac_model = None
        else:
            self.snac_model = None
            logger.error("SNAC model is not available. Audio conversion will not work.")
        
        logger.info(f"Initialized Orpheus TTS with Ollama backend at {self.api_url}")
        logger.info(f"Using model: {self.model_name}")
        logger.info(f"Parameters: temp={self.temperature}, top_p={self.top_p}, repeat_penalty={self.repeat_penalty}")
    
    def format_prompt(self, text: str, voice: str = "tara") -> str:
        """Format text with voice name as expected by Orpheus."""
        if voice not in AVAILABLE_VOICES:
            logger.warning(f"Voice '{voice}' not in available voices. Using 'tara' instead.")
            voice = "tara"
        
        return f"{voice}: {text}"
    
    def generate_speech(self, 
                      text: str, 
                      voice: str = "tara",
                      stream: bool = False) -> Union[bytes, Generator[bytes, None, None]]:
        """Generate speech from text using Ollama and SNAC."""
        # Check if SNAC is available
        if self.snac_model is None:
            error_msg = "SNAC model is not available. Cannot generate speech."
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        # Format the prompt for Orpheus
        prompt = self.format_prompt(text, voice)
        
        if stream:
            # Return a generator for streaming audio
            return self._stream_audio(prompt)
        else:
            # Generate complete audio and return bytes
            return self._generate_complete_audio(prompt)
    
    def _generate_complete_audio(self, prompt: str) -> bytes:
        """Generate complete audio file from text."""
        logger.info(f"Generating complete audio for prompt: {prompt[:50]}...")
        
        # Prepare request payload for Ollama
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "top_p": self.top_p,
                "repeat_penalty": self.repeat_penalty
            }
        }
        
        try:
            # Request text generation from Ollama
            response = requests.post(
                self.api_url,
                json=payload,
                timeout=self.api_timeout
            )
            
            if response.status_code != 200:
                logger.error(f"Ollama API request failed: {response.status_code} - {response.text}")
                raise RuntimeError(f"Failed to generate text: {response.text}")
            
            # Extract generated text
            result = response.json()
            generated_text = result.get("response", "")
            
            if not generated_text:
                logger.warning("Ollama returned empty response")
                return b""
            
            # Convert to audio using SNAC
            logger.info("Converting generated text to audio...")
            audio_samples = self.snac_model.generate_with_text(generated_text)
            
            # Create WAV file in memory
            wav_buffer = BytesIO()
            with wave.open(wav_buffer, "wb") as wf:
                wf.setnchannels(1)  # Mono
                wf.setsampwidth(2)  # 16-bit
                wf.setframerate(self.sample_rate)
                
                # Convert to int16
                import numpy as np
                audio_int16 = (audio_samples * 32767).astype(np.int16)
                wf.writeframes(audio_int16.tobytes())
            
            wav_buffer.seek(0)
            audio_data = wav_buffer.read()
            
            logger.info(f"Generated {len(audio_data)} bytes of audio")
            return audio_data
            
        except Exception as e:
            logger.error(f"Error generating audio: {str(e)}")
            raise
    
    def _stream_audio(self, prompt: str) -> Generator[bytes, None, None]:
        """Stream audio chunks as they're generated."""
        logger.info(f"Streaming audio for prompt: {prompt[:50]}...")
        
        # Prepare request for Ollama
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": self.temperature,
                "top_p": self.top_p,
                "repeat_penalty": self.repeat_penalty
            }
        }
        
        try:
            # Create WAV header
            header_buffer = BytesIO()
            with wave.open(header_buffer, "wb") as wf:
                wf.setnchannels(1)  # Mono
                wf.setsampwidth(2)  # 16-bit
                wf.setframerate(self.sample_rate)
                wf.writeframes(b'')  # Write empty frame to create header
            
            header_buffer.seek(0)
            header_bytes = header_buffer.read()
            
            # Send header first
            yield header_bytes
            
            # Request streaming text from Ollama
            response = requests.post(
                self.api_url,
                json=payload,
                stream=True,
                timeout=self.api_timeout
            )
            
            if response.status_code != 200:
                logger.error(f"Ollama API request failed: {response.status_code}")
                return
            
            # Process the streaming response
            buffer = ""
            import numpy as np
            
            for line in response.iter_lines():
                if line:
                    try:
                        # Parse JSON response
                        data = json.loads(line)
                        
                        # Extract token
                        token = data.get("response", "")
                        buffer += token
                        
                        # Process buffer when it has enough content
                        if len(buffer) >= 4:  # Process small chunks
                            # Convert to audio
                            audio_samples = self.snac_model.generate_with_text(buffer)
                            
                            # Convert to int16 and get bytes
                            audio_int16 = (audio_samples * 32767).astype(np.int16)
                            audio_bytes = audio_int16.tobytes()
                            
                            # Reset buffer and yield the audio chunk
                            buffer = ""
                            yield audio_bytes
                        
                        # Check if done
                        if data.get("done", False):
                            # Process any remaining buffer
                            if buffer:
                                audio_samples = self.snac_model.generate_with_text(buffer)
                                audio_int16 = (audio_samples * 32767).astype(np.int16)
                                yield audio_int16.tobytes()
                            break
                            
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse JSON response: {line}")
                        continue
                    except Exception as e:
                        logger.error(f"Error processing token: {str(e)}")
                        continue
        
        except Exception as e:
            logger.error(f"Error in streaming audio: {str(e)}")
            raise
    
    def test_connection(self) -> Dict[str, str]:
        """Test connection to Ollama server."""
        try:
            # Simple test request
            response = requests.post(
                self.api_url,
                json={
                    "model": self.model_name,
                    "prompt": "Hello",
                    "stream": False
                },
                timeout=10
            )
            
            if response.status_code == 200:
                return {"status": "connected", "message": "Successfully connected to Ollama"}
            else:
                return {"status": "error", "message": f"Failed to connect: {response.status_code} - {response.text}"}
        
        except Exception as e:
            return {"status": "error", "message": f"Failed to connect: {str(e)}"} 