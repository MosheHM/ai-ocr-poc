
import pandera as pa
import pandera.pandas as pa_pandas
from pandera.typing import Series
from pydantic import Field, field_validator
from .base import BaseRecord

class ExternalFreightInvoiceRecord(BaseRecord):
    """Business logic validation for External Freight Invoice records."""
    dealnumber: str = Field(..., pattern=r'^I\d{15}$', description="Starts with I followed by 15 digits")

    @field_validator('dealnumber')
    @classmethod
    def validate_dealnumber(cls, v: str) -> str:
        if not v.startswith('I') or len(v) != 16 or not v[1:].isdigit():
            raise ValueError(f"Deal number must be 'I' + 15 digits, got: {v}")
        return v

class ExternalFreightInvoiceSchema(pa_pandas.DataFrameModel):
    """DataFrame-level validation schema for External Freight Invoices."""
    dealnumber: Series[str] = pa.Field(str_matches=r'^I\d{15}$', coerce=True)

    class Config:
        strict = False
