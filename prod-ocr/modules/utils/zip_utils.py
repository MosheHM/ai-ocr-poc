"""ZIP file utilities for packaging results."""
import os
import json
import zipfile
import logging
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)


def create_results_zip(
    output_dir: str,
    results_data: Dict[str, Any],
    zip_filename: str = "processing_results.zip"
) -> str:
    """Create a ZIP file containing all split PDFs and results JSON.

    Args:
        output_dir: Directory containing the split PDF files and results
        results_data: Dictionary containing the extraction results
        zip_filename: Name of the ZIP file to create

    Returns:
        Path to the created ZIP file

    Raises:
        Exception: If ZIP creation fails
    """
    try:
        output_dir = Path(output_dir)
        zip_path = output_dir / zip_filename

        logger.info(f"Creating results ZIP file: {zip_path}")

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            results_json = json.dumps(results_data, indent=2, ensure_ascii=False)
            zipf.writestr('extraction_results.json', results_json)
            logger.info("Added extraction_results.json to ZIP")

            source_pdf = results_data.get('source_pdf')
            if source_pdf and os.path.exists(source_pdf):
                source_filename = Path(source_pdf).name
                zipf.write(source_pdf, arcname=source_filename)
                logger.info(f"Added source file {source_filename} to ZIP")

        file_size_in_kb = os.path.getsize(zip_path) / 1024
        logger.info(f"Successfully created ZIP file: {zip_path} ({file_size_in_kb:.2f} KB)")

        return str(zip_path)

    except Exception as e:
        logger.error(f"Failed to create results ZIP: {e}")
        raise
