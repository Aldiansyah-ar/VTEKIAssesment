from __future__ import annotations
import re
from decimal import Decimal, InvalidOperation
from typing import Optional


_NUM = r"\d{1,3}(?:,\d{3})*\.\d{2}"


def _d(s: str) -> Optional[Decimal]:
    try:
        return Decimal(s.replace(",", "").strip())
    except (InvalidOperation, AttributeError):
        return None


def _find(pattern: str, text: str, flags=re.I) -> tuple[Optional[str], float]:
    m = re.search(pattern, text, flags)
    if m:
        return m.group(1).strip(), 0.95
    return None, 0.0


def parse_header(text: str) -> dict:
    out: dict = {}
    out["invoice_number"], c = _find(r"Invoice\s*no[.:\s]+([A-Z0-9][A-Z0-9\-/]*)", text)
    out["_conf_invoice_number"] = c

    raw_date, c = _find(r"Date\s*of\s*issue[.:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})", text)
    out["issue_date_raw"], out["_conf_issue_date"] = raw_date, c
    if raw_date:
        iso, fmt = _normalize_date(raw_date)
        out["issue_date_iso"] = iso
        out["date_format_assumed"] = fmt
    else:
        out["issue_date_iso"] = None
        out["date_format_assumed"] = None

    cur, c = _find(r"\b(INR|USD|EUR|GBP|IDR|SGD|MYR|THB|JPY|AUD)\b", text)
    out["currency"], out["_conf_currency"] = (cur.upper() if cur else None), (0.9 if cur else 0.5)

    seller, c = _find(r"Seller[.:\s]*\n?\s*([^\n]+)", text)
    out["seller_name"], out["_conf_seller_name"] = (seller, c)

    client, c = _find(r"Client[.:\s]*\n?\s*([^\n]+)", text)
    out["client_name"], out["_conf_client_name"] = (client, c)

    ids: list[str] = []
    for m in re.finditer(r"(?:GSTIN|Tax\s*Id)[.:\s]+([A-Z0-9\-]{6,20})", text, re.I):
        v = m.group(1).strip()
        if not ids or ids[-1] != v:
            ids.append(v)
    out["seller_tax_id"] = ids[0] if len(ids) >= 1 else None
    out["client_tax_id"] = ids[1] if len(ids) >= 2 else None
    out["seller_gstin"] = None
    m = re.search(r"GSTIN[.:\s]+([A-Z0-9]{15})", text, re.I)
    if m:
        out["seller_gstin"] = m.group(1).strip()

    out["_conf_seller_tax_id"] = 0.95 if out["seller_tax_id"] else 0.0
    out["_conf_client_tax_id"] = 0.95 if out["client_tax_id"] else 0.0
    return out


def _normalize_date(raw: str) -> tuple[str, str]:
    parts = re.split(r"[/-]", raw)
    if len(parts) != 3:
        return raw, "UNKNOWN"
    a, b, c = parts
    try:
        a_i, b_i = int(a), int(b)
        c_i = int(c) if len(c) == 4 else 2000 + int(c)
    except ValueError:
        return raw, "UNKNOWN"
    if a_i <= 12 and b_i <= 12 and a_i != b_i:
        fmt = "DMY" if a_i <= 31 and b_i <= 12 else "MDY"
    else:
        fmt = "DMY" if a_i > 12 else "MDY"
    d, mo = (a_i, b_i) if fmt == "DMY" else (b_i, a_i)
    try:
        return f"{c_i:04d}-{mo:02d}-{d:02d}", fmt
    except ValueError:
        return raw, "UNKNOWN"


_ITEM_RE = re.compile(
    r"^(?P<desc>.+?)\s+"
    r"(?P<qty>\d+\.\d+)\s+"
    r"(?P<um>[A-Za-z]+)\s+"
    rf"(?P<unit_price>{_NUM})\s+"
    rf"(?P<net_worth>{_NUM})\s+"
    r"(?P<vat>\d+)%\s+"
    rf"(?P<gross>{_NUM})$"
)


