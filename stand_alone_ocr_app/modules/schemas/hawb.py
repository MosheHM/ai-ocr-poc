
import pandera as pa
import pandera.pandas as pa_pandas
from pandera.typing import Series
from pydantic import Field
from .base import BaseRecord

class HAWBRecord(BaseRecord):
    """Business logic validation for HAWB records."""
    customer_name: str = Field(..., description="Customer Name")
    currency: str = Field(..., description="Currency string")
    carrier: str = Field(..., description="Carrier Name")
    hawb_number: str = Field(..., description="HAWB Number")
    pieces: int = Field(..., description="Number of pieces")
    weight: float = Field(..., description="Weight")

class HAWBSchema(pa_pandas.DataFrameModel):
    """DataFrame-level validation schema for HAWBs."""
    customer_name: Series[str] = pa.Field(coerce=True)
    currency: Series[str] = pa.Field(coerce=True)
    carrier: Series[str] = pa.Field(coerce=True)
    hawb_number: Series[str] = pa.Field(coerce=True)
    pieces: Series[int] = pa.Field(coerce=True)
    weight: Series[float] = pa.Field(coerce=True)

    class Config:
        strict = False
