import google.genai as genai
from google.genai import types
from typing import List, Optional
from models import GeminiJokeItem
from firebase.config import GEMINI_API_KEY
from firebase.firebase_init import get_storage_bucket, get_firestore
import json
import re
import base64

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
    def generate_audio_for_joke(joke_id: str, setup: str, punchline: str) -> Optional[str]:
        """
        Generate audio for a joke using Gemini's TTS model, upload to Firebase Storage,
        and update Firestore with the audio URL.
        
        Args:
           setup: setup for the joke
           punchline: punchline for the joke
        """
        try:
            if not GEMINI_API_KEY:
                raise ValueError("GEMINI_API_KEY is not set in environment variables")
            
            # Create Gemini client
            client = genai.Client(api_key=GEMINI_API_KEY)
            
            # 1. Generate the audio content using Gemini TTS

                    # 1. Use a raw dictionary for the entire config 
            # to bypass the SDK's strict Pydantic validation
            joke_config = {
                "response_modalities": ["AUDIO"],
                "speech_config": {
                    "voice_config": {
                        "prebuilt_voice_config": {
                            # For multiple voices, Gemini 2.5 often prefers 
                            # a single high-quality voice that you "direct" via the prompt.
                            "voice_name": "Puck" 
                        }
                    }
                }
            }

            # 2. Use "Prompt Engineering" to switch voices
            # Gemini 2.5 Flash is smart enough to change voices if you label them
            audio_prompt = f"""
            Please perform this joke with two different voices:
            WOMAN: {setup}
            [short pause]
            KID: {punchline}
            """
            # Generate audio with TTS model
            response = client.models.generate_content(
                model="gemini-2.5-flash-preview-tts",
                contents=audio_prompt,
                config=joke_config
            )
            
            # 2. Extract the audio data
            # The response should contain audio data
            if not hasattr(response, 'candidates') or not response.candidates or len(response.candidates) == 0:
                raise ValueError("No response candidates from Gemini")
            
            candidate = response.candidates[0]
            if not hasattr(candidate, 'content') or not candidate.content:
                raise ValueError("No content in response candidate")
            
            # Extract audio data from the response
            audio_data = None
            if hasattr(candidate.content, 'parts'):
                for part in candidate.content.parts:
                    if hasattr(part, 'inline_data') and part.inline_data:
                        if hasattr(part.inline_data, 'data'):
                            audio_data = part.inline_data.data
                            break
                    elif hasattr(part, 'data'):
                        audio_data = part.data
                        break
            
            if not audio_data:
                raise ValueError("No audio data found in response")
            
            # Decode base64 audio data to bytes
            audio_bytes = base64.b64decode(audio_data)
            
            # 3. Upload to Firebase Storage
            bucket = get_storage_bucket()
            file_path = f"jokes_audio/{joke_id}/default.mp3"
            blob = bucket.blob(file_path)
            
            # Upload the audio file
            blob.upload_from_string(
                audio_bytes,
                content_type='audio/mp3'
            )
            
            # Make the file publicly accessible
            blob.make_public()
            
            # Get the public URL
            audio_url = blob.public_url
            
            # 4. Update Firestore
            db = get_firestore()
            db.collection("jokes").document(joke_id).update({"audioUrl": audio_url})
            
            return audio_url
            
        except Exception as e:
            print(f"Error generating audio for joke {joke_id}: {str(e)}")
            return None

