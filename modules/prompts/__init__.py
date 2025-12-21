"""Prompts module initialization."""
from .prompt_loader import (
    PromptLoader,
    load_prompt,
    get_classification_prompt,
    get_invoice_extraction_prompt,
    get_obl_extraction_prompt,
    get_hawb_extraction_prompt,
    get_packing_list_extraction_prompt
)

__all__ = [
    'PromptLoader',
    'load_prompt',
    'get_classification_prompt',
    'get_invoice_extraction_prompt',
    'get_obl_extraction_prompt',
    'get_hawb_extraction_prompt',
    'get_packing_list_extraction_prompt'
]
