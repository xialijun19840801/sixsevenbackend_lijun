from fastapi import APIRouter, HTTPException, Depends, status, BackgroundTasks
from pydantic import BaseModel
from models import JokeCreate, JokeResponse, JokeListResponse, LoginResponse, FavoriteResponse, DeleteJokeResponse, LikeDislikeResponse, GeminiJokeRequest, GeminiJokeResponse, JokeAudioRequest, JokeAudioResponse, VoiceCreate, VoiceResponse
from firebase_service import FirebaseService
from firebase.auth import get_current_user_id, get_optional_user_id
from firebase_admin import auth
from gemini_service import GeminiService
from typing import Optional
from datetime import datetime
import random
import uuid
import threading

router = APIRouter()

class LoginRequest(BaseModel):
    token: str

class FavoriteRequest(BaseModel):
    joke_id: str

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    Verify Firebase ID token and return user information
    This endpoint expects a Firebase ID token in the request body
    """
    try:
        decoded_token = auth.verify_id_token(request.token)
        user_id = decoded_token.get('uid')
        # Email is usually present, but may be empty for some Google accounts
        # or if user hasn't verified their email
        user_email = decoded_token.get('email', '') or decoded_token.get('name', '') or 'No email'
        
        return LoginResponse(
            message="Login successful",
            user_id=user_id,
            user_email=user_email
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}"
        )

@router.post("/jokes", response_model=JokeResponse)
async def add_joke(
    joke: JokeCreate,
    user_id: str = Depends(get_current_user_id)
):
    """
    Add a new joke (requires authentication)
    """
    try:
        # Add joke to Firestore and user's creation_history
        joke_id = FirebaseService.add_to_user_created_jokes(
            joke_setup=joke.joke_setup,
            joke_punchline=joke.joke_punchline,
            creator_id=user_id,
            joke_content=joke.joke_content,
            default_audio_url=joke.default_audio_url,
            audio_urls=joke.audio_urls,
            scenarios=joke.scenarios,
            age_range=joke.age_range
        )
        
        # Get the created joke to return
        jokes = FirebaseService.get_all_jokes()
        created_joke = next((j for j in jokes if j.joke_id == joke_id), None)
        
        if not created_joke:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve created joke"
            )
        
        return created_joke
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add joke: {str(e)}"
        )

@router.get("/jokes", response_model=JokeListResponse)
async def get_all_jokes():
    """
    Get all jokes (no authentication required)
    """
    try:
        jokes = FirebaseService.get_all_jokes()
        return JokeListResponse(jokes=jokes)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get jokes: {str(e)}"
        )

@router.get("/users/{user_id}/favorites", response_model=JokeListResponse)
async def get_favorite_jokes(
    user_id: str,
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Get all favorite jokes for a user (requires authentication)
    User can only view their own favorites
    """
    try:
        # Verify user is viewing their own favorites
        if user_id != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own favorites"
            )
        
        # Get favorite jokes
        jokes = FirebaseService.get_favorite_jokes(user_id)
        return JokeListResponse(jokes=jokes)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get favorite jokes: {str(e)}"
        )

@router.get("/users/{user_id}/created-jokes", response_model=JokeListResponse)
async def get_user_created_jokes(
    user_id: str,
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Get all jokes created by a user (requires authentication)
    User can only view their own created jokes
    """
    try:
        # Verify user is viewing their own created jokes
        if user_id != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own created jokes"
            )
        
        # Get created jokes
        jokes = FirebaseService.get_user_created_jokes(user_id)
        return JokeListResponse(jokes=jokes)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get created jokes: {str(e)}"
        )

@router.post("/users/{user_id}/favorites", response_model=FavoriteResponse)
async def add_to_favorite_jokes(
    user_id: str,
    request: FavoriteRequest,
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Add a joke to user's favorites (requires authentication)
    User can only add to their own favorites
    """
    try:
        # Verify user is adding to their own favorites
        if user_id != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only add to your own favorites"
            )
        
        # Verify joke exists (direct check is more efficient)
        if not FirebaseService.joke_id_exists(request.joke_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Joke with ID {request.joke_id} not found"
            )
        
        # Add to favorites
        added = FirebaseService.add_to_favorite_jokes(user_id, request.joke_id)
        
        if added:
            return FavoriteResponse(
                message="Joke added to favorites",
                success=True,
                joke_id=request.joke_id,
                user_id=user_id
            )
        else:
            return FavoriteResponse(
                message="Joke is already in favorites",
                success=False,
                joke_id=request.joke_id,
                user_id=user_id
            )
    except HTTPException:
        raise
    except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to add to favorites: {str(e)}"
            )

