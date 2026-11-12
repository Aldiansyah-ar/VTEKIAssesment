"""
Usage:
    python -m src.predict --input outputs/scored_input.json --output outputs/predictions.csv
Input JSON (list of account-level records):
    [{"AccountID": ..., "n_out_tx": ..., ..., "tx_per_day": ...}, ...]
"""
import argparse, json
import numpy as np
import pandas as pd
import joblib
import shap
from src import config, privacy


def reason_codes(row: pd.Series, model, feature_cols, top_n=3):
    """SHAP-based reason codes for a single row."""
    explainer = shap.TreeExplainer(model)
    sv = explainer.shap_values(pd.DataFrame([row[feature_cols].values],
                                            columns=feature_cols))
    sv = sv[1] if isinstance(sv, list) else sv
    contrib = pd.Series(sv[0], index=feature_cols).sort_values(key=abs, ascending=False)
    out = []
    for name, val in contrib.head(top_n).items():
        out.append({"feature": name,
                    "direction": "increases_risk" if val > 0 else "decreases_risk",
                    "shap_value": float(round(val, 4)),
                    "value": float(row[name]) if pd.notna(row[name]) else None})
    return out


def predict_batch(rows: list[dict]) -> pd.DataFrame:
    bundle = joblib.load(config.MODEL_DIR / "fraud_model.joblib")
    model = bundle["lgbm"]
    cols  = bundle["feature_cols"]

    df = pd.DataFrame(rows)
    # PII masking BEFORE scoring (privacy by design).
    df = privacy.mask_pii(df, keep=["AccountID"])
    X = df[cols].apply(pd.to_numeric, errors="coerce")

    scores = model.predict_proba(X)[:, 1]
    df["risk_score"] = scores
    df["risk_rank"]  = np.argsort(-scores) + 1
    df["model_version"] = config.MODEL_VERSION
    df["reason_codes"] = [json.dumps(reason_codes(df.iloc[i], model, cols))
                          for i in range(len(df))]
    df["human_review_required"] = (scores >= 0.5).astype(int)
    df["review_status"] = df["human_review_required"].map(
        {1: "PENDING_ANALYST_REVIEW", 0: "NO_ACTION"})
    return df.sort_values("risk_score", ascending=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", default=str(config.OUTPUT_DIR / "predictions.csv"))
    args = ap.parse_args()

    with open(args.input) as f:
        rows = json.load(f)
    out = predict_batch(rows)
    out.to_csv(args.output, index=False)
    print(f"Scored {len(out)} accounts → {args.output}")
    print(out[["AccountID", "risk_score", "risk_rank",
               "human_review_required", "review_status"]].head(10))


if __name__ == "__main__":
    main()