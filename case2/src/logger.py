from __future__ import annotations
import json
import logging
from .masking import mask_id

logger = logging.getLogger("invoice_extractor")


def log_extraction(path: str, invoice_jsonable: dict, method: str, latency_ms: float) -> None:
    """Log metadata only. Never log raw PDF, raw tax IDs, or amounts."""
    safe = {
        "event": "extraction_done",
        "path": path,
        "method": method,
        "latency_ms": round(latency_ms, 2),
        "invoice_number": invoice_jsonable.get("invoice_number"),
        "seller_tax_id_masked": mask_id((invoice_jsonable.get("seller") or {}).get("tax_id")),
        "client_tax_id_masked": mask_id((invoice_jsonable.get("client") or {}).get("tax_id")),
        "grand_total_present": invoice_jsonable.get("grand_total") is not None,
        "needs_review": invoice_jsonable.get("needs_review"),
        "overall_confidence": round(invoice_jsonable.get("overall_confidence", 0.0), 3),
    }
    logger.info(json.dumps(safe))