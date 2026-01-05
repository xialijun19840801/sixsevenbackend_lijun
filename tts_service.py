from google.cloud import texttospeech
from typing import Tuple
import base64

class TTSService:
    """Service for generating text-to-speech audio with different voices"""
    
    def __init__(self):
        """Initialize the Text-to-Speech client"""
        self.client = texttospeech.TextToSpeechClient()
    
    def generate_joke_audio(self, setup: str, punchline: str) -> Tuple[str, str]:
        """
        Generate audio for a joke using different voices:
        - Setup: Woman's voice (en-US-Neural2-F)
        - Punchline: Child-like voice (en-US-Neural2-J with higher pitch)
        
        Returns:
            Tuple[str, str]: (setup_audio_b64, punchline_audio_b64) as base64-encoded MP3 strings
        """
        # Generate setup audio with woman's voice
        setup_audio = self._synthesize_speech(
            text=setup,
            voice_name="en-US-Neural2-F",  # Woman's voice
            pitch=0.0,  # Normal pitch
            speaking_rate=1.0  # Normal speed
        )
        
        # Generate punchline audio with child-like voice (higher pitch, slightly faster)
        punchline_audio = self._synthesize_speech(
            text=punchline,
            voice_name="en-US-Neural2-J",  # Higher-pitched, child-like voice
            pitch=4.0,  # Higher pitch for child-like effect
            speaking_rate=1.1  # Slightly faster for funnier effect
        )
        
        # Encode audio as base64 for JSON response
        setup_audio_b64 = base64.b64encode(setup_audio).decode('utf-8')
        punchline_audio_b64 = base64.b64encode(punchline_audio).decode('utf-8')
        
        return setup_audio_b64, punchline_audio_b64
    
    def _synthesize_speech(
        self,
        text: str,
        voice_name: str,
        pitch: float = 0.0,
        speaking_rate: float = 1.0
    ) -> bytes:
        """
        Synthesize speech from text using specified voice and parameters
        
        Args:
            text: Text to synthesize
            voice_name: Voice name (e.g., "en-US-Neural2-F")
            pitch: Pitch adjustment in semitones (-20.0 to 20.0)
            speaking_rate: Speaking rate (0.25 to 4.0)
        
        Returns:
            bytes: Audio content as MP3
        """
        # Configure the voice
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            name=voice_name,
        )
        
        # Configure the audio format
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            pitch=pitch,
            speaking_rate=speaking_rate
        )
        
        # Perform the text-to-speech request
        synthesis_input = texttospeech.SynthesisInput(text=text)
        response = self.client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )
        
        return response.audio_content