@router.delete("/users/{user_id}/created-jokes/{joke_id}", response_model=DeleteJokeResponse)
async def delete_user_created_joke(
    user_id: str,
    joke_id: str,
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Delete a joke from user's created jokes (requires authentication)
    User can only delete their own created jokes
    """
    try:
        # Verify user is deleting their own joke
        if user_id != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own created jokes"
            )
        
        # Verify joke exists (direct check is more efficient)
        if not FirebaseService.joke_id_exists(joke_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Joke with ID {joke_id} not found"
            )
        
        # Remove from user's creation_history
        deleted = FirebaseService.delete_user_created_joke(user_id, joke_id)
        
        if deleted:
            return DeleteJokeResponse(
                message="Joke removed from your created jokes",
                success=True,
                joke_id=joke_id,
                user_id=user_id
            )
        else:
            return DeleteJokeResponse(
                message="Joke was not in your created jokes list",
                success=False,
                joke_id=joke_id,
                user_id=user_id
            )
    except HTTPException:
        raise
    except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete joke: {str(e)}"
            )

@router.delete("/users/{user_id}/favorites/{joke_id}", response_model=FavoriteResponse)
async def delete_favorite_jokes(
    user_id: str,
    joke_id: str,
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Delete a joke from user's favorites (requires authentication)
    User can only delete from their own favorites
    """
    try:
        # Verify user is deleting from their own favorites
        if user_id != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete from your own favorites"
            )
        
        # Verify joke exists (direct check is more efficient)
        if not FirebaseService.joke_id_exists(joke_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Joke with ID {joke_id} not found"
            )
        
        # Remove from favorites
        deleted = FirebaseService.delete_favorite_jokes(user_id, joke_id)
        
        if deleted:
            return FavoriteResponse(
                message="Joke removed from favorites",
                success=True,
                joke_id=joke_id,
                user_id=user_id
            )
        else:
            return FavoriteResponse(
                message="Joke was not in your favorites",
                success=False,
                joke_id=joke_id,
                user_id=user_id
            )
    except HTTPException:
        raise
    except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete from favorites: {str(e)}"
            )

@router.get("/users/{user_id}/liked-jokes", response_model=JokeListResponse)
async def get_liked_jokes(
    user_id: str,
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Get all liked jokes for a user (requires authentication)
    User can only view their own liked jokes
    """
    try:
        # Verify user is viewing their own liked jokes
        if user_id != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own liked jokes"
            )

        # Get liked jokes
        jokes = FirebaseService.get_liked_jokes(user_id)
        return JokeListResponse(jokes=jokes)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get liked jokes: {str(e)}"
        )

@router.get("/users/{user_id}/disliked-jokes", response_model=JokeListResponse)
async def get_disliked_jokes(
    user_id: str,
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Get all disliked jokes for a user (requires authentication)
    User can only view their own disliked jokes
    """
    try:
        # Verify user is viewing their own disliked jokes
        if user_id != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own disliked jokes"
            )

        # Get disliked jokes
        jokes = FirebaseService.get_disliked_jokes(user_id)
        return JokeListResponse(jokes=jokes)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get disliked jokes: {str(e)}"
        )

