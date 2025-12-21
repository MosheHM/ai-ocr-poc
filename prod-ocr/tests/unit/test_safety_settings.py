import pytest
from unittest.mock import MagicMock, patch
from modules.document_splitter.splitter import DocumentSplitter
from google.genai import types

@pytest.mark.unit
class TestSafetySettings:
    """Tests for safety settings configuration in DocumentSplitter."""

    def test_safety_settings_configuration(self):
        """Test that safety settings are correctly configured to BLOCK_NONE for all categories."""
        # Mock the client
        with patch('modules.document_splitter.splitter.genai.Client') as MockClient:
            # Setup the mock
            mock_client_instance = MockClient.return_value
            mock_models = mock_client_instance.models
            
            # Setup return value to avoid errors in _log_response_diagnostics and subsequent processing
            mock_response = MagicMock()
            mock_response.text = "{}"
            mock_response.candidates = []
            mock_response.prompt_feedback = None
            mock_models.generate_content.return_value = mock_response

            # Initialize splitter
            splitter = DocumentSplitter(api_key="test_key")
            
            # Call the method that triggers the API call
            # We use _call_gemini_with_pdf directly to verify the call arguments
            splitter._call_gemini_with_pdf(b"dummy pdf content", "dummy prompt")
            
            # Verify generate_content was called
            assert mock_models.generate_content.called
            
            # Get the call arguments
            call_args = mock_models.generate_content.call_args
            kwargs = call_args.kwargs
            
            # Check config
            assert 'config' in kwargs
            config = kwargs['config']
            assert isinstance(config, types.GenerateContentConfig)
            
            # Check safety settings
            safety_settings = config.safety_settings
            assert len(safety_settings) == 4
            
            # Verify each category is set to BLOCK_NONE
            expected_categories = {
                types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                types.HarmCategory.HARM_CATEGORY_HARASSMENT
            }
            
            found_categories = set()
            for setting in safety_settings:
                assert setting.threshold == types.HarmBlockThreshold.BLOCK_NONE
                found_categories.add(setting.category)
            
            assert found_categories == expected_categories
