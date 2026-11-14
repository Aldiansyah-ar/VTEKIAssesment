import json
import numpy as np
import pandas as pd
import joblib
from sklearn.metrics import (precision_score, recall_score, f1_score,
                             confusion_matrix, average_precision_score,
                             roc_auc_score)
from src import config, data_loader, data_quality, features, labels
from src.train import split_train_test


def precision_at_k(y_true, scores, k):
    order = np.argsort(-scores)[:k]
    return float(np.mean(np.array(y_true)[order]))


def main():
    bundle = joblib.load(config.MODEL_DIR / "fraud_model.joblib")
    tables = data_quality.clean(data_loader.load_all())
    feats = features.build_features(tables)
    y = labels.build_proxy_label(feats)

    X_tr, X_te, y_tr, y_te = split_train_test(feats, y)
    results = {}
    for name in ["baseline", "lgbm"]:
        model = bundle[name]
        scores = model.predict_proba(X_te)[:, 1]
        preds  = (scores >= 0.5).astype(int)

        results[name] = {
            "precision":       float(precision_score(y_te, preds, zero_division=0)),
            "recall":          float(recall_score(y_te, preds, zero_division=0)),
            "f1":              float(f1_score(y_te, preds, zero_division=0)),
            "pr_auc":          float(average_precision_score(y_te, scores)),
            "roc_auc":         float(roc_auc_score(y_te, scores)),
            "confusion_matrix":confusion_matrix(y_te, preds).tolist(),
            "precision@50":    precision_at_k(y_te, scores, k=50),
            "precision@100":   precision_at_k(y_te, scores, k=100),
            "n_test":          int(len(y_te)),
            "n_pos_test":      int(y_te.sum()),
        }

    with open(config.OUTPUT_DIR / "evaluate.json", "w") as f:
        json.dump(results, f, indent=2)
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()