@router.post("/users/{user_id}/like-history/{joke_id}", response_model=LikeDislikeResponse)
async def add_to_user_liked_history(
    user_id: str,
    joke_id: str,
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Add joke to user's like_history and remove from dislike_history (requires authentication)
    User can only modify their own like history
    """
    try:
        # Verify user is modifying their own history
        if user_id != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only modify your own like history"
            )
        
        # Verify joke exists (direct check is more efficient)
        if not FirebaseService.joke_id_exists(joke_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Joke with ID {joke_id} not found"
            )
        
        # Add to like_history and remove from dislike_history
        success = FirebaseService.add_to_user_liked_history(user_id, joke_id)
        
        return LikeDislikeResponse(
            message="Joke added to like history",
            success=success,
            joke_id=joke_id,
            user_id=user_id
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add to like history: {str(e)}"
        )

@router.post("/users/{user_id}/dislike-history/{joke_id}", response_model=LikeDislikeResponse)
async def add_to_user_dislike_history(
    user_id: str,
    joke_id: str,
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Add joke to user's dislike_history and remove from like_history (requires authentication)
    User can only modify their own dislike history
    """
    try:
        # Verify user is modifying their own history
        if user_id != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only modify your own dislike history"
            )
        
        # Verify joke exists (direct check is more efficient)
        if not FirebaseService.joke_id_exists(joke_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Joke with ID {joke_id} not found"
            )
        
        # Add to dislike_history and remove from like_history
        success = FirebaseService.add_to_user_disliked_history(user_id, joke_id)
        
        return LikeDislikeResponse(
            message="Joke added to dislike history",
            success=success,
            joke_id=joke_id,
            user_id=user_id
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add to dislike history: {str(e)}"
        )

@router.post("/jokes/generate", response_model=GeminiJokeResponse)
async def generate_jokes_with_gemini(
    request: GeminiJokeRequest,
    current_user_id: Optional[str] = Depends(get_optional_user_id)
):
    """
    Generate 10 jokes using Gemini AI based on age range and scenario.
    If authenticated, personalizes jokes based on user's liked/disliked history.
    Works without authentication for generic joke generation.
    """
    try:
        liked_jokes_dict = None
        disliked_jokes_dict = None
        
        # If user is authenticated, get their preferences
        if current_user_id:
            # Get user's liked and disliked jokes for personalization
            liked_jokes = FirebaseService.get_liked_jokes(current_user_id)
            disliked_jokes = FirebaseService.get_disliked_jokes(current_user_id)
            
            # Convert to dictionaries for Gemini service
            if liked_jokes:
                liked_jokes_dict = [
                    {
                        "joke_setup": joke.joke_setup,
                        "joke_punchline": joke.joke_punchline,
                        "joke_content": joke.joke_content
                    }
                    for joke in liked_jokes
                ]
            
            if disliked_jokes:
                disliked_jokes_dict = [
                    {
                        "joke_setup": joke.joke_setup,
                        "joke_punchline": joke.joke_punchline,
                        "joke_content": joke.joke_content
                    }
                    for joke in disliked_jokes
                ]
        
        # Generate jokes using Gemini with user preferences (if available)
        jokes = GeminiService.generate_jokes(
            age_range=request.age_range,
            scenario=request.scenario,
            num_jokes=10,
            liked_jokes=liked_jokes_dict,
            disliked_jokes=disliked_jokes_dict
        )
        
        return GeminiJokeResponse(jokes=jokes)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate jokes: {str(e)}"
        )

class GetJokesRequest(BaseModel):
    age_range: str
    scenario: str
    num_jokes: Optional[int] = 5  # Default to 5 jokes if not provided

