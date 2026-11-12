import argparse, json
from pathlib import Path
from rag_engine import load_corpus, build_retriever, answer

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--data-dir", default="data")
    p.add_argument("--role", default="passenger", choices=["passenger", "staff"])
    p.add_argument("--query", help="single-shot query")
    args = p.parse_args()

    chunks = load_corpus(Path(args.data_dir))
    retriever = build_retriever(chunks)
    print(f"[info] loaded {len(chunks)} chunks")

    if args.query:
        print(json.dumps(answer(args.query, args.role, retriever), indent=2))
        return

    print(f"SkyWings assistant (role={args.role}). Type 'exit' to quit.")
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

if __name__ == "__main__":
    main()