import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import joblib
import shap
from src import config, privacy


def _json_safe(obj):
    """Recursively convert numpy / pandas / NaN values to JSON-safe types."""
    if isinstance(obj, dict):
        return {k: _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_json_safe(v) for v in obj]
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        v = float(obj)
        return None if (math.isnan(v) or math.isinf(v)) else v
    if isinstance(obj, np.bool_):
        return bool(obj)
    if isinstance(obj, float):
        return None if (math.isnan(obj) or math.isinf(obj)) else obj
    if obj is pd.NaT:
        return None
    try:
        if pd.isna(obj):
            return None
    except (TypeError, ValueError):
        pass
    return obj


def build_explainer(model):
    return shap.TreeExplainer(model)


def reason_codes(row, explainer, feature_cols, top_n=3):
    sv = explainer.shap_values(
        pd.DataFrame([row[feature_cols].values], columns=feature_cols)
    )
    sv = sv[1] if isinstance(sv, list) else sv
    contrib = pd.Series(sv[0], index=feature_cols).sort_values(key=abs, ascending=False)

    out = []
    for name, val in contrib.head(top_n).items():
        raw = row[name]
        try:
            raw_val = None if pd.isna(raw) else float(raw)
        except (TypeError, ValueError):
            raw_val = None
        out.append({
            "feature": name,
            "direction": "increases_risk" if val > 0 else "decreases_risk",
            "shap_value": round(float(val), 4),
            "value": raw_val,
        })
    return out


def predict_batch(rows):
    bundle = joblib.load(config.MODEL_DIR / "fraud_model.joblib")
    model  = bundle["lgbm"]
    cols   = bundle["feature_cols"]
    explainer = build_explainer(model)

    df = pd.DataFrame(rows)
    df = privacy.mask_pii(df, keep=["AccountID"])
    X  = df[cols].apply(pd.to_numeric, errors="coerce")

    scores = model.predict_proba(X)[:, 1]
    df["risk_score"]       = scores
    df["risk_rank"]        = np.argsort(-scores) + 1
    df["model_version"]    = config.MODEL_VERSION
    df["reason_codes"]     = [
        reason_codes(df.iloc[i], explainer, cols) for i in range(len(df))
    ]
    df["human_review_required"] = (scores >= 0.5).astype(int)
    df["review_status"] = df["human_review_required"].map(
        {1: "PENDING_ANALYST_REVIEW", 0: "NO_ACTION"}
    )
    return df.sort_values("risk_score", ascending=False).reset_index(drop=True)


def build_output_payload(df):
    records = df.to_dict(orient="records")
    return {
        "model_version": config.MODEL_VERSION,
        "generated_at":  datetime.now(timezone.utc).isoformat(),
        "n_scored":      len(records),
        "summary": {
            "n_high_risk":      int(df["human_review_required"].sum()),
            "n_pending_review": int((df["review_status"] == "PENDING_ANALYST_REVIEW").sum()),
            "max_risk_score":   float(df["risk_score"].max()) if len(df) else None,
            "min_risk_score":   float(df["risk_score"].min()) if len(df) else None,
        },
        "predictions": records,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True,
                    help="Path to input JSON (list of account records)")
    ap.add_argument("--output", default=str(config.OUTPUT_DIR / "predictions.json"),
                    help="Path to output JSON")
    args = ap.parse_args()

    with open(args.input, encoding="utf-8") as f:
        rows = json.load(f)

    df      = predict_batch(rows)
    payload = _json_safe(build_output_payload(df))

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    print(f"Scored {payload['n_scored']} accounts → {out_path}")
    print(f"High risk (≥0.5): {payload['summary']['n_high_risk']}")
    print("Top 3 predictions:")
    print(json.dumps(payload["predictions"][:3], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()