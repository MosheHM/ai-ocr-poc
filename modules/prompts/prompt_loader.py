"""Prompt loader module for managing system prompts."""
from pathlib import Path
from typing import Dict
from functools import lru_cache


class PromptLoader:
    """Loads and caches prompts from text files."""
    
    def __init__(self, prompts_dir: Path = None):
        """Initialize the prompt loader.
        
        Args:
            prompts_dir: Directory containing prompt files. 
                        Defaults to modules/prompts directory.
        """
        if prompts_dir is None:
            # Default to prompts directory in modules
            prompts_dir = Path(__file__).parent
        self.prompts_dir = Path(prompts_dir)
        self._cache: Dict[str, str] = {}
    
    @lru_cache(maxsize=32)
    def load_prompt(self, prompt_name: str) -> str:
        """Load a prompt from a text file.
        
        Args:
            prompt_name: Name of the prompt file (without .txt extension)
        
        Returns:
            The prompt text
            
        Raises:
            FileNotFoundError: If the prompt file doesn't exist
        """
        prompt_path = self.prompts_dir / f"{prompt_name}.txt"
        
        if not prompt_path.exists():
            raise FileNotFoundError(
                f"Prompt file not found: {prompt_path}\n"
                f"Available prompts: {self.list_available_prompts()}"
            )
        
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    
    def list_available_prompts(self) -> list:
        """List all available prompt files.
        
        Returns:
            List of prompt names (without .txt extension)
        """
        if not self.prompts_dir.exists():
            return []
        
        return [
            p.stem for p in self.prompts_dir.glob("*.txt")
        ]
    
    def reload_prompt(self, prompt_name: str) -> str:
        """Force reload a prompt, bypassing cache.
        
        Args:
            prompt_name: Name of the prompt file
            
        Returns:
            The reloaded prompt text
        """
        # Clear from cache
        self.load_prompt.cache_clear()
        return self.load_prompt(prompt_name)


# Global prompt loader instance
_prompt_loader = PromptLoader()


def load_prompt(prompt_name: str) -> str:
    """Load a prompt using the global prompt loader.
    
    Args:
        prompt_name: Name of the prompt file (without .txt extension)
    
    Returns:
        The prompt text
    """
    return _prompt_loader.load_prompt(prompt_name)


def get_classification_prompt() -> str:
    """Get the document classification prompt."""
    return load_prompt("classification_prompt")


def get_invoice_extraction_prompt() -> str:
    """Get the invoice extraction prompt."""
    return load_prompt("invoice_extraction_prompt")


def get_obl_extraction_prompt() -> str:
    """Get the OBL extraction prompt."""
    return load_prompt("obl_extraction_prompt")


def get_hawb_extraction_prompt() -> str:
    """Get the HAWB extraction prompt."""
    return load_prompt("hawb_extraction_prompt")


def get_packing_list_extraction_prompt() -> str:
    """Get the packing list extraction prompt."""
    return load_prompt("packing_list_extraction_prompt")
