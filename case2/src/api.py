from __future__ import annotations
import os
import tempfile
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, Header, HTTPException
from .pipeline import extract_invoice, UnsupportedFileError, FileTooLargeError
from .masking import mask_invoice_for_viewer

API_KEYS = {
    os.environ.get("ANALYST_KEY", "dev-analyst-key"): "analyst",
    os.environ.get("VIEWER_KEY", "dev-viewer-key"): "viewer",
}

app = FastAPI(title="Invoice Extraction API (Case 2)")

MAX_BYTES = 10 * 1024 * 1024


def _role_from_header(x_api_key: str | None) -> str:
    if not x_api_key or x_api_key not in API_KEYS:
        raise HTTPException(status_code=401, detail="invalid_or_missing_api_key")
    return API_KEYS[x_api_key]


@app.post("/extract")
async def extract(file: UploadFile = File(...), x_api_key: str | None = Header(default=None)):
    role = _role_from_header(x_api_key)
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=415, detail="unsupported_content_type")
    content = await file.read()
    if len(content) > MAX_BYTES:
        raise HTTPException(status_code=413, detail="file_too_large")
    if not content.startswith(b"%PDF-"):
        raise HTTPException(status_code=415, detail="not_a_pdf_magic")

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=True) as tmp:
        tmp.write(content)
        tmp.flush()
        try:
            out = extract_invoice(tmp.name)
        except UnsupportedFileError as e:
            raise HTTPException(status_code=415, detail=e.code)
        except FileTooLargeError:
            raise HTTPException(status_code=413, detail="file_too_large")
        except Exception:
            raise HTTPException(status_code=500, detail="extraction_failed")

    if role == "viewer":
        out = mask_invoice_for_viewer(out)
    return {"role": role, "invoice": out}


@app.get("/health")
def health():
    return {"ok": True, "llm_enabled": False}