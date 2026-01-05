from fastapi import APIRouter, HTTPException, Depends, status, BackgroundTasks
from pydantic import BaseModel
from models import JokeCreate, JokeResponse, JokeListResponse, LoginResponse, FavoriteResponse, DeleteJokeResponse, LikeDislikeResponse, GeminiJokeRequest, GeminiJokeResponse
from firebase_service import FirebaseService
from firebase.auth import get_current_user_id, get_optional_user_id
from firebase_admin import auth
from gemini_service import GeminiService
from typing import Optional
from datetime import datetime
import random

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
            default_audio_id=joke.default_audio_id,
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
        
        # Verify joke exists
        jokes = FirebaseService.get_all_jokes()
        joke_exists = any(j.joke_id == request.joke_id for j in jokes)
        
        if not joke_exists:
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
        
        # Verify joke exists and belongs to user
        jokes = FirebaseService.get_all_jokes()
        joke = next((j for j in jokes if j.joke_id == joke_id), None)
        
        if not joke:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Joke with ID {joke_id} not found"
            )
        
        # Verify joke was created by this user
        if joke.creator_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete jokes you created"
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
        
        # Verify joke exists
        jokes = FirebaseService.get_all_jokes()
        joke_exists = any(j.joke_id == joke_id for j in jokes)
        
        if not joke_exists:
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
        
        # Verify joke exists
        jokes = FirebaseService.get_all_jokes()
        joke_exists = any(j.joke_id == joke_id for j in jokes)
        
        if not joke_exists:
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
        
        # Verify joke exists
        jokes = FirebaseService.get_all_jokes()
        joke_exists = any(j.joke_id == joke_id for j in jokes)
        
        if not joke_exists:
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
        # Verify user is accessing their own data
        if current_user_id and user_id != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only get jokes for your own account"
            )
        
        # Get user's liked, disliked, and favorite joke IDs
        liked_jokes = FirebaseService.get_liked_jokes(user_id)
        disliked_jokes = FirebaseService.get_disliked_jokes(user_id)
        favorite_jokes = FirebaseService.get_favorite_jokes(user_id)
        
        # Create sets of joke IDs to filter out
        excluded_joke_ids = set()
        for joke in liked_jokes:
            excluded_joke_ids.add(joke.joke_id)
        for joke in disliked_jokes:
            excluded_joke_ids.add(joke.joke_id)
        for joke in favorite_jokes:
            excluded_joke_ids.add(joke.joke_id)
        
        # Get 20 random jokes from database
        all_jokes = FirebaseService.get_random_jokes(limit=20)
        
        # Filter out excluded jokes
        remaining_jokes = [joke for joke in all_jokes if joke.joke_id not in excluded_joke_ids]
        
        result_jokes = []
        
        if len(remaining_jokes) >= 10:
            # Get 8 from remaining jokes
            selected_remaining = random.sample(remaining_jokes, min(8, len(remaining_jokes)))
            result_jokes.extend(selected_remaining)
            
            # Get 2 from liked jokes (if available)
            if len(liked_jokes) > 0:
                selected_liked = random.sample(liked_jokes, min(2, len(liked_jokes)))
                result_jokes.extend(selected_liked)
            
            # If we still need more to reach 10, fill from remaining
            while len(result_jokes) < 10 and len(remaining_jokes) > len(selected_remaining):
                remaining_ids = {j.joke_id for j in selected_remaining}
                more_remaining = [j for j in remaining_jokes if j.joke_id not in remaining_ids]
                if more_remaining:
                    result_jokes.append(random.choice(more_remaining))
                    selected_remaining.append(result_jokes[-1])
                else:
                    break
            
            # Return exactly 10 jokes
            return JokeListResponse(jokes=result_jokes[:10])
        else:
            # Not enough jokes remaining, generate from Gemini
            try:
                gemini_jokes = GeminiService.generate_jokes(
                    age_range=request.age_range,
                    scenario=request.scenario,
                    num_jokes=10,
                    liked_jokes=[
                        {
                            "joke_setup": joke.joke_setup,
                            "joke_punchline": joke.joke_punchline,
                            "joke_content": joke.joke_content
                        }
                        for joke in liked_jokes[:5]
                    ] if liked_jokes else None,
                    disliked_jokes=[
                        {
                            "joke_setup": joke.joke_setup,
                            "joke_punchline": joke.joke_punchline,
                            "joke_content": joke.joke_content
                        }
                        for joke in disliked_jokes[:5]
                    ] if disliked_jokes else None
                )
                
                # Convert Gemini jokes to JokeResponse format
                result_jokes = []
                for gemini_joke in gemini_jokes:
                    # Create a temporary JokeResponse (without joke_id since not saved yet)
                    joke_response = JokeResponse(
                        joke_id="",  # Will be empty for new jokes
                        joke_setup=gemini_joke.joke_setup,
                        joke_punchline=gemini_joke.joke_punchline,
                        joke_content=gemini_joke.joke_content,
                        default_audio_id="",
                        scenarios=[request.scenario] if request.scenario else [],
                        age_range=[],
                        created_by_customer=False,
                        creator_id="gemini",
                        created_at=datetime.utcnow()
                    )
                    result_jokes.append(joke_response)
                
                # Save jokes to database asynchronously in background
                jokes_to_save = [
                    {
                        "joke_setup": joke.joke_setup,
                        "joke_punchline": joke.joke_punchline,
                        "joke_content": joke.joke_content,
                        "scenarios": [request.scenario] if request.scenario else [],
                        "age_range": []
                    }
                    for joke in gemini_jokes
                ]
                
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

