from __future__ import annotations
import os
import json
from pathlib import Path
from .masking import mask_id

AUDIT = Path("audit/llm_payload.jsonl")


class LLMDisabledError(RuntimeError):
    pass


def build_masked_payload(raw_text: str) -> dict:
    return {
        "task": "extract_invoice_fields",
        "schema_version": "invoice-extractor/1.0.0",
        "text": _mask_document_text(raw_text),
    }


def _mask_document_text(text: str) -> str:
    import re
    # Mask GSTIN / Tax Id patterns
    text = re.sub(r"\b\d{2}[A-Z]{5}\d{4}[A-Z]\d[Z][A-Z0-9]\b",
                  lambda m: mask_id(m.group(0)), text)
    text = re.sub(r"\b\d{3}-\d{2}-\d{4}\b", lambda m: mask_id(m.group(0)), text)
    return text


def extract_with_llm(raw_text: str) -> dict:
    if os.environ.get("ENABLE_LLM_EXTRACTION") != "1":
        raise LLMDisabledError(
            "LLM extraction is opt-in. Set ENABLE_LLM_EXTRACTION=1 to enable. "
            "The default regex path is offline and privacy-preserving."
        )
    payload = build_masked_payload(raw_text)
    AUDIT.parent.mkdir(exist_ok=True)
    with AUDIT.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"payload_preview": payload["text"][:200]}) + "\n")
    raise NotImplementedError("Wire your approved LLM client here.")