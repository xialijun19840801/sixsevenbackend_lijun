from firebase.firebase_init import get_firestore, get_storage_bucket
from models import JokeResponse
from typing import List, Optional, Dict
from datetime import datetime
from firebase_admin.firestore import ArrayUnion
import random
import threading

def _get_db():
    """Lazy initialization of Firestore client"""
    return get_firestore()

class FirebaseService:
    
    @staticmethod
    def _normalize_audio_urls(audio_urls_data):
        """
        Normalize audio_urls from old format (list of strings) to new format (list of dicts).
        Handles backward compatibility.
        
        Args:
            audio_urls_data: Can be a list of strings (old format) or list of dicts (new format)
        
        Returns:
            List of dicts with format [{"voice_id": str, "audio_url": str}, ...]
        """
        if not audio_urls_data:
            return []
        
        normalized = []
        for item in audio_urls_data:
            if isinstance(item, str):
                # Old format: string -> convert to dict with default voice_id
                normalized.append({"voice_id": "default", "audio_url": item})
            elif isinstance(item, dict):
                # New format: already a dict
                normalized.append(item)
            else:
                # Skip invalid entries
                continue
        
        return normalized
    
    @staticmethod
    def add_to_user_created_jokes(
        joke_setup: str,
        joke_punchline: str,
        creator_id: str,
        joke_content: Optional[str] = "",
        default_audio_url: Optional[str] = "",
        audio_urls: Optional[List[Dict[str, str]]] = None,
        scenarios: Optional[List[str]] = None,
        age_range: Optional[List[str]] = None
    ) -> str:
        """Add a new joke to Firestore and add it to user's creation_history"""
        db = _get_db()
        joke_data = {
            'joke_setup': joke_setup,
            'joke_punchline': joke_punchline,
            'joke_content': joke_content,
            'default_audio_url': default_audio_url,
            'audio_urls': audio_urls or [],
            'scenarios': scenarios or [],
            'age_range': age_range or [],
            'created_by_customer': True,
            'creator_id': creator_id,
            'created_at': datetime.utcnow(),
            'random_val': random.random()
        }
        
        # Add joke to jokes collection
        # add() returns (timestamp, DocumentReference)
        _, doc_ref = db.collection('jokes').add(joke_data)
        joke_id = doc_ref.id

        # Add joke_id to user's creation_history
        user_ref = db.collection('users').document(creator_id)
        user_doc = user_ref.get()

        if not user_doc.exists:
            # Create user document if it doesn't exist
            user_data = {
                'user_display_name': '',
                'user_email': '',
                'country': '',
                'favorites': [],
                'like_history': [],
                'dislike_history': [],
                'creation_history': [joke_id],
                'joke_jar': [],
                'voices': [],
                'settings': {},
                'age_range': '',
                'scenario': '',
                'voice_to_use': '',
                'created_at': datetime.utcnow()
            }
            user_ref.set(user_data)
        else:
            # Update existing user document
            user_data = user_doc.to_dict()
            creation_history = user_data.get('creation_history', [])
            if joke_id not in creation_history:
                creation_history.append(joke_id)
                user_ref.update({'creation_history': creation_history})

        return joke_id

    @staticmethod
    def get_all_jokes() -> List[JokeResponse]:
        """Get all jokes from Firestore"""
        db = _get_db()
        jokes_ref = db.collection('jokes')
        docs = jokes_ref.order_by('created_at', direction='DESCENDING').stream()

        jokes = []
        for doc in docs:
            data = doc.to_dict()
            # Convert Firestore timestamp to datetime if needed
            created_at = data.get('created_at')
            if hasattr(created_at, 'timestamp'):
                created_at = datetime.fromtimestamp(created_at.timestamp())

            joke = JokeResponse(
                joke_id=doc.id,
                joke_setup=data.get('joke_setup', ''),
                joke_punchline=data.get('joke_punchline', ''),
                joke_content=data.get('joke_content', ''),
                default_audio_url=data.get('default_audio_url', data.get('default_audio_id', '')),  # Support old field name for backward compatibility
                audio_urls=FirebaseService._normalize_audio_urls(data.get('audio_urls', data.get('audio_ids', []))),  # Support old field name for backward compatibility
                scenarios=data.get('scenarios', []),
                age_range=data.get('age_range', data.get('ages', [])),  # Support both old and new field names
                created_by_customer=data.get('created_by_customer', False),
                creator_id=data.get('creator_id', ''),
                created_at=created_at,
                random_val=data.get('random_val')
            )
            jokes.append(joke)

        return jokes

        

    @staticmethod
    def get_user_created_jokes(user_id: str) -> List[JokeResponse]:
        """Get all jokes created by a user"""
        db = _get_db()
        user_ref = db.collection('users').document(user_id)
        user_doc = user_ref.get()

        if not user_doc.exists:
            return []

        user_data = user_doc.to_dict()
        created_joke_ids = user_data.get('creation_history', [])

        if not created_joke_ids:
            return []

        jokes = []
        for joke_id in created_joke_ids:
            joke_ref = db.collection('jokes').document(joke_id)
            joke_doc = joke_ref.get()

            if joke_doc.exists:
                data = joke_doc.to_dict()
                created_at = data.get('created_at')
                if hasattr(created_at, 'timestamp'):
                    created_at = datetime.fromtimestamp(created_at.timestamp())

                joke = JokeResponse(
                    joke_id=joke_doc.id,
                    joke_setup=data.get('joke_setup', ''),
                    joke_punchline=data.get('joke_punchline', ''),
                    joke_content=data.get('joke_content', ''),
                    default_audio_url=data.get('default_audio_url', ''),  # Support old field name for backward compatibility
                    audio_urls=data.get('audio_urls', []),  # Support old field name for backward compatibility
                    scenarios=data.get('scenarios', []),
                    age_range=data.get('age_range', data.get('ages', [])),  # Support both old and new field names
                    created_by_customer=data.get('created_by_customer', False),
                    creator_id=data.get('creator_id', ''),
                    created_at=created_at
                )
                jokes.append(joke)

        return jokes

    @staticmethod
    def delete_user_created_joke(user_id: str, joke_id: str) -> bool:
        """Remove a joke from user's creation_history"""
        db = _get_db()
        user_ref = db.collection('users').document(user_id)

        # Get current user document
        user_doc = user_ref.get()

        if not user_doc.exists:
            return False

        # Get current creation_history
        user_data = user_doc.to_dict()
        creation_history = user_data.get('creation_history', [])

        # Remove joke_id if it exists in creation_history
        if joke_id in creation_history:
            creation_history.remove(joke_id)
            user_ref.update({'creation_history': creation_history})
            return True
        else:
            # Joke not in creation_history
            return False

    @staticmethod
    def get_favorite_jokes(user_id: str) -> List[JokeResponse]:
        """Get all favorite jokes for a user"""
        db = _get_db()
        user_ref = db.collection('users').document(user_id)
        user_doc = user_ref.get()

        if not user_doc.exists:
            return []

        user_data = user_doc.to_dict()
        favorite_ids = user_data.get('favorites', [])

        if not favorite_ids:
            return []

        # Get all jokes that are in favorites
        jokes = []
        for joke_id in favorite_ids:
            joke_ref = db.collection('jokes').document(joke_id)
            joke_doc = joke_ref.get()

            if joke_doc.exists:
                data = joke_doc.to_dict()
                # Convert Firestore timestamp to datetime if needed
                created_at = data.get('created_at')
                if hasattr(created_at, 'timestamp'):
                    created_at = datetime.fromtimestamp(created_at.timestamp())

                joke = JokeResponse(
                    joke_id=joke_doc.id,
                    joke_setup=data.get('joke_setup', ''),
                    joke_punchline=data.get('joke_punchline', ''),
                    joke_content=data.get('joke_content', ''),
                    default_audio_id=data.get('default_audio_id', ''),
                    audio_ids=data.get('audio_ids', []),
                    scenarios=data.get('scenarios', []),
                    age_range=data.get('age_range', data.get('ages', [])),  # Support both old and new field names
                    created_by_customer=data.get('created_by_customer', False),
                    creator_id=data.get('creator_id', ''),
                    created_at=created_at,
                    random_val=data.get('random_val')
                )
                jokes.append(joke)

        return jokes

    @staticmethod
    def get_user_joke_ids(user_id: str) -> Dict[str, List[str]]:
        """
        Get all favorite, liked, and disliked joke IDs for a user in a single query.
        Returns: {
            'favorite_joke_ids': List[str],
            'liked_joke_ids': List[str],
            'disliked_joke_ids': List[str]
        }
        """
        db = _get_db()
        user_ref = db.collection('users').document(user_id)
        user_doc = user_ref.get()

        if not user_doc.exists:
            return {
                'favorite_joke_ids': [],
                'liked_joke_ids': [],
                'disliked_joke_ids': []
            }

        user_data = user_doc.to_dict()
        favorite_ids = user_data.get('favorites', [])
        liked_ids = user_data.get('like_history', [])
        disliked_ids = user_data.get('dislike_history', [])
        joke_jar_ids = user_data.get('joke_jar', [])

        return {
            'favorite_joke_ids': favorite_ids if favorite_ids else [],
            'liked_joke_ids': liked_ids if liked_ids else [],
            'disliked_joke_ids': disliked_ids if disliked_ids else [],
            'joke_jar_ids': joke_jar_ids if joke_jar_ids else []
        }

    @staticmethod
    def add_to_favorite_jokes(user_id: str, joke_id: str) -> bool:
        """Add a joke to user's favorites list"""
        db = _get_db()
        user_ref = db.collection('users').document(user_id)

        # Get current user document
        user_doc = user_ref.get()

        if not user_doc.exists:
            # Create user document if it doesn't exist
            user_data = {
                'user_display_name': '',
                'user_email': '',
                'country': '',
                'favorites': [joke_id],
                'like_history': [],
                'dislike_history': [],
                'creation_history': [],
                'joke_jar': [],
                'voices': [],
                'settings': {},
                'age_range': '',
                'scenario': '',
                'voice_to_use': '',
                'created_at': datetime.utcnow()
            }
            user_ref.set(user_data)
            # Update joke_metadata: increment saved_to_favorite_times
            FirebaseService._update_joke_metadata_counter(joke_id, 'saved_to_favorite_times', 1)
            return True
        
        # Get current favorites
        user_data = user_doc.to_dict()
        favorites = user_data.get('favorites', [])

        # Add joke_id if not already in favorites
        if joke_id not in favorites:
            favorites.append(joke_id)
            user_ref.update({'favorites': favorites})
            # Update joke_metadata: increment saved_to_favorite_times
            FirebaseService._update_joke_metadata_counter(joke_id, 'saved_to_favorite_times', 1)
            return True
        else:
            # Already in favorites
            return False
    
    @staticmethod
    def delete_favorite_jokes(user_id: str, joke_id: str) -> bool:
        """Remove a joke from user's favorites list"""
        db = _get_db()
        user_ref = db.collection('users').document(user_id)

        # Get current user document
        user_doc = user_ref.get()

        if not user_doc.exists:
            return False

        # Get current favorites
        user_data = user_doc.to_dict()
        favorites = user_data.get('favorites', [])

        # Remove joke_id if it exists in favorites
        if joke_id in favorites:
            favorites.remove(joke_id)
            user_ref.update({'favorites': favorites})
            # Update joke_metadata: decrement saved_to_favorite_times
            FirebaseService._update_joke_metadata_counter(joke_id, 'saved_to_favorite_times', -1)
            return True
        else:
            # Joke not in favorites
            return False

    @staticmethod
    def add_to_user_liked_history(user_id: str, joke_id: str) -> bool:
        """Add joke to user's like_history and remove from dislike_history"""
        db = _get_db()
        user_ref = db.collection('users').document(user_id)
        user_doc = user_ref.get()

        if not user_doc.exists:
            user_data = {
                'user_display_name': '',
                'user_email': '',
                'country': '',
                'favorites': [],
                'like_history': [joke_id],
                'dislike_history': [],
                'creation_history': [],
                'joke_jar': [],
                'voices': [],
                'settings': {},
                'age_range': '',
                'scenario': '',
                'voice_to_use': '',
                'created_at': datetime.utcnow()
            }
            user_ref.set(user_data)
            # Update joke_metadata: increment liked_times
            FirebaseService._update_joke_metadata_counter(joke_id, 'liked_times', 1)
            return True

        user_data = user_doc.to_dict()
        like_history = user_data.get('like_history', [])
        dislike_history = user_data.get('dislike_history', [])

        was_in_dislike = joke_id in dislike_history
        updated = False
        if joke_id not in like_history:
            like_history.append(joke_id)
            updated = True
        if joke_id in dislike_history:
            dislike_history.remove(joke_id)
            updated = True

        if updated:
            user_ref.update({
                'like_history': like_history,
                'dislike_history': dislike_history
            })
            # Update joke_metadata: increment liked_times, decrement disliked_times if it was there
            FirebaseService._update_joke_metadata_counter(joke_id, 'liked_times', 1)
            if was_in_dislike:
                FirebaseService._update_joke_metadata_counter(joke_id, 'disliked_times', -1)
            return True
        return False

    @staticmethod
    def add_to_user_disliked_history(user_id: str, joke_id: str) -> bool:
        """Add joke to user's dislike_history and remove from like_history"""
        db = _get_db()
        user_ref = db.collection('users').document(user_id)
        user_doc = user_ref.get()

        if not user_doc.exists:
            user_data = {
                'user_display_name': '',
                'user_email': '',
                'country': '',
                'favorites': [],
                'like_history': [],
                'dislike_history': [joke_id],
                'creation_history': [],
                'joke_jar': [],
                'voices': [],
                'settings': {},
                'age_range': '',
                'scenario': '',
                'voice_to_use': '',
                'created_at': datetime.utcnow()
            }
            user_ref.set(user_data)
            # Update joke_metadata: increment disliked_times
            FirebaseService._update_joke_metadata_counter(joke_id, 'disliked_times', 1)
            return True

        # Get current like_history and dislike_history
        user_data = user_doc.to_dict()
        like_history = user_data.get('like_history', [])
        dislike_history = user_data.get('dislike_history', [])

        was_in_like = joke_id in like_history
        
        # Remove from like_history if present
        if joke_id in like_history:
            like_history.remove(joke_id)
        
        # Add to dislike_history if not already present
        if joke_id not in dislike_history:
            dislike_history.append(joke_id)
        
        # Update user document
        user_ref.update({
            'like_history': like_history,
            'dislike_history': dislike_history
        })
        # Update joke_metadata: increment disliked_times, decrement liked_times if it was there
        FirebaseService._update_joke_metadata_counter(joke_id, 'disliked_times', 1)
        if was_in_like:
            FirebaseService._update_joke_metadata_counter(joke_id, 'liked_times', -1)
        return True
    
    @staticmethod
    def get_liked_jokes(user_id: str) -> List[JokeResponse]:
        """Get all liked jokes for a user"""
        db = _get_db()
        user_ref = db.collection('users').document(user_id)
        user_doc = user_ref.get()
        
        if not user_doc.exists:
            return []
        
        user_data = user_doc.to_dict()
        liked_ids = user_data.get('like_history', [])
        
        if not liked_ids:
            return []
        
        # Get all jokes that are in like_history
        jokes = []
        for joke_id in liked_ids:
            joke_ref = db.collection('jokes').document(joke_id)
            joke_doc = joke_ref.get()
            
            if joke_doc.exists:
                data = joke_doc.to_dict()
                # Convert Firestore timestamp to datetime if needed
                created_at = data.get('created_at')
                if hasattr(created_at, 'timestamp'):
                    created_at = datetime.fromtimestamp(created_at.timestamp())
                
                joke = JokeResponse(
                    joke_id=joke_doc.id,
                    joke_setup=data.get('joke_setup', ''),
                    joke_punchline=data.get('joke_punchline', ''),
                    joke_content=data.get('joke_content', ''),
                    default_audio_url=data.get('default_audio_url', data.get('default_audio_id', '')),  # Support old field name for backward compatibility
                    audio_urls=FirebaseService._normalize_audio_urls(data.get('audio_urls', data.get('audio_ids', []))),  # Support old field name for backward compatibility
                    scenarios=data.get('scenarios', []),
                    age_range=data.get('age_range', data.get('ages', [])),  # Support both old and new field names
                    created_by_customer=data.get('created_by_customer', False),
                    creator_id=data.get('creator_id', ''),
                    created_at=created_at
                )
                jokes.append(joke)
        
        return jokes
    
    @staticmethod
    def get_random_jokes(limit: int = 10, age_range: Optional[str] = None, scenario: Optional[str] = None) -> List[JokeResponse]:
        """Get random jokes from Firestore, optionally filtered by age_range and scenario"""
        db = _get_db()
        threshold = random.random()
        direction = random.choice([True, False])

        jokes_ref = db.collection('jokes')
        
        # Build query based on direction
        # Query more than limit to account for filtering by age_range/scenario
        query_limit = limit * 10  # Query up to 10x the limit to ensure we have enough after filtering
        
        if direction:
            # Direction True: get jokes where random_val >= threshold, ordered ascending
            query = jokes_ref.where('random_val', '>=', threshold).order_by('random_val', direction='ASCENDING').limit(query_limit)
        else:
            # Direction False: get jokes where random_val <= threshold, ordered descending
            query = jokes_ref.where('random_val', '<=', threshold).order_by('random_val', direction='DESCENDING').limit(query_limit)
        
        docs = list(query.stream())
        
        jokes = []
        for doc in docs:
            data = doc.to_dict()
            # Skip jokes without random_val (old jokes)
            if data.get('random_val') is None:
                continue
                
            created_at = data.get('created_at')
            if hasattr(created_at, 'timestamp'):
                created_at = datetime.fromtimestamp(created_at.timestamp())
            
            joke = JokeResponse(
                joke_id=doc.id,
                joke_setup=data.get('joke_setup', ''),
                joke_punchline=data.get('joke_punchline', ''),
                joke_content=data.get('joke_content', ''),
                default_audio_url=data.get('default_audio_url', ''),  # Support old field name for backward compatibility
                audio_urls=data.get('audio_urls', []),  # Support old field name for backward compatibility
                scenarios=data.get('scenarios', []),
                age_range=data.get('age_range', data.get('ages', [])),  # Support both old and new field names
                created_by_customer=data.get('created_by_customer', False),
                creator_id=data.get('creator_id', ''),
                created_at=created_at,
                random_val=data.get('random_val')
            )
            
            # Filter by scenario: 
            # - If scenario is "all" or empty/None, match all jokes (no filtering)
            # - If scenario is provided, match if scenario is in joke's scenarios OR joke's scenarios is empty
            scenario_match = True
            if scenario and scenario.strip():
                scenario_lower = scenario.strip().lower()
                if scenario_lower != "all":
                    joke_scenarios = joke.scenarios or []
                    scenario_match = scenario_lower in [s.lower() for s in joke_scenarios] or len(joke_scenarios) == 0
            
            # Filter by age_range:
            # - If age_range is "all" or empty/None, match all jokes (no filtering)
            # - If age_range is provided, match if age_range is in joke's age_range OR joke's age_range is empty
            age_match = True
            if age_range and age_range.strip():
                age_range_lower = age_range.strip().lower()
                if age_range_lower != "all":
                    joke_age_ranges = joke.age_range or []
                    age_match = age_range_lower in [a.lower() for a in joke_age_ranges] or len(joke_age_ranges) == 0
            
            # Only include jokes that match both filters
            if scenario_match and age_match:
                jokes.append(joke)
                # Stop once we have enough jokes
                if len(jokes) >= limit:
                    break
        
        return jokes[:limit]
    
    @staticmethod
    def joke_exists(joke_setup: str, joke_punchline: str) -> bool:
        """Check if a joke with the same setup and punchline already exists"""
        db = _get_db()
        jokes_ref = db.collection('jokes')
        
        # Query for jokes with matching setup and punchline
        setup_query = jokes_ref.where('joke_setup', '==', joke_setup).stream()
        for doc in setup_query:
            data = doc.to_dict()
            if data.get('joke_punchline', '').strip().lower() == joke_punchline.strip().lower():
                return True
        
        return False
    
    @staticmethod
    def get_joke_doc_by_setup_punchline(joke_setup: str, joke_punchline: str):
        """Get a joke document reference by setup and punchline, returns (doc_ref, data) or (None, None)"""
        db = _get_db()
        jokes_ref = db.collection('jokes')
        
        # Query for jokes with matching setup
        setup_query = jokes_ref.where('joke_setup', '==', joke_setup).stream()
        for doc in setup_query:
            data = doc.to_dict()
            if data.get('joke_punchline', '').strip().lower() == joke_punchline.strip().lower():
                return doc.reference, data
        
        return None, None
    
    @staticmethod
    def _update_joke_metadata_counter(joke_id: str, field: str, increment: int = 1):
        """
        Helper function to update joke_metadata counter fields asynchronously.
        field: 'liked_times', 'disliked_times', or 'saved_to_favorite_times'
        increment: 1 to increment, -1 to decrement
        Runs in a background thread to avoid blocking the main operation.
        """
        def _update_counter():
            try:
                db = _get_db()
                metadata_ref = db.collection('joke_metadata').document(joke_id)
                metadata_doc = metadata_ref.get()
                
                if metadata_doc.exists:
                    # Update existing metadata
                    current_value = metadata_doc.to_dict().get(field, 0)
                    new_value = max(0, current_value + increment)  # Ensure it doesn't go below 0
                    metadata_ref.update({field: new_value})
                else:
                    # Create new metadata document with default values
                    metadata_data = {
                        'liked_times': 0,
                        'disliked_times': 0,
                        'saved_to_favorite_times': 0
                    }
                    metadata_data[field] = max(0, increment)  # Ensure it doesn't go below 0
                    metadata_ref.set(metadata_data)
            except Exception as e:
                print(f"Error updating joke_metadata counter for joke {joke_id}: {str(e)}")
        
        # Run the update in a background thread
        thread = threading.Thread(target=_update_counter, daemon=True)
        thread.start()
    
    @staticmethod
    def joke_id_exists(joke_id: str) -> bool:
        """Check if a joke with the given ID exists in Firestore"""
        db = _get_db()
        joke_ref = db.collection('jokes').document(joke_id)
        joke_doc = joke_ref.get()
        return joke_doc.exists
    
    @staticmethod
    def get_joke_by_id(joke_id: str) -> Optional[JokeResponse]:
        """Get a joke by its ID"""
        db = _get_db()
        joke_ref = db.collection('jokes').document(joke_id)
        joke_doc = joke_ref.get()
        
        if not joke_doc.exists:
            return None
        
        data = joke_doc.to_dict()
        created_at = data.get('created_at')
        if hasattr(created_at, 'timestamp'):
            created_at = datetime.fromtimestamp(created_at.timestamp())
        
        return JokeResponse(
            joke_id=joke_doc.id,
            joke_setup=data.get('joke_setup', ''),
            joke_punchline=data.get('joke_punchline', ''),
            joke_content=data.get('joke_content', ''),
            default_audio_url=data.get('default_audio_url', data.get('default_audio_id', '')),  # Support old field name for backward compatibility
            audio_urls=data.get('audio_urls', data.get('audio_ids', [])),  # Support old field name for backward compatibility
            scenarios=data.get('scenarios', []),
            age_range=data.get('age_range', data.get('ages', [])),  # Support both old and new field names
            created_by_customer=data.get('created_by_customer', False),
            creator_id=data.get('creator_id', ''),
            created_at=created_at,
            random_val=data.get('random_val')
        )
    
    @staticmethod
    def get_random_liked_jokes(user_id: str, limit: int = 1) -> List[JokeResponse]:
        """Get a random subset of liked jokes for a user (avoids full database scan)"""
        # Get liked joke IDs
        user_joke_ids = FirebaseService.get_user_joke_ids(user_id)
        liked_joke_ids = user_joke_ids.get('liked_joke_ids', [])
        
        if not liked_joke_ids:
            return []
        
        # Randomly select up to 'limit' IDs
        selected_ids = random.sample(liked_joke_ids, min(limit, len(liked_joke_ids)))
        
        # Fetch jokes by ID
        jokes = []
        for joke_id in selected_ids:
            joke = FirebaseService.get_joke_by_id(joke_id)
            if joke:
                jokes.append(joke)
        
        return jokes
    
    @staticmethod
    def get_random_disliked_jokes(user_id: str, limit: int = 5) -> List[JokeResponse]:
        """Get a random subset of disliked jokes for a user (avoids full database scan)"""
        # Get disliked joke IDs
        user_joke_ids = FirebaseService.get_user_joke_ids(user_id)
        disliked_joke_ids = user_joke_ids.get('disliked_joke_ids', [])
        
        if not disliked_joke_ids:
            return []
        
        # Randomly select up to 'limit' IDs
        selected_ids = random.sample(disliked_joke_ids, min(limit, len(disliked_joke_ids)))
        
        # Fetch jokes by ID
        jokes = []
        for joke_id in selected_ids:
            joke = FirebaseService.get_joke_by_id(joke_id)
            if joke:
                jokes.append(joke)
        
        return jokes
    
    @staticmethod
    def get_default_audio(joke_id: str) -> Optional[str]:
        """
        Get the audio URL for a joke and save it to the joke_audios collection.
        
        Args:
            joke_id: The ID of the joke
        
        Returns:
            str: The audio URL for the joke, or None if not found
        """
        db = _get_db()
        
        # Get the joke document to retrieve the audio URL
        joke_ref = db.collection('jokes').document(joke_id)
        joke_doc = joke_ref.get()
        
        if not joke_doc.exists:
            return None
        
        joke_data = joke_doc.to_dict()
        
        # Get audio URL
        audio_url = joke_data.get('default_audio_url')
        
        if audio_url:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Getting default audio for joke {joke_id}: {audio_url}")
            return audio_url
            
        return None
    
    @staticmethod
    def save_jokes_async(jokes: List[dict], creator_id: str = "gemini"):
        """Save jokes to database asynchronously (for background tasks), skipping duplicates"""
        db = _get_db()
        saved_count = 0
        
        for joke_data in jokes:
            try:
                joke_setup = joke_data.get('joke_setup', '')
                joke_punchline = joke_data.get('joke_punchline', '')
                new_scenarios = joke_data.get('scenarios', [])
                new_age_range = joke_data.get('age_range', [])
                
                # Check if joke already exists and get its document reference
                existing_doc_ref, existing_data = FirebaseService.get_joke_doc_by_setup_punchline(
                    joke_setup, joke_punchline
                )
                
                if existing_doc_ref and existing_data:
                    # Joke exists - merge age_range and scenarios
                    existing_scenarios = set(existing_data.get('scenarios', []))
                    existing_age_range = set(existing_data.get('age_range', []))
                    
                    # Add new scenarios and age_range to existing sets
                    existing_scenarios.update(new_scenarios)
                    existing_age_range.update(new_age_range)
                    
                    # Update the existing joke with merged data
                    existing_doc_ref.update({
                        'scenarios': list(existing_scenarios),
                        'age_range': list(existing_age_range)
                    })
                    saved_count += 1
                    continue
                
                # Joke doesn't exist - create new joke document
                joke_doc = {
                    'joke_setup': joke_setup,
                    'joke_punchline': joke_punchline,
                    'joke_content': joke_data.get('joke_content', ''),
                    'default_audio_url': joke_data.get('default_audio_url', ''),
                    'audio_urls': joke_data.get('audio_urls', []),
                    'scenarios': new_scenarios,
                    'age_range': new_age_range,
                    'created_by_customer': False,
                    'creator_id': creator_id,
                    'created_at': datetime.utcnow(),
                    'random_val': random.random()
                }
                
                # If joke_id is provided, use it; otherwise let Firestore generate one
                joke_id = joke_data.get('joke_id', '')
                if joke_id:
                    # Use the provided joke_id
                    doc_ref = db.collection('jokes').document(joke_id)
                    doc_ref.set(joke_doc)
                else:
                    # Let Firestore generate the ID
                    db.collection('jokes').add(joke_doc)
                
                saved_count += 1
            except Exception as e:
                print(f"Error saving joke: {str(e)}")
                continue
        
        print(f"Saved {saved_count} new jokes to database")
        return saved_count
    
    @staticmethod
    def get_disliked_jokes(user_id: str) -> List[JokeResponse]:
        """Get all disliked jokes for a user"""
        db = _get_db()
        user_ref = db.collection('users').document(user_id)
        user_doc = user_ref.get()
        
        if not user_doc.exists:
            return []
        
        user_data = user_doc.to_dict()
        disliked_ids = user_data.get('dislike_history', [])
        
        if not disliked_ids:
            return []
        
        # Get all jokes that are in dislike_history
        jokes = []
        for joke_id in disliked_ids:
            joke_ref = db.collection('jokes').document(joke_id)
            joke_doc = joke_ref.get()
            
            if joke_doc.exists:
                data = joke_doc.to_dict()
                # Convert Firestore timestamp to datetime if needed
                created_at = data.get('created_at')
                if hasattr(created_at, 'timestamp'):
                    created_at = datetime.fromtimestamp(created_at.timestamp())
                
                joke = JokeResponse(
                    joke_id=joke_doc.id,
                    joke_setup=data.get('joke_setup', ''),
                    joke_punchline=data.get('joke_punchline', ''),
                    joke_content=data.get('joke_content', ''),
                    default_audio_id=data.get('default_audio_id', ''),
                    audio_ids=data.get('audio_ids', []),
                    scenarios=data.get('scenarios', []),
                    age_range=data.get('age_range', data.get('ages', [])),  # Support both old and new field names
                    created_by_customer=data.get('created_by_customer', False),
                    creator_id=data.get('creator_id', ''),
                    created_at=created_at,
                    random_val=data.get('random_val')
                )
                jokes.append(joke)
        
        return jokes
    
    @staticmethod
    def migrate_add_random_val() -> Dict[str, int]:
        """
        Migration function to add random_val to all jokes that don't have it.
        Returns a dictionary with statistics about the migration.
        """
        db = _get_db()
        jokes_ref = db.collection('jokes')
        docs = jokes_ref.stream()
        
        updated_count = 0
        skipped_count = 0
        error_count = 0
        
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting migration to add random_val to jokes...")
        
        for doc in docs:
            try:
                data = doc.to_dict()
                
                # Check if random_val already exists
                if 'random_val' in data and data['random_val'] is not None:
                    skipped_count += 1
                    continue
                
                # Add random_val
                random_value = random.random()
                doc.reference.update({'random_val': random_value})
                updated_count += 1
                
                if updated_count % 100 == 0:
                    print(f"Migrated {updated_count} jokes so far...")
                    
            except Exception as e:
                print(f"Error updating joke {doc.id}: {str(e)}")
                error_count += 1
                continue
        
        result = {
            'updated': updated_count,
            'skipped': skipped_count,
            'errors': error_count,
            'total_processed': updated_count + skipped_count + error_count
        }
        
        print(f"Migration completed: {result}")
        return result
    
    @staticmethod
    def save_audio_url_async(joke_id: str, audio_url: str, audio_size: int, voice_id: str = "default", is_default: bool = True):
        """
        Save audio URL and metadata to Firestore asynchronously.
        Updates the joke document with default_audio_url if is_default is True.
        Always inserts/updates entry in joke_audios collection.
        
        Args:
            joke_id: The ID of the joke
            audio_url: The URL of the audio file
            audio_size: The size of the audio file in bytes
            voice_id: The ID of the voice used for this audio (defaults to "default")
            is_default: If True, update default_audio_url in the joke document. Defaults to True.
        """
        try:
            db = _get_db()
            joke_ref = db.collection('jokes').document(joke_id)
            
            # Always add audio_url to audio_urls array as a map of voice_id to audio_url
            audio_entry = {"voice_id": voice_id, "audio_url": audio_url}
            joke_ref.update({
                'audio_urls': ArrayUnion([audio_entry])
            })
            
            # Update the joke document with default_audio_url only if is_default is True
            if is_default:
                joke_ref.update({
                    'default_audio_url': audio_url
                })
           
            # Insert/update entry in joke_audios collection (always save)
            db.collection('joke_audios').document(joke_id).set({
                'joke_id': joke_id,
                'audio_url': audio_url,
                'audio_size': audio_size,
                'voice_id': voice_id,
                'created_at': datetime.utcnow()
            }, merge=True)
        except Exception as e:
            print(f"Error saving audio URL asynchronously for joke {joke_id}: {str(e)}")
    
    @staticmethod
    def save_to_bucket(file_path: str, file_data: bytes, content_type: str = 'audio/wav') -> tuple[str, int]:
        """
        Upload file data to Firebase Storage bucket and make it publicly accessible.
        
        Args:
            file_path: The path where the file should be stored in the bucket
            file_data: The file data as bytes
            content_type: The content type of the file (default: 'audio/wav')
        
        Returns:
            tuple: (public_url, file_size) - The public URL of the uploaded file and its size in bytes
        """
        try:
            bucket = get_storage_bucket()
            blob = bucket.blob(file_path)
            
            # Upload the file
            blob.upload_from_string(file_data, content_type=content_type)
            
            # Make the file publicly accessible
            blob.make_public()
            
            # Get the public URL and file size
            audio_url = blob.public_url
            file_size = len(file_data)
            
            return audio_url, file_size
        except Exception as e:
            print(f"Error uploading file to bucket at {file_path}: {str(e)}")
            raise
    
    @staticmethod
    def add_voice(voice_id: str, creator_id: str, voice_name: str, voice_url: str) -> Dict:
        """
        Add a voice to the voices collection and update the user's voices array.
        
        Args:
            voice_id: UUID of the voice
            creator_id: ID of the user creating the voice
            voice_name: Name of the voice
            voice_url: URL of the voice file
        
        Returns:
            Dict containing the voice data
        """
        db = _get_db()
        
        # Prepare voice data
        voice_data = {
            'voice_id': voice_id,
            'creator_id': creator_id,
            'voice_name': voice_name,
            'voice_url': voice_url,
            'created_at': datetime.utcnow()
        }
        
        # Save to voices collection (use voice_id as document ID)
        db.collection('voices').document(voice_id).set(voice_data)
        
        # Update user's voices array
        user_ref = db.collection('users').document(creator_id)
        user_doc = user_ref.get()
        
        if not user_doc.exists:
            # Create user document if it doesn't exist
            user_data = {
                'user_display_name': '',
                'user_email': '',
                'country': '',
                'favorites': [],
                'like_history': [],
                'dislike_history': [],
                'creation_history': [],
                'joke_jar': [],
                'voices': [voice_id],
                'settings': {},
                'age_range': '',
                'scenario': '',
                'voice_to_use': '',
                'created_at': datetime.utcnow()
            }
            user_ref.set(user_data)
        else:
            # Update existing user document - add voice_id to voices array using ArrayUnion to avoid duplicates
            user_ref.update({
                'voices': ArrayUnion([voice_id])
            })
        
            return voice_data
    
    @staticmethod
    def add_to_history(creator_id: str, joke_id: str) -> bool:
        """
        Add a joke_id to the user's joke_jar array.
        
        Args:
            creator_id: ID of the user
            joke_id: ID of the joke to add to joke_jar
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            db = _get_db()
            user_ref = db.collection('users').document(creator_id)
            user_doc = user_ref.get()
            
            if not user_doc.exists:
                # Create user document if it doesn't exist
                user_data = {
                    'user_display_name': '',
                    'user_email': '',
                    'country': '',
                    'favorites': [],
                    'like_history': [],
                    'dislike_history': [],
                    'creation_history': [],
                    'joke_jar': [joke_id],
                    'voices': [],
                    'settings': {},
                    'age_range': '',
                    'scenario': '',
                    'voice_to_use': '',
                    'created_at': datetime.utcnow()
                }
                user_ref.set(user_data)
            else:
                # Update existing user document - add joke_id to joke_jar array using ArrayUnion
                user_ref.update({
                    'joke_jar': ArrayUnion([joke_id])
                })
            
            return True
        except Exception as e:
            print(f"Error adding to joke_jar for user {creator_id}: {str(e)}")
            return False
    