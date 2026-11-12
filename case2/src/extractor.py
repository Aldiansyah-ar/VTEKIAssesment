from __future__ import annotations
import re
from pathlib import Path
import pdfplumber

MAX_BYTES = 10 * 1024 * 1024
PDF_MAGIC = b"%PDF-"


class UnsupportedFileError(Exception):
    def __init__(self, code: str, message: str = ""):
        super().__init__(message or code)
        self.code = code


class FileTooLargeError(Exception):
    def __init__(self, size: int):
        super().__init__(f"file_too_large:{size}")
        self.size = size


def safe_open_pdf(path: str | Path) -> Path:
    p = Path(path)
    if not p.exists() or not p.is_file():
        raise UnsupportedFileError("file_not_found")
    if p.suffix.lower() != ".pdf":
        raise UnsupportedFileError("unsupported_extension")
    size = p.stat().st_size
    if size > MAX_BYTES:
        raise FileTooLargeError(size)
    with open(p, "rb") as f:
        head = f.read(5)
    if head != PDF_MAGIC:
        raise UnsupportedFileError("not_a_pdf_magic")
    return p


def extract_text_and_tables(path: str | Path) -> tuple[str, list[list[list[str]]], int]:
    """Return (full_text, tables, n_pages). Never logs raw content."""
    p = safe_open_pdf(path)
    full_text_parts: list[str] = []
    tables: list[list[list[str]]] = []
    with pdfplumber.open(str(p)) as pdf:
        n_pages = len(pdf.pages)
        for page in pdf.pages:
            try:
                t = page.extract_text() or ""
            except Exception:
                t = ""
            full_text_parts.append(t)
            try:
                page_tables = page.extract_tables() or []
                tables.extend(page_tables)
            except Exception:
                pass
    text = "\n".join(full_text_parts)
    return text, tables, n_pages


def normalize_lines(text: str) -> list[str]:
    return [re.sub(r"\s+", " ", ln).strip() for ln in text.splitlines()]