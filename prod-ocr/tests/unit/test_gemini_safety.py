import pytest
import json
from unittest.mock import MagicMock, patch
from modules.document_splitter.splitter import DocumentSplitter
from google.genai import types

@pytest.mark.unit
class TestGeminiSafetyIntegration:
    """Tests for Gemini integration with focus on safety settings and response handling."""

    @patch('modules.document_splitter.splitter.genai.Client')
    def test_safety_settings_configuration(self, MockClient):
        """
        Verify that safety settings are configured to BLOCK_NONE for all categories.
        This ensures the 'work for every doc type' requirement is met.
        """
        # Setup mock
        mock_client_instance = MockClient.return_value
        mock_models = mock_client_instance.models
        
        # Create a mock response that mimics the structure seen in logs
        mock_response = MagicMock()
        mock_response.text = "[]" # Empty JSON list
        mock_response.candidates = []
        mock_models.generate_content.return_value = mock_response

        # Initialize splitter
        splitter = DocumentSplitter(api_key="test_key")
        
        # Trigger the call
        try:
            splitter._call_gemini_with_pdf(b"pdf_content", "prompt")
        except ValueError:
            # We expect ValueError because response text is "[]" which might fail validation 
            # or just pass through. We care about the call arguments here.
            pass
            
        # Verify generate_content arguments
        assert mock_models.generate_content.called
        call_args = mock_models.generate_content.call_args
        kwargs = call_args.kwargs
        
        # Check config existence
        assert 'config' in kwargs
        config = kwargs['config']
        assert isinstance(config, types.GenerateContentConfig)
        
        # Check safety settings
        safety_settings = config.safety_settings
        assert len(safety_settings) == 4
        
        # Verify all categories are present and set to BLOCK_NONE
        expected_settings = {
            types.HarmCategory.HARM_CATEGORY_HATE_SPEECH: types.HarmBlockThreshold.BLOCK_NONE,
            types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: types.HarmBlockThreshold.BLOCK_NONE,
            types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: types.HarmBlockThreshold.BLOCK_NONE,
            types.HarmCategory.HARM_CATEGORY_HARASSMENT: types.HarmBlockThreshold.BLOCK_NONE,
        }
        
        found_settings = {}
        for setting in safety_settings:
            found_settings[setting.category] = setting.threshold
            
        assert found_settings == expected_settings, "Safety settings do not match expected BLOCK_NONE configuration"

    @patch('modules.document_splitter.splitter.genai.Client')
    def test_response_diagnostics_with_real_log_structure(self, MockClient):
        """
        Verify that _log_response_diagnostics handles a response structure matching the logs.
        """
        mock_client_instance = MockClient.return_value
        mock_models = mock_client_instance.models
        
        # Construct a mock response based on the provided logs
        mock_response = MagicMock()
        
        # Mock Candidate
        mock_candidate = MagicMock()
        mock_candidate.finish_reason = types.FinishReason.STOP
        mock_candidate.finish_message = "STOP"
        mock_candidate.index = 0
        
        # Mock Content and Part
        mock_part = MagicMock()
        mock_part.text = """```json
[
  {
    "doc_type": "hawb",
    "customer_name": "CARASSO MOTORS LTD",
    "doc_type_confidence": 0.95
  }
]
```"""
        mock_content = MagicMock()
        mock_content.parts = [mock_part]
        mock_content.role = 'model'
        
        mock_candidate.content = mock_content
        
        # Safety ratings (simulated as empty/safe as per successful log)
        mock_candidate.safety_ratings = []
        
        mock_response.candidates = [mock_candidate]
        mock_response.text = mock_part.text
        mock_response.prompt_feedback = None
        
        mock_models.generate_content.return_value = mock_response

        # Initialize splitter
        splitter = DocumentSplitter(api_key="test_key")
        
        # Call the method
        result = splitter._call_gemini_with_pdf(b"pdf_content", "prompt")
        
        # Verify result is cleaned text
        assert "HAWB" in result
        assert "```json" in result # _call_gemini_with_pdf returns raw text, cleaning happens in extract_documents

    @patch('modules.document_splitter.splitter.genai.Client')
    def test_response_diagnostics_with_safety_ratings(self, MockClient):
        """
        Verify that _log_response_diagnostics correctly extracts safety ratings if present.
        """
        mock_client_instance = MockClient.return_value
        mock_models = mock_client_instance.models
        
        # Mock response with safety ratings
        mock_response = MagicMock()
        mock_candidate = MagicMock()
        mock_candidate.finish_reason = types.FinishReason.STOP
        
        # Create safety ratings
        rating1 = MagicMock()
        rating1.category = types.HarmCategory.HARM_CATEGORY_HATE_SPEECH
        rating1.probability = types.HarmProbability.NEGLIGIBLE
        rating1.blocked = False
        
        rating2 = MagicMock()
        rating2.category = types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT
        rating2.probability = types.HarmProbability.LOW
        rating2.blocked = False
        
        mock_candidate.safety_ratings = [rating1, rating2]
        mock_response.candidates = [mock_candidate]
        mock_response.text = "Safe content"
        
        mock_models.generate_content.return_value = mock_response
        
        splitter = DocumentSplitter(api_key="test_key")
        
        # We need to spy on _log_response_diagnostics or check the logs
        # Here we'll call _log_response_diagnostics directly to verify its output
        diagnostics = splitter._log_response_diagnostics(mock_response, "model-name")
        
        assert "safety_ratings" in diagnostics
        ratings = diagnostics["safety_ratings"]
        assert len(ratings) == 2
        assert ratings[0]["category"] == str(types.HarmCategory.HARM_CATEGORY_HATE_SPEECH)
        assert ratings[1]["category"] == str(types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT)
