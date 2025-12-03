# Prod OCR Runner

This folder contains a self-contained version of the document splitting workflow so it can be deployed or shared independently of the rest of the repository.

## Structure

- `split_documents.py` – CLI entry point for splitting PDFs.
- `modules/` – minimal subset of modules required to run the splitter (document splitter + PDF utilities).
- `requirements.txt` – runtime dependencies.
- `.env` – **not committed**. Copy `.env.example` and set `GEMINI_API_KEY`.

## Usage

```bash
pip install -r requirements.txt
cp .env.example .env  # or create manually
python split_documents.py "path/to/file.pdf" --output-dir="out"
```

The script defaults to writing results into `prod-ocr/split_output` when no `--output-dir` is provided.
