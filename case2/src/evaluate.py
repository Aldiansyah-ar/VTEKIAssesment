from __future__ import annotations
import json
import sys
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from .pipeline import extract_invoice

NUMERIC_FIELDS = {"subtotal", "tax_total", "grand_total"}


def _norm(v):
    if v is None:
        return None
    try:
        return Decimal(str(v))
    except Exception:
        return str(v).strip().lower()


def _field_match(pred, exp, path=""):
    """Return list of dicts: {field, expected, predicted, match}."""
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
            out.append({
                "field": f"{path}._len",
                "expected": len(exp),
                "predicted": len(pred),
                "match": False,
            })
        return out
    if path.split(".")[-1] in NUMERIC_FIELDS or isinstance(exp, (int, float)):
        ok = _norm(pred) == _norm(exp)
    else:
        ok = _norm(pred) == _norm(exp)
    return [{
        "field": path,
        "expected": None if exp is None else str(exp),
        "predicted": None if pred is None else str(pred),
        "match": ok,
    }]


def run(expected_dir="expected", samples_dir="samples",
        out_path: str | None = None, fmt: str = "table") -> int:
    """fmt: 'table' | 'json' | 'both'. out_path: file tujuan (auto-create folder)."""
    exp_dir = Path(expected_dir)
    smp_dir = Path(samples_dir)

    reports = []
    t_start = datetime.now(timezone.utc)

    for exp_file in sorted(exp_dir.glob("*.expected.json")):
        stem = exp_file.name.replace(".expected.json", "")
        sample = smp_dir / f"{stem.replace('_original', '')}.pdf"
        if stem == "invoice_original":
            sample = smp_dir / "invoice.pdf"

        report = {"sample": stem, "sample_path": str(sample)}

        if not sample.exists():
            report.update({"status": "skip", "reason": f"missing {sample}"})
            reports.append(report)
            continue

        expected = json.loads(exp_file.read_text())
        try:
            pred = extract_invoice(sample)
        except Exception as e:
            report.update({"status": "error", "error": str(e)})
            reports.append(report)
            continue

        checks = _field_match(pred, expected)
        matched = sum(1 for c in checks if c["match"])
        total = len(checks)
        field_acc = matched / total if total else 0.0

        expected_none = [k for k, v in expected.items() if v is None]
        missing_ok = sum(1 for k in expected_none if pred.get(k) is None)
        missing_field_rate = (
            (len(expected_none) - missing_ok) / len(expected_none)
            if expected_none else 0.0
        )

        review_expected = bool(expected.get("must_have_review", False))
        review_pred = bool(pred.get("needs_review", False))

        report.update({
            "status": "ok",
            "field_accuracy": round(field_acc, 4),
            "fields_matched": matched,
            "fields_total": total,
            "missing_field_rate": round(missing_field_rate, 4),
            "review_expected": review_expected,
            "review_predicted": review_pred,
            "review_ok": review_expected == review_pred,
            "overall_confidence": pred.get("overall_confidence"),
            "latency_ms": (pred.get("_meta") or {}).get("latency_ms"),
            "extraction_method": pred.get("extraction_method"),
            "failures": [c for c in checks if not c["match"]],
            "per_field": checks,
        })
        reports.append(report)

    ok = [r for r in reports if r["status"] == "ok"]
    summary = {
        "samples_total": len(reports),
        "samples_ok": len(ok),
        "samples_skipped": sum(1 for r in reports if r["status"] == "skip"),
        "samples_error": sum(1 for r in reports if r["status"] == "error"),
        "mean_field_accuracy": round(
            sum(r["field_accuracy"] for r in ok) / len(ok), 4
        ) if ok else 0.0,
        "review_routing_accuracy": round(
            sum(1 for r in ok if r["review_ok"]) / len(ok), 4
        ) if ok else 0.0,
        "mean_latency_ms": round(
            sum(r["latency_ms"] or 0 for r in ok) / len(ok), 2
        ) if ok else 0.0,
    }

    payload = {
        "tool": "invoice-extractor/1.0.0",
        "generated_at": t_start.isoformat(),
        "expected_dir": str(exp_dir),
        "samples_dir": str(smp_dir),
        "summary": summary,
        "samples": reports,
    }

    table_lines = [
        "| sample | field_acc | missing_rate | review_ok | failures |",
        "|---|---|---|---|---|",
    ]
    for r in reports:
        if r["status"] != "ok":
            table_lines.append(f"| {r['sample']} | {r['status']} | - | - | {r.get('reason', r.get('error', ''))} |")
        else:
            table_lines.append(
                f"| {r['sample']} | {r['field_accuracy']:.3f} | "
                f"{r['missing_field_rate']:.3f} | {r['review_ok']} | "
                f"{len(r['failures'])} |"
            )
    table = "\n".join(table_lines)

    if fmt in ("table", "both"):
        print(table)
        print()
        print("SUMMARY:", json.dumps(summary, indent=2))

    if out_path:
        p = Path(out_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        if fmt in ("json", "both") or out_path.endswith(".json"):
            p.write_text(json.dumps(payload, indent=2, ensure_ascii=False),
                         encoding="utf-8")
            print(f"wrote {p}  ({p.stat().st_size} bytes)")
        else:
            p.write_text(table + "\n", encoding="utf-8")
            print(f"wrote {p}")

    return 0 if summary["samples_error"] == 0 else 1


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--expected-dir", default="expected")
    ap.add_argument("--samples-dir", default="samples")
    ap.add_argument("--output", default=None)
    args = ap.parse_args()
    sys.exit(run(args.expected_dir, args.samples_dir, args.out))