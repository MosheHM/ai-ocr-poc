
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict

class ValidationStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"

class ValidationResult(BaseModel):
    doc_type: str = "UNKNOWN"
    row: int
    column: str
    status: ValidationStatus
    message: str
    original_value: Optional[Any] = None

class BaseRecord(BaseModel):
    """Base model for all document records."""
    model_config = ConfigDict(extra='ignore')
    
    row_index: int
