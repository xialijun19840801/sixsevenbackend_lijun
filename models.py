from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime

# Request Models
class JokeCreate(BaseModel):
    joke_setup: str
    joke_punchline: str
    joke_content: Optional[str] = ""
    default_audio_url: Optional[str] = ""
    audio_urls: Optional[List[Dict[str, str]]] = []
    scenarios: Optional[List[str]] = []
    age_range: Optional[List[str]] = []

# Response Models
class JokeResponse(BaseModel):
    joke_id: str
    joke_setup: str
    joke_punchline: str
    joke_content: Optional[str] = ""
    default_audio_url: Optional[str] = ""
    audio_urls: Optional[List[Dict[str, str]]] = []
    scenarios: Optional[List[str]] = []
    age_range: Optional[List[str]] = []
    emoji: Optional[str] = ""
    created_by_customer: bool
    creator_id: str
    created_at: Optional[datetime] = None
    random_val: Optional[float] = None

class JokeListResponse(BaseModel):
    jokes: List[JokeResponse]

class LoginResponse(BaseModel):
    message: str
    user_id: str
    user_email: str

class FavoriteResponse(BaseModel):
    message: str
    success: bool
    joke_id: str
    user_id: str

class DeleteJokeResponse(BaseModel):
    message: str
    success: bool
    joke_id: str
    user_id: str

class LikeDislikeResponse(BaseModel):
    message: str
    success: bool
    joke_id: str
    user_id: str

class GeminiJokeRequest(BaseModel):
    age_range: str  # e.g., "5-10", "10-15", "adult"
    scenario: str   # e.g., "school", "family", "animals"

class GeminiJokeItem(BaseModel):
    joke_setup: str
    joke_punchline: str
    joke_content: Optional[str] = ""
    emoji: Optional[str] = ""

class GeminiJokeResponse(BaseModel):
    jokes: List[GeminiJokeItem]

class JokeAudioRequest(BaseModel):
    joke_setup: str
    joke_punchline: str

class JokeAudioResponse(BaseModel):
    setup_audio: str  # Base64 encoded MP3
    punchline_audio: str  # Base64 encoded MP3
    setup_voice: str = "en-US-Neural2-F"
    punchline_voice: str = "en-US-Neural2-J"

class VoiceCreate(BaseModel):
    voice_id: str  # UUID
    creator_id: str
    voice_name: str
    voice_url: str

class VoiceResponse(BaseModel):
    voice_id: str
    creator_id: str
    voice_name: str
    voice_url: str
    created_at: Optional[datetime] = None

class JokeJarRequest(BaseModel):
    creator_id: str
    joke_id: str

class JokeJarResponse(BaseModel):
    message: str
    success: bool
    creator_id: str
    joke_id: str

class VoiceItem(BaseModel):
    voice_id: str
    voice_name: str

class VoiceListResponse(BaseModel):
    voices: List[VoiceItem]

