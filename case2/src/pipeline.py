from __future__ import annotations
import time
from pathlib import Path
from .extractor import extract_text_and_tables, UnsupportedFileError, FileTooLargeError
from .parser import parse
from .validator import validate
from .schema import Invoice, LineItem, Party
from .logger import log_extraction

REVIEW_THRESHOLD = 0.70

_CONF_WEIGHTS = {
    "invoice_number": 1.5,
    "issue_date": 1.0,
    "seller_name": 1.0,
    "client_name": 1.0,
    "seller_tax_id": 0.5,
    "client_tax_id": 0.5,
    "currency": 0.3,
    "totals": 2.0,
}


def _score(conf: dict) -> float:
    total_w = sum(_CONF_WEIGHTS[k] for k in _CONF_WEIGHTS if k in conf)
    if total_w == 0:
        return 0.0
    s = sum(conf[k] * _CONF_WEIGHTS[k] for k in _CONF_WEIGHTS if k in conf)
    return round(s / total_w, 4)


def extract_invoice(path: str | Path) -> dict:
    """Main entry point. Returns a fully-populated JSON-serialisable dict."""
    t0 = time.perf_counter()
    text, tables, n_pages = extract_text_and_tables(path)
    merged, item_review = parse(text, tables)

    conf = {
        "invoice_number": merged.get("_conf_invoice_number", 0.0),
        "issue_date": merged.get("_conf_issue_date", 0.0),
        "seller_name": merged.get("_conf_seller_name", 0.0),
        "client_name": merged.get("_conf_client_name", 0.0),
        "seller_tax_id": merged.get("_conf_seller_tax_id", 0.0),
        "client_tax_id": merged.get("_conf_client_tax_id", 0.0),
        "currency": merged.get("_conf_currency", 0.0),
        "totals": merged.get("_conf_totals", 0.0),
    }
    overall = _score(conf)

    items = [
        LineItem(**{k: v for k, v in it.items()})
        for it in merged.get("line_items", [])
        if it.get("quantity") is not None and it.get("net_worth") is not None
    ]
    failed_items = [it for it in merged.get("line_items", [])
                    if it.get("net_worth") is None]

    inv = Invoice(
        invoice_number=merged.get("invoice_number"),
        issue_date_raw=merged.get("issue_date_raw"),
        issue_date_iso=merged.get("issue_date_iso"),
        date_format_assumed=merged.get("date_format_assumed"),
        currency=merged.get("currency"),
        seller=Party(
            name=merged.get("seller_name"),
            tax_id=merged.get("seller_tax_id"),
            gstin=merged.get("seller_gstin"),
        ),
        client=Party(
            name=merged.get("client_name"),
            tax_id=merged.get("client_tax_id"),
        ),
        line_items=items,
        subtotal=merged.get("subtotal"),
        tax_total=merged.get("tax_total"),
        grand_total=merged.get("grand_total"),
        field_confidence=conf,
        overall_confidence=overall,
    )

    review_reasons, warnings = validate(inv)
    review_reasons.extend(item_review)
    if overall < REVIEW_THRESHOLD and not review_reasons:
        review_reasons.append(f"low_overall_confidence:{overall}")

    inv.review_reasons = review_reasons
    inv.warnings = warnings
    inv.needs_review = bool(review_reasons)

    if not text.strip():
        inv.needs_review = True
        inv.review_reasons.append("no_text_layer")
        inv.warnings.append("document_may_be_scanned_image")

    latency_ms = (time.perf_counter() - t0) * 1000.0
    out = inv.to_jsonable()
    out["_meta"] = {"latency_ms": round(latency_ms, 2), "pages": n_pages}
    log_extraction(str(path), out, inv.extraction_method, latency_ms)
    return out


# --- Errors re-exported for CLI/API ----------------------------------------
__all__ = ["extract_invoice", "UnsupportedFileError", "FileTooLargeError"]