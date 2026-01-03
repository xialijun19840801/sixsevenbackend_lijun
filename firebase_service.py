from firebase.firebase_init import get_firestore
from models import JokeResponse
from typing import List, Optional
from datetime import datetime

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
        ages: Optional[List[str]] = None
    ) -> str:
        """Add a new joke to Firestore and add it to user's creation_history"""
        db = _get_db()
        joke_data = {
            'joke_setup': joke_setup,
            'joke_punchline': joke_punchline,
            'joke_content': joke_content,
            'default_audio_id': default_audio_id,
            'scenarios': scenarios or [],
            'ages': ages or [],
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
                'age': '',
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
    def delete_user_created_jokes(user_id: str, joke_id: str) -> bool:
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
                ages=data.get('ages', []),
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
                'age': '',
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
        
        # Get current user document
        user_doc = user_ref.get()
        
        if not user_doc.exists:
            # Create user document if it doesn't exist
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
                'age': '',
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
        
        # Remove from dislike_history if present
        if joke_id in dislike_history:
            dislike_history.remove(joke_id)
        
        # Add to like_history if not already present
        if joke_id not in like_history:
            like_history.append(joke_id)
        
        # Update user document
        user_ref.update({
            'like_history': like_history,
            'dislike_history': dislike_history
        })
        return True
    
    @staticmethod
    def add_to_user_dislike_history(user_id: str, joke_id: str) -> bool:
        """Add joke to user's dislike_history and remove from like_history"""
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
                'favorites': [],
                'like_history': [],
                'dislike_history': [joke_id],
                'creation_history': [],
                'voices': [],
                'settings': {},
                'age': '',
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
    
    