@router.post("/users/{user_id}/jokes/get", response_model=JokeListResponse)
async def get_jokes(
    user_id: str,
    request: GetJokesRequest,
    background_tasks: BackgroundTasks,
    current_user_id: Optional[str] = Depends(get_optional_user_id)
):
    """
    Get jokes for a user based on age range and scenario.
    Filters out liked, disliked, and favorited jokes.
    If not enough jokes remain, generates new ones from Gemini.
    """
    try:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting to get jokes for user {user_id}, num_jokes: {request.num_jokes if request.num_jokes else 5}, age_range: {request.age_range}, scenario: {request.scenario}")
        
        # Verify user is accessing their own data
        if current_user_id and user_id != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only get jokes for your own account"
            )
        
        # Get user's liked, disliked, and favorite joke IDs
        user_joke_ids = FirebaseService.get_user_joke_ids(user_id)
        favorite_joke_ids = user_joke_ids.get('favorite_joke_ids', [])
        liked_joke_ids = user_joke_ids.get('liked_joke_ids', [])
        disliked_joke_ids = user_joke_ids.get('disliked_joke_ids', [])
        
        # Create set of joke IDs to filter out (combine all three lists)
        excluded_joke_ids = set(favorite_joke_ids) | set(liked_joke_ids) | set(disliked_joke_ids)
        
        # Get random jokes from database that match age_range and scenario
        num_jokes = request.num_jokes if request.num_jokes and request.num_jokes > 0 else 5
        all_jokes = FirebaseService.get_random_jokes(
            limit=num_jokes * 5,  # Get more to ensure we have enough after filtering
            age_range=request.age_range,
            scenario=request.scenario
        )
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Retrieved {len(all_jokes)} random jokes from database")
        
        # Filter out excluded jokes
        remaining_jokes = [joke for joke in all_jokes if joke.joke_id not in excluded_joke_ids]
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Remaining jokes: {len(remaining_jokes)}")
        
        result_jokes = []
        
        # Get 1 random liked joke (avoids full database scan)
        liked_jokes = FirebaseService.get_random_liked_jokes(user_id, limit=1)
        
        # Calculate how many jokes to get from remaining (num_jokes - 1)
        num_from_remaining = max(0, num_jokes - 1)
        
        # Check if remaining_jokes is more than 70% of all_jokes
        if len(all_jokes) > 0 and len(remaining_jokes) > 0.7 * len(all_jokes) and len(remaining_jokes) > num_from_remaining:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Returning {num_jokes} jokes: {num_from_remaining} from remaining, 1 from liked jokes")
            
            # Get num_jokes - 1 from remaining jokes
            selected_remaining = []
            if num_from_remaining > 0:
                selected_remaining = random.sample(remaining_jokes, min(num_from_remaining, len(remaining_jokes)))
                result_jokes.extend(selected_remaining)
            
            # Get 1 from liked jokes (if available)
            if len(liked_jokes) > 0:
                selected_liked = random.sample(liked_jokes, min(1, len(liked_jokes)))
                result_jokes.extend(selected_liked)
            
            # If we still need more (e.g., no liked jokes), fill from remaining
            while len(result_jokes) < num_jokes:
                remaining_ids = {j.joke_id for j in selected_remaining}
                more_remaining = [j for j in remaining_jokes if j.joke_id not in remaining_ids]
                if more_remaining:
                    selected_joke = random.choice(more_remaining)
                    result_jokes.append(selected_joke)
                    selected_remaining.append(selected_joke)
                else:
                    break
            
            # Return exactly num_jokes jokes
            return JokeListResponse(jokes=result_jokes[:num_jokes])
        else:
            
            # Not enough jokes remaining, generate from Gemini
            try:
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Getting {num_jokes} jokes from Gemini for user {user_id}, age_range: {request.age_range}, scenario: {request.scenario}, better to get new jokes which user has not liked or disliked.")
                
                # Get random liked and disliked jokes for Gemini context (avoids full database scan)
                liked_jokes_for_gemini = FirebaseService.get_random_liked_jokes(user_id, limit=10)
                disliked_jokes_for_gemini = FirebaseService.get_random_disliked_jokes(user_id, limit=10)
                
                gemini_jokes = GeminiService.generate_jokes(
                    age_range=request.age_range,
                    scenario=request.scenario,
                    num_jokes=num_jokes,
                    liked_jokes=[
                        {
                            "joke_setup": joke.joke_setup,
                            "joke_punchline": joke.joke_punchline,
                            "joke_content": joke.joke_content
                        }
                        for joke in liked_jokes_for_gemini
                    ] if liked_jokes_for_gemini else None,
                    disliked_jokes=[
                        {
                            "joke_setup": joke.joke_setup,
                            "joke_punchline": joke.joke_punchline,
                            "joke_content": joke.joke_content
                        }
                        for joke in disliked_jokes_for_gemini
                    ] if disliked_jokes_for_gemini else None
                )
                
                # Convert Gemini jokes to JokeResponse format
                result_jokes = []
                jokes_to_save = []
                for gemini_joke in gemini_jokes:
                    # Generate UUID for joke_id
                    joke_id = str(uuid.uuid4())
                    
                    # Create a temporary JokeResponse with UUID for joke_id
                    joke_response = JokeResponse(
                        joke_id=joke_id,  # Generate UUID for new jokes
                        joke_setup=gemini_joke.joke_setup,
                        joke_punchline=gemini_joke.joke_punchline,
                        joke_content=gemini_joke.joke_content,
                        default_audio_url="",
                        audio_urls=[],
                        scenarios=[request.scenario] if request.scenario else [],
                        age_range=[request.age_range] if request.age_range else [],
                        created_by_customer=False,
                        creator_id="gemini",
                        created_at=datetime.utcnow()
                    )
                    result_jokes.append(joke_response)
                    
                    # Prepare joke data for saving with joke_id
                    jokes_to_save.append({
                        "joke_id": joke_id,  # Include the UUID so it's used when saving
                        "joke_setup": gemini_joke.joke_setup,
                        "joke_punchline": gemini_joke.joke_punchline,
                        "joke_content": gemini_joke.joke_content,
                        "scenarios": [request.scenario] if request.scenario else [],
                        "age_range": [request.age_range] if request.age_range else []
                    })
                
                # Run async save in background
                background_tasks.add_task(
                    FirebaseService.save_jokes_async,
                    jokes_to_save,
                    "gemini"
                )
                
                return JokeListResponse(jokes=result_jokes)
                
            except Exception as gemini_error:
                # If Gemini fails, return whatever we have
                if remaining_jokes:
                    return JokeListResponse(jokes=remaining_jokes[:10])
                else:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"Failed to generate jokes from Gemini: {str(gemini_error)}"
                    )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get jokes: {str(e)}"
        )

        
