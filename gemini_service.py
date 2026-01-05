import google.generativeai as genai
from typing import List
from models import GeminiJokeItem
from firebase.config import GEMINI_API_KEY
import json
import re

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
        
        # Configure Gemini
        genai.configure(api_key=GEMINI_API_KEY)
        
        # Create the models
        model = genai.GenerativeModel('gemini-2.5-flash')

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
            response = model.generate_content(prompt)
            
            # Extract JSON from response
            response_text = response.text.strip()
            
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
            response_text = response.text if 'response' in locals() else ""
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

