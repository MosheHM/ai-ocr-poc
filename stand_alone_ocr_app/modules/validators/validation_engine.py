
import pandas as pd
import pandera as pa
import logging
from typing import Dict, List, Any, Type
from ..schemas.base import ValidationResult, ValidationStatus
from ..schemas.invoice import InvoiceSchema, InvoiceRecord
from ..schemas.hawb import HAWBSchema, HAWBRecord
from ..schemas.obl import OBLSchema, OBLRecord
from ..schemas.packing_list import PackingListSchema, PackingListRecord

logger = logging.getLogger(__name__)

class ValidationEngine:
    """Orchestrates multi-layer validation."""
    
    SCHEMA_MAP = {
        'INVOICE': (InvoiceSchema, InvoiceRecord),
        'HAWB': (HAWBSchema, HAWBRecord),
        'OBL': (OBLSchema, OBLRecord),
        'PACKING_LIST': (PackingListSchema, PackingListRecord),
    }

    def validate_all(self, dataframes: Dict[str, pd.DataFrame]) -> tuple[Dict[str, pd.DataFrame], List[ValidationResult]]:
        """Run validation for all document types found."""
        validated_dfs = {}
        all_errors = []

        for doc_type, df in dataframes.items():
            if doc_type in self.SCHEMA_MAP:
                schema_cls, record_cls = self.SCHEMA_MAP[doc_type]
                logger.info(f"Validating {len(df)} {doc_type} records against schema")
                
                v_df, errors = self._validate_single_type(df, schema_cls, record_cls, doc_type)
                validated_dfs[doc_type] = v_df
                all_errors.extend(errors)
            else:
                logger.warning(f"No schema found for doc type: {doc_type}")
                validated_dfs[doc_type] = df

        return validated_dfs, all_errors

    def _validate_single_type(self, df: pd.DataFrame, schema: Type[pa.DataFrameModel], record_model: Type, doc_type: str) -> tuple[pd.DataFrame, List[ValidationResult]]:
        errors = []
        
        try:
            validated_df = schema.validate(df, lazy=True)
        except pa.errors.SchemaErrors as exc:
            self._collect_pandera_errors(exc, errors, doc_type)
            validated_df = df

        for idx, row in validated_df.iterrows():
            try:
                row_dict = {k: v for k, v in row.to_dict().items() if not pd.isna(v) and not k.startswith('_')}
                row_dict['row_index'] = idx
                record_model(**row_dict)
            except Exception as e:
                errors.append(ValidationResult(
                    doc_type=doc_type,
                    row=idx,
                    column="Business Logic",
                    status=ValidationStatus.FAILED,
                    message=str(e),
                    original_value="Row Record"
                ))
                
        return validated_df, errors

    def _collect_pandera_errors(self, exc: pa.errors.SchemaErrors, error_list: List[ValidationResult], doc_type: str):
        """Convert pandera errors to our ValidationResult format."""
        for error in exc.failure_cases.to_dict('records'):
            row_idx = error.get('index')
            if pd.isna(row_idx): row_idx = -1
            
            error_list.append(ValidationResult(
                doc_type=doc_type,
                row=int(row_idx),
                column=str(error.get('column', 'unknown')),
                status=ValidationStatus.FAILED,
                message=str(error.get('check', 'schema check failed')),
                original_value=error.get('failure_case'),
            ))
