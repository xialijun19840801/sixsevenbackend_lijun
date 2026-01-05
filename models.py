from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# Request Models
class JokeCreate(BaseModel):
    joke_setup: str
    joke_punchline: str
    joke_content: Optional[str] = ""
    default_audio_id: Optional[str] = ""
    scenarios: Optional[List[str]] = []
    ages: Optional[List[int]] = []

# Response Models
class JokeResponse(BaseModel):
    joke_id: str
    joke_setup: str
    joke_punchline: str
    joke_content: Optional[str] = ""
    default_audio_id: Optional[str] = ""
    scenarios: Optional[List[str]] = []
    ages: Optional[List[int]] = []
    created_by_customer: bool
    creator_id: str
    created_at: Optional[datetime] = None

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

class GeminiJokeResponse(BaseModel):
    jokes: List[GeminiJokeItem]

