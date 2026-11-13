def mask_id(value: str | None, keep_left: int = 4, keep_right: int = 4) -> str | None:
    if not value:
        return value
    s = str(value)
    if len(s) <= keep_left + keep_right:
        return "*" * len(s)
    return s[:keep_left] + "*" * (len(s) - keep_left - keep_right) + s[-keep_right:]


def mask_invoice_for_viewer(inv_jsonable: dict) -> dict:
    """Return the invoice payload with PII masked for role 'viewer'."""
    out = {**inv_jsonable}
    for role in ("seller", "client"):
        party = dict(out.get(role) or {})
        for key in ("tax_id", "gstin"):
            if party.get(key):
                party[key] = mask_id(party[key])
        if party.get("name"):
            n = party["name"]
            party["name"] = (n[:3] + "*" * max(0, len(n) - 5) + n[-2:]) if len(n) > 6 else "*" * len(n)
        out[role] = party
    return out