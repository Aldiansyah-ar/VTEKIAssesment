import json, sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from rag_engine import load_corpus, build_retriever, answer

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
QF   = ROOT / "eval" / "questions.jsonl"
OUT  = ROOT / "outputs"


def is_refusal(txt: str) -> bool:
    t = txt.lower()
    return "don't have enough information" in t or "can't process" in t


def _save_json(output_dir: Path, name: str, payload: dict,
               add_timestamp: bool = False) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    safe = Path(name).name
    if safe.endswith(".json"):
        safe = safe[:-5]
    if add_timestamp:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        safe = f"{safe}_{ts}"
    fp = output_dir / f"{safe}.json"
    fp.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return fp


def run(output_dir: Path = OUT, output_name: str = "eval",
        add_timestamp: bool = False) -> Path:
    retriever = build_retriever(load_corpus(DATA))
    rows = [json.loads(l) for l in QF.read_text().splitlines() if l.strip()]

    recall_hit = recall_tot = 0
    cite_ok    = cite_tot   = 0
    refuse_ok  = refuse_tot = 0
    per_question = []

    for r in rows:
        out = answer(r["question"], r["role"], retriever)
        ret_ids = [i for i, _ in out.get("retrieved", [])]

        rec = {
            "id": r["id"],
            "type": r["type"],
            "role": r["role"],
            "question": r["question"],
            "expected_sources": r["expected_sources"],
            "expected_answer": r.get("expected_answer"),
            "answer": out["answer"],
            "citations": out["citations"],
            "retrieved": ret_ids,
            "blocked": out["blocked"],
            "reason": out.get("reason"),
            "hits": {},
        }

        if r["type"] in ("answerable", "answerable_staff"):
            if r["expected_sources"]:
                recall_tot += 1
                hit = any(s in ret_ids for s in r["expected_sources"])
                if hit:
                    recall_hit += 1
                rec["hits"]["recall_at_4"] = hit
            cite_tot += 1
            cit = any(s in out["citations"] for s in r["expected_sources"])
            if cit:
                cite_ok += 1
            rec["hits"]["citation"] = cit
        else:
            refuse_tot += 1
            ref = is_refusal(out["answer"])
            if ref:
                refuse_ok += 1
            rec["hits"]["refusal"] = ref

        per_question.append(rec)

        print(f"[{r['id']}] {r['type']:18s} role={r['role']}")
        print(f"  Q : {r['question']}")
        print(f"  A : {out['answer']}")
        print(f"  cite={out['citations']}  retrieved={ret_ids}")
        print()

    summary = {
        "timestamp": datetime.now().isoformat(),
        "metrics": {
            "recall_at_4": {
                "hits": recall_hit, "total": recall_tot,
                "value": round(recall_hit / recall_tot, 4) if recall_tot else None,
            },
            "citation_accuracy": {
                "hits": cite_ok, "total": cite_tot,
                "value": round(cite_ok / cite_tot, 4) if cite_tot else None,
            },
            "refusal_accuracy": {
                "hits": refuse_ok, "total": refuse_tot,
                "value": round(refuse_ok / refuse_tot, 4) if refuse_tot else None,
            },
        },
        "per_question": per_question,
    }

    fp = _save_json(output_dir, output_name, summary,
                    add_timestamp=add_timestamp)

    print("=" * 60)
    print(f"Retrieval Recall@4 : {recall_hit}/{recall_tot}")
    print(f"Citation accuracy  : {cite_ok}/{cite_tot}")
    print(f"Refusal accuracy   : {refuse_ok}/{refuse_tot}")
    print(f"[saved] {fp}")
    return fp


def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--output-dir", default=str(OUT),
                   help="direktori output (default: outputs/)")
    p.add_argument("--output-name", default="eval",
                   help="nama file output tanpa .json (default: eval)")
    p.add_argument("--output-timestamp", action="store_true",
                   help="tambahkan timestamp ke nama file agar tidak overwrite")
    args = p.parse_args()

    run(output_dir=Path(args.output_dir),
        output_name=args.output_name,
        add_timestamp=args.output_timestamp)


if __name__ == "__main__":
    main()