@router.get("/jokes/{joke_id}/audio")
async def get_audio_for_joke(joke_id: str, background_tasks: BackgroundTasks):
    """
    Get the audio URL for a joke.
    First tries to get the default audio URL from the joke.
    If not found, generates audio using Gemini TTS.
    Returns the audio URL and saves it asynchronously to the joke document.
    """
    try:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Getting audio for joke {joke_id}")
        # First, try to get the default audio URL from the joke
        audio_url = FirebaseService.get_default_audio(joke_id)
        
        if audio_url:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Got default audio for joke {joke_id}: {audio_url}")
            return {"audio_url": audio_url, "joke_id": joke_id}
        
        # If no audio URL found, get the joke to generate audio
        joke = FirebaseService.get_joke_by_id(joke_id)
        if not joke:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Joke with ID {joke_id} not found"
            )
        
        # Generate audio using Gemini TTS (this now handles upload and DB save)
        result = GeminiService.generate_audio_for_joke(joke_id, joke.joke_setup, joke.joke_punchline)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate audio for joke"
            )
        
        # Unpack result (audio_url, audio_size)
        audio_url, audio_size = result
        
        # Save the audio URL and metadata asynchronously using FirebaseService
        # is_default=True since this is the default audio for the joke
        background_tasks.add_task(
            FirebaseService.save_audio_url_async,
            joke_id,
            audio_url,
            audio_size,
            True  # is_default=True
        )
        
        return {"audio_url": audio_url, "joke_id": joke_id}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get audio for joke: {str(e)}"
        )

@router.post("/voices", response_model=VoiceResponse)
async def create_voice(
    voice: VoiceCreate,
    user_id: str = Depends(get_current_user_id)
):
    """
    Create a new voice and save it to the voices collection.
    Also updates the user's voices array.
    Requires authentication.
    """
    try:
        # Verify that the creator_id matches the authenticated user
        if voice.creator_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Creator ID must match authenticated user"
            )
        
        # Save voice to voices collection and update user
        voice_data = FirebaseService.add_voice(
            voice_id=voice.voice_id,
            creator_id=voice.creator_id,
            voice_name=voice.voice_name,
            voice_url=voice.voice_url
        )
        
        return VoiceResponse(
            voice_id=voice_data['voice_id'],
            creator_id=voice_data['creator_id'],
            voice_name=voice_data['voice_name'],
            voice_url=voice_data['voice_url'],
            created_at=voice_data.get('created_at')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create voice: {str(e)}"
        )
