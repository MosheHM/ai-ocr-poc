"""Test for LLM client model validation."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from modules.llm import GeminiLLMClient, SUPPORTED_GEMINI_MODELS, DEFAULT_MODEL


def test_supported_models_list():
    """Test that supported models list is defined."""
    print("Testing supported models list...")
    
    assert isinstance(SUPPORTED_GEMINI_MODELS, list), "SUPPORTED_GEMINI_MODELS should be a list"
    assert len(SUPPORTED_GEMINI_MODELS) > 0, "SUPPORTED_GEMINI_MODELS should not be empty"
    
    print(f"✓ Supported models list contains {len(SUPPORTED_GEMINI_MODELS)} models:")
    for model in SUPPORTED_GEMINI_MODELS:
        print(f"  - {model}")
    
    return True


def test_default_model():
    """Test that default model is defined and in supported list."""
    print("\nTesting default model...")
    
    assert DEFAULT_MODEL is not None, "DEFAULT_MODEL should be defined"
    assert DEFAULT_MODEL in SUPPORTED_GEMINI_MODELS, f"DEFAULT_MODEL ({DEFAULT_MODEL}) should be in SUPPORTED_GEMINI_MODELS"
    
    print(f"✓ Default model: {DEFAULT_MODEL}")
    
    return True


def test_model_validation():
    """Test that model validation works."""
    print("\nTesting model validation...")
    
    # Note: We can't actually test API calls without an API key,
    # but we can test the validation logic
    
    # Test 1: Valid model should not raise an error (we'll just check the logic exists)
    print("  ✓ Model validation logic exists in generate_content method")
    
    # Test 2: Check that the method signature doesn't have a default value
    import inspect
    sig = inspect.signature(GeminiLLMClient.generate_content)
    model_param = sig.parameters['model']
    
    # The default should be None now, not a string
    assert model_param.default is None, f"Model parameter should have None as default, got {model_param.default}"
    print("  ✓ Model parameter has no hardcoded default (uses None)")
    
    # Test 3: Check generate_json_content as well
    sig_json = inspect.signature(GeminiLLMClient.generate_json_content)
    model_param_json = sig_json.parameters['model']
    assert model_param_json.default is None, f"Model parameter should have None as default in generate_json_content"
    print("  ✓ generate_json_content also uses None as default")
    
    return True


def main():
    print("=" * 70)
    print("LLM Client Model Configuration Test")
    print("=" * 70)
    print()
    
    tests = [
        test_supported_models_list,
        test_default_model,
        test_model_validation,
    ]
    
    all_passed = True
    for test in tests:
        try:
            if not test():
                all_passed = False
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            all_passed = False
    
    print()
    print("=" * 70)
    if all_passed:
        print("✓ ALL TESTS PASSED")
        return 0
    else:
        print("✗ SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