def parse_line_items(text: str) -> tuple[list[dict], list[str]]:
    """Return (items, review_reasons). Handles malformed nested-row tables."""
    raw_items: list[dict] = []
    current: Optional[dict] = None
    new_item_re = re.compile(r"^(\d+)\.\s+(.+)$")

    for raw_line in text.splitlines():
        line = re.sub(r"\s+", " ", raw_line).strip()
        if not line:
            continue
        # Skip header text
        if re.match(r"^No\.?\s+Description", line, re.I):
            continue
        m = new_item_re.match(line)
        if m:
            if current:
                raw_items.append(current)
            current = {"no": int(m.group(1)), "raw": m.group(2)}
        elif current is not None and re.search(r"\d", line):
            current["raw"] += " " + line

    if current:
        raw_items.append(current)

    items: list[dict] = []
    review: list[str] = []
    for it in raw_items:
        m = _ITEM_RE.search(it["raw"])
        if not m:
            review.append(f"line_item_unparsed:{it['no']}")
            items.append({
                "no": it["no"], "description": it["raw"][:120],
                "quantity": None, "unit": None, "unit_price": None,
                "net_worth": None, "vat_rate": None, "gross_worth": None,
                "confidence": 0.0,
            })
            continue
        g = m.groupdict()
        items.append({
            "no": it["no"],
            "description": g["desc"].strip(),
            "quantity": _d(g["qty"]),
            "unit": g["um"],
            "unit_price": _d(g["unit_price"]),
            "net_worth": _d(g["net_worth"]),
            "vat_rate": _d(g["vat"]),
            "gross_worth": _d(g["gross"]),
            "confidence": 0.9,
        })
    return items, review


def parse_totals(text: str, tables: list[list[list[str]]]) -> dict:
    """Prefer structured table row containing 'Total'; fall back to text regex."""
    out = {"subtotal": None, "tax_total": None, "grand_total": None,
           "_conf_totals": 0.0, "_source": None}

    for tbl in tables:
        for row in tbl:
            cells = [c for c in row if c]
            if any(isinstance(c, str) and re.fullmatch(r"Total", c.strip(), re.I) for c in cells):
                nums = [c.strip() for c in cells if c and re.search(r"\d", c)]
                amounts = []
                for cell in nums:
                    m = re.search(r"([\d,]+\.\d{2})", cell)
                    if m:
                        amounts.append(_d(m.group(1)))
                if len(amounts) >= 3:
                    out["subtotal"], out["tax_total"], out["grand_total"] = amounts[-3:]
                    out["_conf_totals"] = 0.95
                    out["_source"] = "table"
                    return out

    m = re.search(
        rf"Total[^\n]*?([\d,]+\.\d{{2}})[^\n]*?([\d,]+\.\d{{2}})[^\n]*?([\d,]+\.\d{{2}})",
        text, re.I,
    )
    if m:
        out["subtotal"] = _d(m.group(1))
        out["tax_total"] = _d(m.group(2))
        out["grand_total"] = _d(m.group(3))
        out["_conf_totals"] = 0.85
        out["_source"] = "text"
        return out

    inr = re.findall(rf"INR\s*([\d,]+\.\d{{2}})", text)
    if len(inr) >= 3:
        out["subtotal"] = _d(inr[-3])
        out["tax_total"] = _d(inr[-2])
        out["grand_total"] = _d(inr[-1])
        out["_conf_totals"] = 0.6
        out["_source"] = "inr_heuristic"
        return out


    m = re.search(
        rf"^\s*10%\s+([\d,]+\.\d{{2}})\s+([\d,]+\.\d{{2}})\s+([\d,]+\.\d{{2}})\s*$",
        text, re.M,
    )
    if m:
        out["subtotal"] = _d(m.group(1))
        out["tax_total"] = _d(m.group(2))
        out["grand_total"] = _d(m.group(3))
        out["_conf_totals"] = 0.75
        out["_source"] = "summary_row"
    return out


def parse(text: str, tables: list[list[list[str]]]) -> tuple[dict, list[str]]:
    """Return (merged dict ready for schema, review_reasons)."""
    header = parse_header(text)
    items, item_review = parse_line_items(text)
    totals = parse_totals(text, tables)
    merged = {**header, **totals, "line_items": items}
    return merged, item_review