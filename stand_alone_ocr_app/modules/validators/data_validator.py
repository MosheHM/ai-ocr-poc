
"""Validation logic for extracted data."""
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

def validate_extraction_results(results: Dict[str, Any]) -> Dict[str, Any]:
    """Validate extracted data and append error information.
    
    Args:
        results: The raw extraction results dictionary.
        
    Returns:
        The results dictionary with validation errors added to fields.
    """
    logger.info("Starting validation of extraction results")
    
    if "documents" not in results:
        logger.warning("No documents found in results")
        return results

    total_errors = 0
    
    for doc in results["documents"]:
        if "DOC_DATA" not in doc:
            continue
            
        for field in doc["DOC_DATA"]:
            field_errors = []
            value = field.get("field_value")
            field_id = field.get("field_id", "UNKNOWN")
            
            if value is None or value == "":
                field_errors.append("Value is missing or empty")
            
            if field_id in ["WEIGHT", "PIECES", "INVOICE_AMOUNT"]:
                if value is not None and not isinstance(value, (int, float)):
                    try:
                        float(str(value).replace(',', ''))
                    except ValueError:
                        field_errors.append(f"Expected numeric value for {field_id}")

            if field_errors:
                field["errors"] = field_errors
                total_errors += len(field_errors)
            else:
                field["errors"] = []

    logger.info(f"Validation completed. Found {total_errors} errors/warnings.")
    return results
