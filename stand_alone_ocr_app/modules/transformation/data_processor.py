
import pandas as pd
from typing import Dict, Any, List, Tuple

class DataProcessor:
    """Transform extracted JSON data into structured DataFrames."""

    @staticmethod
    def process_extraction_results(results: Dict[str, Any]) -> Dict[str, pd.DataFrame]:
        """
        Convert list of documents to a dictionary of DataFrames keyed by document type.
        
        Args:
           results: The raw JSON output from the splitter/extractor.
        
        Returns:
           Dictionary where keys are doc types (e.g., 'INVOICE') and values are DataFrames.
        """
        if "documents" not in results:
            return {}

        grouped_data: Dict[str, List[Dict[str, Any]]] = {}

        for doc_idx, doc in enumerate(results["documents"]):
            doc_type = doc.get("DOC_TYPE", "UNKNOWN").upper()
            
            # Pivot the DOC_DATA list into a single dictionary
            row_data = {"row_index": doc_idx} # Track original index
            
            # Add metadata columns
            row_data["_source_page"] = doc.get("START_PAGE_NO")
            
            # Pivot fields
            if "DOC_DATA" in doc and isinstance(doc["DOC_DATA"], list):
                for field in doc["DOC_DATA"]:
                    field_id = field.get("field_id", "").lower() # Normalize to lowercase for schema matching
                    field_value = field.get("field_value")
                    row_data[field_id] = field_value
            
            if doc_type not in grouped_data:
                grouped_data[doc_type] = []
            grouped_data[doc_type].append(row_data)

        # Convert lists to DataFrames
        dfs = {}
        for doc_type, rows in grouped_data.items():
            dfs[doc_type] = pd.DataFrame(rows)
            
        return dfs
