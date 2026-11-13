from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from .pipeline import extract_invoice, UnsupportedFileError, FileTooLargeError
from .masking import mask_invoice_for_viewer


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Invoice extraction (Case 2)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    ex = sub.add_parser("extract", help="Extract a single invoice PDF")
    ex.add_argument("path")
    ex.add_argument("--output", default=None, help="Write JSON to this file")
    ex.add_argument("--viewer", action="store_true", help="Mask PII (viewer role)")

    ev = sub.add_parser("evaluate", help="Run evaluation against expected/*.json")
    ev.add_argument("--expected-dir", default="expected")
    ev.add_argument("--samples-dir", default="samples")
    ev.add_argument("--output", default=None,
                help="Write results to this file (e.g. output/evaluation.json)")

    args = ap.parse_args(argv)

    if args.cmd == "extract":
        try:
            out = extract_invoice(args.path)
        except (UnsupportedFileError, FileTooLargeError) as e:
            print(json.dumps({"error": str(e), "code": getattr(e, "code", "error")}))
            return 2
        if args.viewer:
            out = mask_invoice_for_viewer(out)
        s = json.dumps(out, indent=2, ensure_ascii=False)
        if args.out:
            out_path = Path(args.out)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(s, encoding="utf-8")
            print(f"wrote {out_path}")
        else:
            print(s)
        return 0 if not out.get("needs_review") else 1

    if args.cmd == "evaluate":
        from .evaluate import run
        return run(args.expected_dir, args.samples_dir, args.out, args.format)
    return 0


if __name__ == "__main__":
    sys.exit(main())