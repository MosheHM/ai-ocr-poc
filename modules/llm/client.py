"""LLM client module for interacting with Google Gemini API."""
import json
from typing import Optional
from google import genai
from google.genai import types


class GeminiLLMClient:
    """Client for Google Gemini API."""
    
    def __init__(self, api_key: str):
        """Initialize the Gemini client.
        
        Args:
            api_key: Google Gemini API key
        """
        self.client = genai.Client(api_key=api_key)
    
    def generate_content(
        self,
        prompt: str,
        image_data: Optional[bytes] = None,
        mime_type: Optional[str] = None,
        model: str = "gemini-2.5-flash"
    ) -> str:
        """Generate content using Gemini API.
        
        Args:
            prompt: The text prompt
            image_data: Optional image/PDF data
            mime_type: MIME type of the image data
            model: Model to use (default: gemini-2.5-flash)
        
        Returns:
            Generated text response
        """
        parts = []
        
        # Add image/PDF data if provided
        if image_data and mime_type:
            parts.append(
                types.Part.from_bytes(
                    data=image_data,
                    mime_type=mime_type
                )
            )
        
        # Add text prompt
        parts.append(types.Part.from_text(text=prompt))
        
        # Generate content
        response = self.client.models.generate_content(
            model=model,
            contents=[
                types.Content(
                    role="user",
                    parts=parts
                )
            ]
        )
        
        return response.text.strip()
    
    def generate_json_content(
        self,
        prompt: str,
        image_data: Optional[bytes] = None,
        mime_type: Optional[str] = None,
        model: str = "gemini-2.5-flash"
    ) -> dict:
        """Generate JSON content using Gemini API.
        
        Args:
            prompt: The text prompt
            image_data: Optional image/PDF data
            mime_type: MIME type of the image data
            model: Model to use
        
        Returns:
            Parsed JSON response
        """
        response_text = self.generate_content(
            prompt=prompt,
            image_data=image_data,
            mime_type=mime_type,
            model=model
        )
        
        # Remove markdown code blocks if present
        cleaned_text = self._clean_json_response(response_text)
        
        try:
            return json.loads(cleaned_text)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON response: {e}\nResponse: {cleaned_text}")
    
    @staticmethod
    def _clean_json_response(text: str) -> str:
        """Remove markdown code blocks from JSON response.
        
        Args:
            text: Raw response text
        
        Returns:
            Cleaned JSON text
        """
        text = text.strip()
        
        # Remove ```json or ``` prefix
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        
        # Remove ``` suffix
        if text.endswith("```"):
            text = text[:-3]
        
        return text.strip()
