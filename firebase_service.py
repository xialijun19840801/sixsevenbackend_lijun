from firebase.firebase_init import get_firestore
from models import JokeResponse
from typing import List, Optional
from datetime import datetime
import random

def _get_db():
    """Lazy initialization of Firestore client"""
    return get_firestore()

class FirebaseService:
    
    @staticmethod
    def add_to_user_created_jokes(
        joke_setup: str,
        joke_punchline: str,
        creator_id: str,
        joke_content: Optional[str] = "",
        default_audio_id: Optional[str] = "",
        scenarios: Optional[List[str]] = None,
        age_range: Optional[List[str]] = None
    ) -> str:
        """Add a new joke to Firestore and add it to user's creation_history"""
        db = _get_db()
        joke_data = {
            'joke_setup': joke_setup,
            'joke_punchline': joke_punchline,
            'joke_content': joke_content,
            'default_audio_id': default_audio_id,
            'scenarios': scenarios or [],
            'age_range': age_range or [],
            'created_by_customer': True,
            'creator_id': creator_id,
            'created_at': datetime.utcnow()
        }
        
        # Add joke to jokes collection
        doc_ref = db.collection('jokes').add(joke_data)
        joke_id = doc_ref[1].id

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
                default_audio_id=data.get('default_audio_id', ''),
                scenarios=data.get('scenarios', []),
                age_range=data.get('age_range', data.get('ages', [])),  # Support both old and new field names
                created_by_customer=data.get('created_by_customer', False),
                creator_id=data.get('creator_id', ''),
                created_at=created_at
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
                    default_audio_id=data.get('default_audio_id', ''),
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
                    scenarios=data.get('scenarios', []),
                    age_range=data.get('age_range', data.get('ages', [])),  # Support both old and new field names
                    created_by_customer=data.get('created_by_customer', False),
                    creator_id=data.get('creator_id', ''),
                    created_at=created_at
                )
                jokes.append(joke)

        return jokes

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
                'voices': [],
                'settings': {},
                'age_range': '',
                'scenario': '',
                'voice_to_use': '',
                'created_at': datetime.utcnow()
            }
            user_ref.set(user_data)
            return True
        
        # Get current favorites
        user_data = user_doc.to_dict()
        favorites = user_data.get('favorites', [])

        # Add joke_id if not already in favorites
        if joke_id not in favorites:
            favorites.append(joke_id)
            user_ref.update({'favorites': favorites})
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
                'voices': [],
                'settings': {},
                'age_range': '',
                'scenario': '',
                'voice_to_use': '',
                'created_at': datetime.utcnow()
            }
            user_ref.set(user_data)
            return True

        user_data = user_doc.to_dict()
        like_history = user_data.get('like_history', [])
        dislike_history = user_data.get('dislike_history', [])

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
                'voices': [],
                'settings': {},
                'age_range': '',
                'scenario': '',
                'voice_to_use': '',
                'created_at': datetime.utcnow()
            }
            user_ref.set(user_data)
            return True

        # Get current like_history and dislike_history
        user_data = user_doc.to_dict()
        like_history = user_data.get('like_history', [])
        dislike_history = user_data.get('dislike_history', [])

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
                    default_audio_id=data.get('default_audio_id', ''),
                    scenarios=data.get('scenarios', []),
                    age_range=data.get('age_range', data.get('ages', [])),  # Support both old and new field names
                    created_by_customer=data.get('created_by_customer', False),
                    creator_id=data.get('creator_id', ''),
                    created_at=created_at
                )
                jokes.append(joke)
        
        return jokes
    
    @staticmethod
    def get_random_jokes(limit: int = 20) -> List[JokeResponse]:
        """Get random jokes from Firestore"""
        db = _get_db()
        jokes_ref = db.collection('jokes')
        docs = list(jokes_ref.stream())
        
        # Shuffle and take limit
        random.shuffle(docs)
        docs = docs[:limit]
        
        jokes = []
        for doc in docs:
            data = doc.to_dict()
            created_at = data.get('created_at')
            if hasattr(created_at, 'timestamp'):
                created_at = datetime.fromtimestamp(created_at.timestamp())
            
            joke = JokeResponse(
                joke_id=doc.id,
                joke_setup=data.get('joke_setup', ''),
                joke_punchline=data.get('joke_punchline', ''),
                joke_content=data.get('joke_content', ''),
                default_audio_id=data.get('default_audio_id', ''),
                scenarios=data.get('scenarios', []),
                age_range=data.get('age_range', data.get('ages', [])),  # Support both old and new field names
                created_by_customer=data.get('created_by_customer', False),
                creator_id=data.get('creator_id', ''),
                created_at=created_at
            )
            jokes.append(joke)
        
        return jokes
    
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
    def save_jokes_async(jokes: List[dict], creator_id: str = "gemini"):
        """Save jokes to database asynchronously (for background tasks), skipping duplicates"""
        db = _get_db()
        saved_count = 0
        
        for joke_data in jokes:
            try:
                # Check if joke already exists
                if FirebaseService.joke_exists(
                    joke_data.get('joke_setup', ''),
                    joke_data.get('joke_punchline', '')
                ):
                    continue  # Skip duplicate
                
                # Create joke document
                joke_doc = {
                    'joke_setup': joke_data.get('joke_setup', ''),
                    'joke_punchline': joke_data.get('joke_punchline', ''),
                    'joke_content': joke_data.get('joke_content', ''),
                    'default_audio_id': joke_data.get('default_audio_id', ''),
                    'scenarios': joke_data.get('scenarios', []),
                    'age_range': joke_data.get('age_range', []),
                    'created_by_customer': False,
                    'creator_id': creator_id,
                    'created_at': datetime.utcnow()
                }
                
                # Add to Firestore
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
                    scenarios=data.get('scenarios', []),
                    age_range=data.get('age_range', data.get('ages', [])),  # Support both old and new field names
                    created_by_customer=data.get('created_by_customer', False),
                    creator_id=data.get('creator_id', ''),
                    created_at=created_at
                )
                jokes.append(joke)
        
        return jokes
