import google.genai as genai
from google.genai import types
from typing import List, Optional, Tuple
from models import GeminiJokeItem
from firebase.config import GEMINI_API_KEY
from firebase.firebase_init import get_firestore
from firebase_service import FirebaseService
import json
import re
import base64
import wave
import io

class GeminiService:
    
    @staticmethod
    def generate_jokes(
        age_range: str, 
        scenario: str, 
        num_jokes: int = 10,
        liked_jokes: List[dict] = None,
        disliked_jokes: List[dict] = None
    ) -> List[GeminiJokeItem]:
        """
        Generate jokes using Gemini AI based on age range, scenario, and user preferences
        
        Args:
            age_range: Age range (e.g., "5-8", "8-12", "all ages")
            scenario: Scenario/context (e.g., "school", "family", "vacation")
            num_jokes: Number of jokes to generate (default: 10)
            liked_jokes: List of jokes the user has liked (to generate similar style)
            disliked_jokes: List of jokes the user has disliked (to avoid similar style)
        
        Returns:
            List of GeminiJokeItem objects
        """
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not set in environment variables")
        
        # Create Gemini client
        client = genai.Client(api_key=GEMINI_API_KEY)

        # Note: Model listing code removed - this was likely for debugging

        # Build preference context
        preference_context = ""
        if liked_jokes and len(liked_jokes) > 0:
            liked_examples = "\n".join([
                f"- Setup: \"{j.get('joke_setup', '')}\" Punchline: \"{j.get('joke_punchline', '')}\""
                for j in liked_jokes[:5]  # Use up to 5 examples
            ])
            preference_context += f"\n\nUser's LIKED jokes (generate jokes in a similar style and humor):\n{liked_examples}"
        
        if disliked_jokes and len(disliked_jokes) > 0:
            disliked_examples = "\n".join([
                f"- Setup: \"{j.get('joke_setup', '')}\" Punchline: \"{j.get('joke_punchline', '')}\""
                for j in disliked_jokes[:5]  # Use up to 5 examples
            ])
            preference_context += f"\n\nUser's DISLIKED jokes (avoid generating jokes with similar style, topics, or humor):\n{disliked_examples}"
        
        # Create the prompt
        prompt = f"""Generate exactly {num_jokes} jokes that are appropriate for age range {age_range} and scenario "{scenario}".

For each joke, provide:
1. A setup (the question or statement that sets up the joke)
2. A punchline (the funny answer or conclusion)

Format the response as a JSON array where each joke has:
- "joke_setup": the setup text
- "joke_punchline": the punchline text
- "joke_content": optional additional context (can be empty string)

Example format:
[
  {{
    "joke_setup": "Why did the chicken cross the playground?",
    "joke_punchline": "To get to the other slide!",
    "joke_content": ""
  }},
  {{
    "joke_setup": "What do you call a sleeping bull?",
    "joke_punchline": "A bulldozer!",
    "joke_content": ""
  }}
]

Make sure the jokes are:
- Age-appropriate for {age_range}
- Related to the scenario: {scenario}
- Clean and family-friendly
- Funny and engaging{preference_context}

Return ONLY the JSON array, no additional text or explanation."""

        try:
            # Generate content
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt
            )
            
            # Extract JSON from response
            # In the new API, text is accessed via candidates[0].content.parts[0].text
            if not response.candidates or len(response.candidates) == 0:
                raise ValueError("No response candidates from Gemini")
            
            candidate = response.candidates[0]
            if not candidate.content or not candidate.content.parts:
                raise ValueError("No content parts in response")
            
            # Get text from the first part
            response_text = ""
            for part in candidate.content.parts:
                if hasattr(part, 'text') and part.text:
                    response_text = part.text
                    break
            
            if not response_text:
                raise ValueError("No text found in response")
            
            response_text = response_text.strip()
            
            # Remove markdown code blocks if present
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            elif response_text.startswith("```"):
                response_text = response_text[3:]
            
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            
            response_text = response_text.strip()
            
            # Parse JSON
            jokes_data = json.loads(response_text)
            
            # Convert to GeminiJokeItem objects
            jokes = []
            for joke_data in jokes_data:
                jokes.append(GeminiJokeItem(
                    joke_setup=joke_data.get("joke_setup", ""),
                    joke_punchline=joke_data.get("joke_punchline", ""),
                    joke_content=joke_data.get("joke_content", "")
                ))
            
            return jokes
            
        except json.JSONDecodeError as e:
            # If JSON parsing fails, try to extract jokes manually
            response_text = ""
            if 'response' in locals() and response:
                try:
                    if response.candidates and len(response.candidates) > 0:
                        candidate = response.candidates[0]
                        if candidate.content and candidate.content.parts:
                            for part in candidate.content.parts:
                                if hasattr(part, 'text') and part.text:
                                    response_text = part.text
                                    break
                except:
                    pass
            print(f"JSON parsing failed: {e}")
            print(f"Response text: {response_text[:500] if response_text else 'No response'}")
            
            # Try to extract jokes using regex as fallback
            if response_text:
                jokes = GeminiService._extract_jokes_from_text(response_text)
                if jokes:
                    return jokes
            
            raise ValueError(f"Failed to parse Gemini response as JSON: {str(e)}")
        except Exception as e:
            raise ValueError(f"Error generating jokes with Gemini: {str(e)}")
    
    @staticmethod
    def _extract_jokes_from_text(text: str) -> List[GeminiJokeItem]:
        """
        Fallback method to extract jokes from text if JSON parsing fails
        """
        jokes = []
        lines = text.split('\n')
        
        current_setup = None
        current_punchline = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Look for setup patterns
            if any(keyword in line.lower() for keyword in ['why', 'what', 'how', 'when', 'where', 'did', 'do', 'does']):
                if current_setup and current_punchline:
                    jokes.append(GeminiJokeItem(
                        joke_setup=current_setup,
                        joke_punchline=current_punchline,
                        joke_content=""
                    ))
                current_setup = line
                current_punchline = None
            elif current_setup and not current_punchline:
                current_punchline = line
        
        # Add the last joke
        if current_setup and current_punchline:
            jokes.append(GeminiJokeItem(
                joke_setup=current_setup,
                joke_punchline=current_punchline,
                joke_content=""
            ))
        
        return jokes[:10]  # Return up to 10 jokes
    
    @staticmethod
    def generate_audio_for_joke(joke_id: str, setup: str, punchline: str) -> Optional[Tuple[str, int]]:
        """
        Generate audio for a joke using Gemini's TTS model, upload to Firebase Storage,
        and save to database. Returns the audio URL and size.
        
        Args:
           joke_id: The ID of the joke
           setup: setup for the joke
           punchline: punchline for the joke
        
        Returns:
           Optional[Tuple[str, int]]: (audio_url, audio_size) or None if generation fails
        """
        try:
            if not GEMINI_API_KEY:
                raise ValueError("GEMINI_API_KEY is not set in environment variables")
            
            # Create Gemini client
            client = genai.Client(api_key=GEMINI_API_KEY)

            # Use the most basic config possible to ensure the SDK doesn't block it
            joke_config = {
                "response_modalities": ["AUDIO"],
                "speech_config": {
                    "voice_config": {
                        "prebuilt_voice_config": {
                            "voice_name": "Puck" # Puck is the most stable voice for 2.5
                        }
                    }
                }
            }

            # We put the "acting" instructions in the prompt text
            audio_prompt = f"""
            Perform this as a dramatic dialogue, make the voice funny and engaging. 
            Change your pitch and tone to distinguish between the characters.
            Character 1 (Woman): {setup}
            [pause]
            Character 2 (Man): {punchline}
            """

            response = client.models.generate_content(
                model="gemini-2.5-flash-preview-tts",
                contents=audio_prompt,
                config=joke_config
            )
            
            # 1. CHECK FOR ERROR/BLOCKING FIRST
            if hasattr(response, 'prompt_feedback') and response.prompt_feedback:
                if hasattr(response.prompt_feedback, 'block_reason') and response.prompt_feedback.block_reason:
                    print(f"BLOCKED: {response.prompt_feedback.block_reason} for joke {joke_id}")
                    return None  # Don't upload anything!
            
            # 2. CHECK IF AUDIO PART EXISTS
            if not hasattr(response, 'candidates') or not response.candidates or len(response.candidates) == 0:
                print(f"ERROR: No response candidates from Gemini for joke {joke_id}")
                raise ValueError("No response candidates from Gemini")
            
            candidate = response.candidates[0]
            if not hasattr(candidate, 'content') or not candidate.content:
                print(f"ERROR: No content in response candidate for joke {joke_id}")
                raise ValueError("No content in response candidate")
            
            # Extract audio data from the response
            audio_data = None
            if hasattr(candidate.content, 'parts') and candidate.content.parts:
                print(f"Get Parts: size = {len(candidate.content.parts)} parts")
                for part in candidate.content.parts:
                    if hasattr(part, 'inline_data') and part.inline_data:
                        if hasattr(part.inline_data, 'data'):
                            audio_data = part.inline_data.data
                            print(f"Get Inline Data.data: size = {len(audio_data)} bytes (base64 encoded)")
                            break
                    elif hasattr(part, 'data'):
                        print(f"Get Data: size = {len(part.data)} bytes (base64 encoded)")
                        audio_data = part.data
                        break
            
            if not audio_data:
                print(f"ERROR: Response contained text but no audio data for joke {joke_id}")
                raise ValueError("No audio data found in response")
            
            # Decode base64 audio data to bytes
            # If part.data is a string, it's base64 and needs decoding
            # If part.data is already 'bytes', don't decode it!
            if isinstance(audio_data, str):
                audio_data = base64.b64decode(audio_data)
            print(f"SUCCESS: Generated {len(audio_data)} bytes for joke {joke_id}")

            # ONLY UPLOAD IF SIZE IS REASONABLE (> 10000 bytes)
            if len(audio_data) <= 10000:
                print(f"ERROR: Audio too small for joke {joke_id}")
                print(f"Audio size: {len(audio_data)} bytes (minimum required: 10000 bytes)")
                print("Finish Reason:", response.candidates[0].finish_reason)
                print("Safety Ratings:", response.candidates[0].safety_ratings)
                return None
            
            wav_audio = GeminiService._convert_to_wav(audio_data)
            
            print(f"Original size: {len(audio_data)} | Wrapped size: {len(wav_audio)} for joke {joke_id}")
            
            # Upload to Firebase Storage bucket using FirebaseService
            file_path = f"jokes_audio/{joke_id}/default.wav"
            audio_url, audio_size = FirebaseService.save_to_bucket(file_path, wav_audio, content_type='audio/wav')
            
            return audio_url, audio_size
            
        except Exception as e:
            print(f"CRITICAL ERROR generating audio for joke {joke_id}: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    @staticmethod
    def _convert_to_wav(pcm_data):
        """
        Convert PCM audio data to WAV format.
        Gemini 2.5 TTS default: 24000Hz, 16-bit, Mono
        """
        with io.BytesIO() as wav_file:
            with wave.open(wav_file, 'wb') as wf:
                wf.setnchannels(1)          # Mono
                wf.setsampwidth(2)          # 16-bit (2 bytes)
                wf.setframerate(24000)      # 24kHz
                wf.writeframes(pcm_data)
            return wav_file.getvalue()
