import requests
import os
import tempfile
import wave
import io
from typing import Optional, Tuple
from firebase.config import ELEVENLABS_API_KEY

class ElevenlabsService:
    """
    Service class for interacting with ElevenLabs API for voice cloning and text-to-speech.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the ElevenlabsService service.
        
        Args:
            api_key: ElevenLabs API key. If not provided, uses ELEVENLABS_API_KEY from environment.
        """
        self.api_key = api_key or ELEVENLABS_API_KEY
        if not self.api_key:
            raise ValueError("ElevenLabs API key is required. Set ELEVENLABS_API_KEY environment variable or pass it to __init__")
        
        self.base_url = "https://api.elevenlabs.io/v1"
        self.headers = {
            "xi-api-key": self.api_key
        }
    
    def _download_voice(self, firebase_voice_url: str) -> bytes:
        """
        Download voice file from Firebase URL.
        
        Args:
            firebase_voice_url: URL of the voice file in Firebase Storage
        
        Returns:
            bytes: The downloaded voice file as bytes
        
        Raises:
            Exception: If download fails
        """
        try:
            print(f"[ElevenLabs] Downloading voice from: {firebase_voice_url}")
            response = requests.get(firebase_voice_url, timeout=30)
            response.raise_for_status()
            print(f"[ElevenLabs] Successfully downloaded voice file ({len(response.content)} bytes)")
            return response.content
        except Exception as e:
            print(f"[ElevenLabs] Error downloading voice: {str(e)}")
            raise
    
    def _clone_voice(self, voice_data: bytes, voice_name: str = "cloned_voice") -> str:
        """
        Clone a voice using ElevenLabs API.
        
        Args:
            voice_data: The voice file data as bytes
            voice_name: Name for the cloned voice
        
        Returns:
            str: The voice_id of the cloned voice
        
        Raises:
            Exception: If voice cloning fails
        """
        try:
            print(f"[ElevenLabs] Cloning voice with name: {voice_name}")
            
            # Create a temporary file to upload
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
                temp_file.write(voice_data)
                temp_file_path = temp_file.name
            
            try:
                # Prepare the request for voice cloning
                url = f"{self.base_url}/voices/add"
                
                # ElevenLabs API expects files as a list in multipart form data
                with open(temp_file_path, 'rb') as voice_file:
                    files = {
                        'files': (f'{voice_name}.mp3', voice_file, 'audio/mpeg')
                    }
                    
                    data = {
                        'name': voice_name,
                        'description': f'Cloned voice from Firebase: {voice_name}'
                    }
                    
                    response = requests.post(
                        url,
                        headers=self.headers,
                        files=files,
                        data=data,
                        timeout=60
                    )
                    response.raise_for_status()
                    
                    result = response.json()
                    voice_id = result.get('voice_id')
                    
                    if not voice_id:
                        raise ValueError("Voice cloning succeeded but no voice_id returned")
                    
                    print(f"[ElevenLabs] Successfully cloned voice. Voice ID: {voice_id}")
                    return voice_id
                
            finally:
                # Clean up temporary file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                    
        except Exception as e:
            print(f"[ElevenLabs] Error cloning voice: {str(e)}")
            raise
    
    def _generate_audio(self, text: str, voice_id: str) -> bytes:
        """
        Generate audio from text using the cloned voice.
        
        Args:
            text: The text to convert to speech
            voice_id: The ElevenLabs voice ID to use
        
        Returns:
            bytes: The generated audio in WAV format
        
        Raises:
            Exception: If audio generation fails
        """
        try:
            print(f"[ElevenLabs] Generating audio for text (length: {len(text)}) with voice_id: {voice_id}")
            
            url = f"{self.base_url}/text-to-speech/{voice_id}"
            
            payload = {
                "text": text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75
                }
            }
            
            # Request WAV format explicitly
            params = {
                "output_format": "pcm_44100"  # WAV format with 44.1kHz sample rate
            }
            
            response = requests.post(
                url,
                headers={**self.headers, "Content-Type": "application/json"},
                json=payload,
                params=params,
                timeout=60
            )
            response.raise_for_status()
            
            # Get audio data
            audio_data = response.content
            
            # Convert PCM to WAV format if needed
            # The response might be raw PCM, so we'll wrap it in WAV format
            audio_data = self._convert_pcm_to_wav(audio_data)
            
            print(f"[ElevenLabs] Successfully generated audio ({len(audio_data)} bytes)")
            return audio_data
            
        except Exception as e:
            print(f"[ElevenLabs] Error generating audio: {str(e)}")
            raise
    
    def _convert_pcm_to_wav(self, pcm_data: bytes, sample_rate: int = 44100, channels: int = 1, sample_width: int = 2) -> bytes:
        """
        Convert PCM audio data to WAV format.
        
        Args:
            pcm_data: Raw PCM audio data
            sample_rate: Sample rate in Hz (default: 44100)
            channels: Number of audio channels (default: 1 for mono)
            sample_width: Sample width in bytes (default: 2 for 16-bit)
        
        Returns:
            bytes: WAV formatted audio data
        """
        try:
            # Create WAV file in memory
            wav_buffer = io.BytesIO()
            
            with wave.open(wav_buffer, 'wb') as wav_file:
                wav_file.setnchannels(channels)
                wav_file.setsampwidth(sample_width)
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(pcm_data)
            
            wav_buffer.seek(0)
            return wav_buffer.read()
            
        except Exception as e:
            print(f"[ElevenLabs] Error converting PCM to WAV: {str(e)}")
            # If conversion fails, return original data
            return pcm_data
    
    def read_joke_with_the_voice(self, firebase_voice_url: str, joke_text: str) -> Tuple[bytes, str]:
        """
        Download voice, clone it, and generate audio for the joke text.
        
        Args:
            firebase_voice_url: URL of the voice file in Firebase Storage
            joke_text: The joke text to convert to speech
        
        Returns:
            Tuple[bytes, str]: (audio_data in WAV format, cloned_voice_id)
        
        Raises:
            Exception: If any step fails
        """
        try:
            # Step 1: Download the voice
            voice_data = self._download_voice(firebase_voice_url)
            
            # Step 2: Clone the voice and get voice_id
            # Extract a name from the URL or use a default
            voice_name = os.path.basename(firebase_voice_url).split('.')[0] or "cloned_voice"
            voice_id = self._clone_voice(voice_data, voice_name)
            
            # Step 3: Generate audio with the cloned voice
            audio_data = self._generate_audio(joke_text, voice_id)
            
            return audio_data, voice_id
            
        except Exception as e:
            print(f"[ElevenLabs] Error in read_joke_with_the_voice: {str(e)}")
            raise

