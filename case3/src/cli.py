import argparse, json
from datetime import datetime
from pathlib import Path
from rag_engine import load_corpus, build_retriever, answer


def _ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def _save_json(output_dir: Path, name: str, payload: dict,
               add_timestamp: bool = False) -> Path:
    """
    Simpan payload ke <output_dir>/<name>.json.

    - Jika add_timestamp=True, sisipkan timestamp sebelum .json
      → <name>_<YYYYmmdd_HHMMSS_micro>.json
    - Jika name sudah berakhiran .json, ekstensi tidak digandakan.
    """
    _ensure_dir(output_dir)

    safe = Path(name).name
    if safe.endswith(".json"):
        safe = safe[:-5]

    if add_timestamp:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        safe = f"{safe}_{ts}"

    out_file = output_dir / f"{safe}.json"
    out_file.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return out_file


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--data-dir", default="data")
    p.add_argument("--role", default="passenger", choices=["passenger", "staff"])
    p.add_argument("--query", help="single-shot query")
    p.add_argument("--output-dir", default="outputs",
                   help="direktori output (default: outputs/)")
    p.add_argument("--output-name", default=None,
                   help="nama file output tanpa .json "
                        "(default: query_<ts> atau session_<ts>)")
    p.add_argument("--output-timestamp", action="store_true",
                   help="tambahkan timestamp ke nama file agar tidak overwrite")
    p.add_argument("--no-save", action="store_true",
                   help="nonaktifkan penyimpanan output ke disk")
    args = p.parse_args()

    chunks = load_corpus(Path(args.data_dir))
    retriever = build_retriever(chunks)
    print(f"[info] loaded {len(chunks)} chunks")

    if args.query:
        result = answer(args.query, args.role, retriever)
        print(json.dumps(result, indent=2))

        if not args.no_save:
            name = args.output_name or "query"
            payload = {
                "timestamp": datetime.now().isoformat(),
                "mode": "single_query",
                "role": args.role,
                "query": args.query,
                "result": result,
            }
            fp = _save_json(Path(args.output_dir), name, payload,
                            add_timestamp=args.output_timestamp)
            print(f"[saved] {fp}")
        return

    print(f"SkyWings assistant (role={args.role}). Type 'exit' to quit.")
    session = {
        "timestamp": datetime.now().isoformat(),
        "mode": "interactive_session",
        "role": args.role,
        "turns": [],
    }

    while True:
        try:
            q = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if q.lower() in ("exit", "quit"):
            break
        if not q:
            continue

        out = answer(q, args.role, retriever)
        print(f"\nAnswer: {out['answer']}")
        if out.get("citations"):
            print(f"Citations: {out['citations']}")
        if out.get("blocked"):
            print(f"[blocked: {out.get('reason')}]")
        print()

        session["turns"].append({
            "timestamp": datetime.now().isoformat(),
            "query": q,
            "result": out,
        })

    if session["turns"] and not args.no_save:
        name = args.output_name or "session"
        fp = _save_json(Path(args.output_dir), name, session,
                        add_timestamp=args.output_timestamp)
        print(f"[saved] {fp}")


if __name__ == "__main__":
    main()