"""Validators module initialization."""
from .validator import PerformanceValidator
from .xml_parser import (
    PageInfo,
    SplitDocumentInfo,
    SplittedResultInfo,
    parse_splitted_result_xml
)
from .splitting_validator import (
    DocumentMatch,
    SplittingValidationResult,
    SplittingValidator
)

__all__ = [
    'PerformanceValidator',
    'PageInfo',
    'SplitDocumentInfo',
    'SplittedResultInfo',
    'parse_splitted_result_xml',
    'DocumentMatch',
    'SplittingValidationResult',
    'SplittingValidator',
]
