from __future__ import annotations
from decimal import Decimal
from typing import List
from .schema import Invoice

RECON_TOL = Decimal("0.01")  # 1 sen toleransi


def validate(inv: Invoice) -> tuple[List[str], List[str]]:
    """Return (review_reasons, warnings)."""
    review: List[str] = []
    warn: List[str] = []

    # Critical fields present
    if not inv.invoice_number:
        review.append("missing_invoice_number")
    if not inv.issue_date_raw:
        review.append("missing_issue_date")
    if not inv.seller.name:
        review.append("missing_seller_name")
    if not inv.client.name:
        review.append("missing_client_name")
    if inv.grand_total is None:
        review.append("missing_grand_total")
    if not inv.line_items:
        review.append("no_line_items")

    # Any failed item
    for it in inv.line_items:
        if it.net_worth is None or it.gross_worth is None:
            review.append(f"line_item_invalid:{it.no}")

    # Reconcile line items vs subtotal / totals
    if inv.line_items and all(it.net_worth is not None for it in inv.line_items):
        s = sum(it.net_worth for it in inv.line_items)
        if inv.subtotal is not None and abs(s - inv.subtotal) > RECON_TOL:
            review.append(f"reconcile_subtotal_mismatch:{s}-{inv.subtotal}")
    if inv.line_items and all(it.gross_worth is not None for it in inv.line_items):
        g = sum(it.gross_worth for it in inv.line_items)
        if inv.grand_total is not None and abs(g - inv.grand_total) > RECON_TOL:
            review.append(f"reconcile_grand_total_mismatch:{g}-{inv.grand_total}")

    if inv.subtotal is not None and inv.tax_total is not None and inv.grand_total is not None:
        if abs(inv.subtotal + inv.tax_total - inv.grand_total) > RECON_TOL:
            review.append("reconcile_subtotal_plus_tax_ne_grand")

    if inv.date_format_assumed == "UNKNOWN":
        warn.append("date_format_unrecognized")
    if inv.currency is None:
        warn.append("currency_not_detected")

    return review, warn