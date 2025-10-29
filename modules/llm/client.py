"""LLM client module for interacting with Google Gemini API."""
import json
from typing import Optional, Literal
from google import genai
from google.genai import types


# Supported Gemini models (maintained list)
SUPPORTED_GEMINI_MODELS = [
    "gemini-2.0-flash-exp",
    "gemini-1.5-flash",
    "gemini-1.5-flash-8b",
    "gemini-1.5-pro",
    "gemini-2.5-flash",
]

# Default model to use when not specified
DEFAULT_MODEL = "gemini-2.5-flash"


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
        model: Optional[str] = None
    ) -> str:
        """Generate content using Gemini API.
        
        Args:
            prompt: The text prompt
            image_data: Optional image/PDF data
            mime_type: MIME type of the image data
            model: Model to use. If not specified, uses DEFAULT_MODEL.
                   Must be one of SUPPORTED_GEMINI_MODELS.
        
        Returns:
            Generated text response
            
        Raises:
            ValueError: If model is not in SUPPORTED_GEMINI_MODELS
        """
        # Use default model if none specified
        if model is None:
            model = DEFAULT_MODEL
        
        # Validate model
        if model not in SUPPORTED_GEMINI_MODELS:
            raise ValueError(
                f"Unsupported model: {model}. "
                f"Supported models: {', '.join(SUPPORTED_GEMINI_MODELS)}"
            )
        
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
        model: Optional[str] = None
    ) -> dict:
        """Generate JSON content using Gemini API.
        
        Args:
            prompt: The text prompt
            image_data: Optional image/PDF data
            mime_type: MIME type of the image data
            model: Model to use. If not specified, uses DEFAULT_MODEL.
                   Must be one of SUPPORTED_GEMINI_MODELS.
        
        Returns:
            Parsed JSON response
            
        Raises:
            ValueError: If model is not supported or JSON parsing fails
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
