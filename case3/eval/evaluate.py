import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from rag_engine import load_corpus, build_retriever, answer

DATA = Path(__file__).resolve().parent.parent / "data"
QF   = Path(__file__).resolve().parent / "questions.jsonl"

def is_refusal(txt: str) -> bool:
    t = txt.lower()
    return "don't have enough information" in t or "can't process" in t

def main():
    retriever = build_retriever(load_corpus(DATA))
    rows = [json.loads(l) for l in QF.read_text().splitlines() if l.strip()]

    recall_hit = recall_tot = 0
    cite_ok    = cite_tot   = 0
    refuse_ok  = refuse_tot = 0

    for r in rows:
        out = answer(r["question"], r["role"], retriever)
        ret_ids = [i for i, _ in out.get("retrieved", [])]

        if r["type"] in ("answerable", "answerable_staff"):
            if r["expected_sources"]:
                recall_tot += 1
                if any(s in ret_ids for s in r["expected_sources"]):
                    recall_hit += 1
            cite_tot += 1
            if any(s in out["citations"] for s in r["expected_sources"]):
                cite_ok += 1
        else:  # unanswerable / access_restricted
            refuse_tot += 1
            if is_refusal(out["answer"]):
                refuse_ok += 1

        print(f"[{r['id']}] {r['type']:18s} role={r['role']}")
        print(f"  Q : {r['question']}")
        print(f"  A : {out['answer']}")
        print(f"  cite={out['citations']}  retrieved={ret_ids}")
        print()

    print("=" * 60)
    print(f"Retrieval Recall@4 : {recall_hit}/{recall_tot}")
    print(f"Citation accuracy  : {cite_ok}/{cite_tot}")
    print(f"Refusal accuracy   : {refuse_ok}/{refuse_tot}")

if __name__ == "__main__":
    main()