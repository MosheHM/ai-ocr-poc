
import pandera as pa
import pandera.pandas as pa_pandas
from pandera.typing import Series
from pydantic import Field
from .base import BaseRecord

class OBLRecord(BaseRecord):
    """Business logic validation for OBL records."""
    customer_name: str = Field(..., description="Customer Name")
    weight: float = Field(..., description="Weight")
    volume: float = Field(..., description="Volume")
    incoterms: str = Field(..., pattern=r'^[A-Z]{3}$', description="Code only, uppercase")

class OBLSchema(pa_pandas.DataFrameModel):
    """DataFrame-level validation schema for OBLs."""
    customer_name: Series[str] = pa.Field(coerce=True)
    weight: Series[float] = pa.Field(coerce=True)
    volume: Series[float] = pa.Field(coerce=True)
    incoterms: Series[str] = pa.Field(str_matches=r'^[A-Z]{3}$', coerce=True)

    class Config:
        strict = False
