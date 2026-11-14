from pathlib import Path
import pymupdf
from fastapi import HTTPException, UploadFile

async def extract_text(file: UploadFile) -> str:
    name = (file.filename or "").lower()
    raw = await file.read()
    if name.endswith(".txt"):
        text = raw.decode("utf-8-sig", errors="replace")
    elif name.endswith(".pdf"):
        try:
            with pymupdf.open(stream=raw, filetype="pdf") as pdf:
                text = "\n".join(page.get_text() for page in pdf)
        except Exception as exc:
            raise HTTPException(status_code=422, detail="Could not read PDF file.") from exc
    else:
        raise HTTPException(status_code=415, detail="Only .pdf and .txt files are supported.")
    if not text.strip():
        raise HTTPException(status_code=422, detail="No extractable text found. Scanned PDFs require OCR.")
    return text
