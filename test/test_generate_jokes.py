#!/usr/bin/env python3
"""
Test script to generate jokes using Gemini and save them to the database.
Generates 5 jokes with age_range: 5-8, scenario: home.
"""

import os
import sys
import uuid
from pathlib import Path

# Add parent directory to path to import modules (since we're in test/ subdirectory)
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from firebase.firebase_init import initialize_firebase
from firebase_service import FirebaseService
from gemini_service import GeminiService
from datetime import datetime

def main():
    """Main function to generate jokes and save them to the database."""
    print("="*60)
    print("Test Script: Generate Jokes with Gemini")
    print("="*60)
    
    # Initialize Firebase
    print("\n1. Initializing Firebase...")
    try:
        initialize_firebase()
        print("✓ Firebase initialized successfully")
    except Exception as e:
        print(f"✗ Failed to initialize Firebase: {str(e)}")
        return
    
    # Parameters for joke generation
    age_range = "5-8"
    scenario = "home"
    num_jokes = 5
    
    print(f"\n2. Generating {num_jokes} jokes...")
    print(f"   Age Range: {age_range}")
    print(f"   Scenario: {scenario}")
    
    try:
        # Generate jokes using Gemini
        gemini_jokes = GeminiService.generate_jokes(
            age_range=age_range,
            scenario=scenario,
            num_jokes=num_jokes,
            liked_jokes=None,
            disliked_jokes=None
        )
        
        print(f"✓ Successfully generated {len(gemini_jokes)} joke(s)")
        
        # Display the generated jokes
        print(f"\n3. Generated Jokes:")
        print("="*60)
        for i, joke in enumerate(gemini_jokes, 1):
            print(f"\nJoke {i}:")
            print(f"  Setup: {joke.joke_setup}")
            print(f"  Punchline: {joke.joke_punchline}")
            if joke.joke_content:
                print(f"  Content: {joke.joke_content}")
            if joke.emoji:
                print(f"  Emoji: {joke.emoji}")
        
        # Prepare joke data for saving
        print(f"\n4. Saving jokes to database...")
        jokes_to_save = []
        for gemini_joke in gemini_jokes:
            joke_id = str(uuid.uuid4())
            jokes_to_save.append({
                "joke_id": joke_id,
                "joke_setup": gemini_joke.joke_setup,
                "joke_punchline": gemini_joke.joke_punchline,
                "joke_content": gemini_joke.joke_content or "",
                "emoji": gemini_joke.emoji or "",
                "scenarios": [scenario],
                "age_range": [age_range]
            })
        
        # Save jokes to database (save_jokes_async is not actually async, just named that way)
        saved_count = FirebaseService.save_jokes_async(
            jokes_to_save,
            creator_id="test_script"
        )
        
        print(f"✓ Saved {saved_count}/{len(gemini_jokes)} joke(s) to database")
        
        # Print summary
        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)
        print(f"Generated: {len(gemini_jokes)} joke(s)")
        print(f"Saved: {saved_count} joke(s)")
        print(f"Age Range: {age_range}")
        print(f"Scenario: {scenario}")
        print("="*60)
        
        # Show joke IDs that were saved
        if saved_count > 0:
            print("\nSaved Joke IDs:")
            for joke_data in jokes_to_save[:saved_count]:
                print(f"  - {joke_data['joke_id']}")
                if joke_data.get('emoji'):
                    print(f"    Emoji: {joke_data['emoji']}")
        
    except Exception as e:
        print(f"\n✗ Error generating or saving jokes: {str(e)}")
        import traceback
        traceback.print_exc()
        return

if __name__ == "__main__":
    main()

