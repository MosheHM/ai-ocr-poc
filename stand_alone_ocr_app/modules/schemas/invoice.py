
from typing import Optional
import pandera as pa
import pandera.pandas as pa_pandas
from pandera.typing import Series
from pydantic import Field, field_validator
from .base import BaseRecord

class InvoiceRecord(BaseRecord):
    """Business logic validation for Invoice records."""
    invoice_no: str = Field(..., description="Extract as-is, preserving all characters")
    invoice_date: str = Field(..., pattern=r'^\d{16}$', description="YYYYMMDDHHMMSSSS (16 digits)")
    currency_id: str = Field(..., min_length=3, max_length=3, description="3-letter currency code")
    incoterms: str = Field(..., pattern=r'^[A-Z]{3}$', description="Code only, uppercase")
    invoice_amount: float = Field(..., description="Number, no symbols")
    customer_id: str = Field(..., description="Extract as-is")

    @field_validator('invoice_date')
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        if len(v) != 16 or not v.isdigit():
            raise ValueError(f"Date must be 16 digits, got: {v}")
        return v

class InvoiceSchema(pa_pandas.DataFrameModel):
    """DataFrame-level validation schema for Invoices."""
    invoice_no: Series[str] = pa.Field(coerce=True)
    invoice_date: Series[str] = pa.Field(str_matches=r'^\d{16}$', coerce=True)
    currency_id: Series[str] = pa.Field(str_length=3, coerce=True)
    incoterms: Series[str] = pa.Field(str_matches=r'^[A-Z]{3}$', coerce=True)
    invoice_amount: Series[float] = pa.Field(coerce=True)
    customer_id: Series[str] = pa.Field(coerce=True)

    class Config:
        strict = False 
