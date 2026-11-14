from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

from .pipeline import extract_invoice, UnsupportedFileError, FileTooLargeError
from .masking import mask_invoice_for_viewer


DEFAULT_EXTRACT_OUT = "outputs/invoice.json"


def _print_summary(out: dict, out_path: Path) -> None:
    """One line summary so the terminal isn't full of JSON."""
    items = out.get("line_items") or []
    print(
        f"wrote {out_path}  "
        f"| invoice={out.get('invoice_number')} "
        f"| items={len(items)} "
        f"| grand_total={out.get('grand_total')} "
        f"| needs_review={out.get('needs_review')} "
        f"| conf={out.get('overall_confidence')}"
    )
    if out.get("review_reasons"):
        print(f"  review_reasons: {', '.join(out['review_reasons'])}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Invoice extraction (Case 2)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    ex = sub.add_parser("extract", help="Extract a single invoice PDF")
    ex.add_argument("path")
    ex.add_argument("--out", default=DEFAULT_EXTRACT_OUT,
                    help=f"Output JSON path (default: {DEFAULT_EXTRACT_OUT})")
    ex.add_argument("--stdout", action="store_true",
                    help="Print full JSON to stdout, not writing file")
    ex.add_argument("--viewer", action="store_true",
                    help="Mask PII (viewer role)")

    ev = sub.add_parser("evaluate", help="Run evaluation against expected/*.json")
    ev.add_argument("--expected-dir", default="expected")
    ev.add_argument("--samples-dir", default="samples")
    ev.add_argument("--out", default=None,
                    help="Override output path (default: output/evaluate.json)")
    ev.add_argument("--no-save", action="store_true",
                    help="Don't write files, just print tables.")
    ev.add_argument("--format", choices=["table", "json", "both", "none"],
                    default="json")

    args = ap.parse_args(argv)

    if args.cmd == "extract":
        try:
            out = extract_invoice(args.path)
        except (UnsupportedFileError, FileTooLargeError) as e:
            print(json.dumps({"error": str(e),
                              "code": getattr(e, "code", "error")}))
            return 2

        if args.viewer:
            out = mask_invoice_for_viewer(out)

        if args.stdout:
            print(json.dumps(out, indent=2, ensure_ascii=False))
            return 0 if not out.get("needs_review") else 1

        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            json.dumps(out, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        _print_summary(out, out_path)
        return 0 if not out.get("needs_review") else 1

    if args.cmd == "evaluate":
        from .evaluate import run, DEFAULT_OUT
        out = None if args.no_save else (args.out or DEFAULT_OUT)
        return run(args.expected_dir, args.samples_dir, out, args.format)

    return 0


if __name__ == "__main__":
    sys.exit(main())