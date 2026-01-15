"""Stand-alone OCR FastAPI Application."""
import logging
import shutil
import tempfile
import secrets
import os
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse

from modules.document_splitter.splitter import DocumentSplitter
from modules.transformation.data_processor import DataProcessor
from modules.validators.validation_engine import ValidationEngine
from modules.utils.report_builder import ExcelReportBuilder
from modules.utils.zip_utils import create_results_zip
from modules.validators.input_validator import validate_pdf_file
from modules.config import get_app_config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI OCR POC API")


def create_secure_temp_dir() -> Path:
    """Create temporary directory with secure permissions."""
    temp_base = Path(tempfile.gettempdir())
    random_suffix = secrets.token_hex(16)
    temp_dir = temp_base / f"ocr_app_{random_suffix}"
    temp_dir.mkdir(mode=0o700, parents=True, exist_ok=False)
    return temp_dir


def cleanup_temp_dir(temp_dir: Path) -> None:
    """Safely cleanup temporary directory."""
    try:
        if temp_dir and temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)
            logger.debug(f"Cleaned up temporary directory: {temp_dir}")
    except Exception as e:
        logger.warning(f"Failed to cleanup temp directory {temp_dir}: {e}")


@app.post("/process_pdf", response_class=FileResponse)
async def process_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """
    Process an uploaded PDF file:
    1. Split documents
    2. Extract data
    3. Validate data
    4. Generate Excel report
    5. Return ZIP with results
    """
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")

    temp_dir = create_secure_temp_dir()
    background_tasks.add_task(cleanup_temp_dir, temp_dir)

    try:
        # Save uploaded file
        input_pdf_path = temp_dir / "input.pdf"
        with open(input_pdf_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Validate PDF
        try:
            validate_pdf_file(str(input_pdf_path))
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

        # Get config
        try:
            config = get_app_config()
        except Exception as e:
            logger.error(f"Configuration error: {e}")
            raise HTTPException(status_code=500, detail="Server configuration error")

        # Initialize components
        splitter = DocumentSplitter(
            api_key=config.gemini_api_key,
            model=config.gemini_model,
            timeout_seconds=config.gemini_timeout_seconds
        )
        
        # Process PDF
        output_dir = temp_dir / "output"
        output_dir.mkdir()
        
        logger.info(f"Processing PDF: {file.filename}")
        results = splitter.split_and_save(str(input_pdf_path), str(output_dir), base_filename=Path(file.filename).stem)

        # Transform and Validate
        dataframes = DataProcessor.process_extraction_results(results)
        validator = ValidationEngine()
        validated_dfs, validation_errors = validator.validate_all(dataframes)

        # Build Report
        report_builder = ExcelReportBuilder()
        report_builder.build_report(
            validated_dfs,
            validation_errors,
            output_dir / "extraction_report.xlsx"
        )

        # Package Results
        zip_path = create_results_zip(str(output_dir), results, "results.zip")
        
        return FileResponse(
            zip_path,
            media_type='application/zip',
            filename=f"{Path(file.filename).stem}_results.zip"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error processing PDF")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")
