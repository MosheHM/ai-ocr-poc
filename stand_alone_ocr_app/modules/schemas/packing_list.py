
import pandera as pa
import pandera.pandas as pa_pandas
from pandera.typing import Series
from pydantic import Field
from .base import BaseRecord

class PackingListRecord(BaseRecord):
    """Business logic validation for Packing List records."""
    customer_name: str = Field(..., description="Customer Name")
    pieces: int = Field(..., description="Number of pieces")
    weight: float = Field(..., description="Weight")

class PackingListSchema(pa_pandas.DataFrameModel):
    """DataFrame-level validation schema for Packing Lists."""
    customer_name: Series[str] = pa.Field(coerce=True)
    pieces: Series[int] = pa.Field(coerce=True)
    weight: Series[float] = pa.Field(coerce=True)

    class Config:
        strict = False
