from __future__ import annotations
import json
import sys
from decimal import Decimal
from pathlib import Path
from src.pipeline import extract_invoice

NUMERIC_FIELDS = {"subtotal", "tax_total", "grand_total"}


def _norm(v):
    if v is None:
        return None
    try:
        return Decimal(str(v))
    except Exception:
        return str(v).strip().lower()


def _field_match(pred, exp, path=""):
    """Return list of (field_path, ok)."""
    out = []
    if isinstance(exp, dict) and isinstance(pred, dict):
        for k, v in exp.items():
            if k == "must_have_review":
                continue
            out.extend(_field_match(pred.get(k), v, f"{path}.{k}" if path else k))
        return out
    if isinstance(exp, list) and isinstance(pred, list):
        for i, (p, e) in enumerate(zip(pred, exp)):
            out.extend(_field_match(p, e, f"{path}[{i}]"))
        if len(pred) != len(exp):
            out.append((f"{path}._len", False))
        return out
    if path.split(".")[-1] in NUMERIC_FIELDS or isinstance(exp, (int, float)):
        return [(path, _norm(pred) == _norm(exp))]
    return [(path, _norm(pred) == _norm(exp))]


def run(expected_dir: str = "expected", samples_dir: str = "samples") -> int:
    exp_dir = Path(expected_dir)
    smp_dir = Path(samples_dir)
    rows = []
    for exp_file in sorted(exp_dir.glob("*.expected.json")):
        stem = exp_file.name.replace(".expected.json", "")
        sample = smp_dir / f"{stem.replace('_original', '')}.pdf"
        if stem == "invoice_original":
            sample = smp_dir / "invoice.pdf"
        if not sample.exists():
            rows.append((stem, "SKIP", f"missing {sample}"))
            continue
        expected = json.loads(exp_file.read_text())
        try:
            pred = extract_invoice(sample)
        except Exception as e:
            rows.append((stem, "ERROR", str(e)))
            continue
        checks = _field_match(pred, expected)
        matched = sum(1 for _, ok in checks if ok)
        total = len(checks)
        field_acc = matched / total if total else 0.0
        missing = sum(1 for p, v in expected.items() if v is None and pred.get(p) is None)
        exp_missing = sum(1 for p, v in expected.items() if v is None)
        review_ok = pred.get("needs_review") == expected.get("must_have_review", False)
        rows.append((stem, f"{field_acc:.3f}", f"review_ok={review_ok}"))

    print("| sample | field_acc | review |")
    print("|---|---|---|")
    for r in rows:
        print("| " + " | ".join(map(str, r)) + " |")
    return 0


if __name__ == "__main__":
    sys.exit(run())