#!/usr/bin/env python3
"""
Test script to generate audio for the first joke using all voices from the voices collection.
Calls the get_audio_for_joke_with_voice functionality.
"""

import os
import sys
from pathlib import Path

# Add current directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from firebase.firebase_init import initialize_firebase
from firebase_service import FirebaseService
from datetime import datetime

def get_first_joke():
    """Get the first joke from the jokes collection."""
    try:
        from firebase.firebase_init import get_firestore
        db = get_firestore()
        
        # Get the first joke
        jokes_ref = db.collection('jokes')
        jokes = jokes_ref.limit(1).stream()
        
        for joke_doc in jokes:
            joke_data = joke_doc.to_dict()
            joke_id = joke_doc.id
            return {
                'joke_id': joke_id,
                'joke_setup': joke_data.get('joke_setup', ''),
                'joke_punchline': joke_data.get('joke_punchline', ''),
                'joke_content': joke_data.get('joke_content', '')
            }
        
        return None
    except Exception as e:
        print(f"Error getting first joke: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def get_all_voices():
    """Get all voices from the voices collection."""
    try:
        from firebase.firebase_init import get_firestore
        db = get_firestore()
        
        voices_ref = db.collection('voices')
        voices = voices_ref.stream()
        
        voice_list = []
        for voice_doc in voices:
            voice_data = voice_doc.to_dict()
            voice_id = voice_doc.id
            voice_list.append({
                'voice_id': voice_id,
                'voice_name': voice_data.get('voice_name', ''),
                'voice_url': voice_data.get('voice_url', ''),
                'creator_id': voice_data.get('creator_id', '')
            })
        
        return voice_list
    except Exception as e:
        print(f"Error getting voices: {str(e)}")
        import traceback
        traceback.print_exc()
        return []

def test_audio_generation_for_joke_with_voice(joke_id: str, voice_id: str):
    """
    Test generating audio for a joke with a specific voice.
    This simulates calling the get_audio_for_joke_with_voice API endpoint.
    
    Args:
        joke_id: The ID of the joke
        voice_id: The ID of the voice
    
    Returns:
        dict: Result with audio_url or error message
    """
    try:
        print(f"\n{'='*60}")
        print(f"Testing audio generation for joke {joke_id} with voice {voice_id}")
        print(f"{'='*60}")
        
        # Step 1: Check if audio already exists
        existing_audio_url = FirebaseService.get_audio_for_joke_and_voice(joke_id, voice_id)
        
        if existing_audio_url:
            print(f"✓ Found existing audio: {existing_audio_url}")
            return {
                'success': True,
                'audio_url': existing_audio_url,
                'cached': True
            }
        
        # Step 2: Get the voice to retrieve voice_url
        voice_data = FirebaseService.get_voice_by_id(voice_id)
        if not voice_data:
            error_msg = f"Voice with ID {voice_id} not found"
            print(f"✗ {error_msg}")
            return {
                'success': False,
                'error': error_msg
            }
        
        voice_url = voice_data.get('voice_url')
        if not voice_url:
            error_msg = f"Voice {voice_id} does not have a voice_url"
            print(f"✗ {error_msg}")
            return {
                'success': False,
                'error': error_msg
            }
        
        print(f"✓ Found voice: {voice_data.get('voice_name', voice_id)}")
        print(f"  Voice URL: {voice_url}")
        
        # Step 3: Get the joke to retrieve joke text
        joke = FirebaseService.get_joke_by_id(joke_id)
        if not joke:
            error_msg = f"Joke with ID {joke_id} not found"
            print(f"✗ {error_msg}")
            return {
                'success': False,
                'error': error_msg
            }
        
        print(f"✓ Found joke:")
        print(f"  Setup: {joke.joke_setup}")
        print(f"  Punchline: {joke.joke_punchline}")
        
        # Step 4: Create joke text from setup and punchline
        joke_text = f"{joke.joke_setup}, {joke.joke_punchline}"
        
        # Step 5: Generate audio using ElevenLabs
        print(f"\nGenerating audio with ElevenLabs...")
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Start generating audio with ElevenLabs")
        
        from elevenlabs_service import ElevenlabsService
        from firebase.config import ELEVENLABS_API_KEY
        
        if not ELEVENLABS_API_KEY:
            error_msg = "ELEVENLABS_API_KEY environment variable is not set"
            print(f"✗ {error_msg}")
            return {
                'success': False,
                'error': error_msg
            }
        
        elevenlabs_service = ElevenlabsService()
        
        result = elevenlabs_service.read_joke_with_the_voice(
            firebase_voice_url=voice_url,
            joke_text=joke_text,
            joke_id=joke_id
        )
        
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Finished generating audio with ElevenLabs")
        
        if not result:
            error_msg = "Failed to generate audio for joke with ElevenLabs"
            print(f"✗ {error_msg}")
            return {
                'success': False,
                'error': error_msg
            }
        
        # Extract audio_url, audio_size, and elevenlabs_voice_id from result
        audio_url = result.get("audio_url")
        audio_size = result.get("audio_size")
        elevenlabs_voice_id = result.get("elevenlabs_voice_id")
        
        if not audio_url or not audio_size:
            error_msg = "Failed to get audio URL or size from ElevenLabs"
            print(f"✗ {error_msg}")
            return {
                'success': False,
                'error': error_msg
            }
        
        print(f"✓ Audio generated successfully!")
        print(f"  Audio URL: {audio_url}")
        print(f"  Audio Size: {audio_size:,} bytes")
        print(f"  ElevenLabs Voice ID: {elevenlabs_voice_id}")
        
        # Step 6: Save the audio URL and metadata to database
        print(f"\nSaving to database...")
        try:
            FirebaseService.save_audio_url_async(
                joke_id,
                audio_url,
                audio_size,
                voice_id,  # Use the user's voice_id
                elevenlabs_voice_id,
                False  # is_default=False
            )
            print(f"✓ Saved to database")
        except Exception as e:
            print(f"⚠ Warning: Error saving to database (non-critical): {str(e)}")
        
        return {
            'success': True,
            'audio_url': audio_url,
            'audio_size': audio_size,
            'elevenlabs_voice_id': elevenlabs_voice_id,
            'cached': False
        }
        
    except Exception as e:
        error_msg = f"Error generating audio: {str(e)}"
        print(f"✗ {error_msg}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': error_msg
        }

def main():
    """Main function to test audio generation for first joke with all voices."""
    print("="*60)
    print("Test Script: Generate Audio for Joke with Voices")
    print("="*60)
    
    # Initialize Firebase
    print("\n1. Initializing Firebase...")
    try:
        initialize_firebase()
        print("✓ Firebase initialized successfully")
    except Exception as e:
        print(f"✗ Failed to initialize Firebase: {str(e)}")
        return
    
    # Get the first joke
    print("\n2. Getting first joke from jokes collection...")
    joke = get_first_joke()
    if not joke:
        print("✗ No jokes found in the collection")
        return
    
    print(f"✓ Found joke:")
    print(f"  Joke ID: {joke['joke_id']}")
    print(f"  Setup: {joke['joke_setup']}")
    print(f"  Punchline: {joke['joke_punchline']}")
    
    # Get all voices
    print("\n3. Getting all voices from voices collection...")
    voices = get_all_voices()
    if not voices:
        print("✗ No voices found in the collection")
        return
    
    print(f"✓ Found {len(voices)} voice(s):")
    for voice in voices:
        print(f"  - {voice['voice_name']} (ID: {voice['voice_id']})")
    
    # Test audio generation for each voice
    print("\n4. Testing audio generation for each voice...")
    results = []
    
    for i, voice in enumerate(voices, 1):
        print(f"\n[{i}/{len(voices)}] Processing voice: {voice['voice_name']}")
        result = test_audio_generation_for_joke_with_voice(
            joke['joke_id'],
            voice['voice_id']
        )
        results.append({
            'voice_name': voice['voice_name'],
            'voice_id': voice['voice_id'],
            'result': result
        })
    
    # Print summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    success_count = 0
    for item in results:
        voice_name = item['voice_name']
        result = item['result']
        if result.get('success'):
            status = "✓ SUCCESS"
            if result.get('cached'):
                status += " (cached)"
            print(f"{status} - {voice_name}")
            print(f"  Audio URL: {result.get('audio_url', 'N/A')}")
            success_count += 1
        else:
            print(f"✗ FAILED - {voice_name}")
            print(f"  Error: {result.get('error', 'Unknown error')}")
    
    print(f"\n{'='*60}")
    print(f"Results: {success_count}/{len(voices)} successful")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()

