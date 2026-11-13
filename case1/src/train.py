import json, joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from lightgbm import LGBMClassifier
from src import config, data_loader, data_quality, features, labels


def split_train_test(feats: pd.DataFrame, y: pd.Series, test_size: float = 0.25):
    """
    Stratified random holdout on accounts.

    WHY NOT TEMPORAL SPLIT
    ----------------------
    `features.build_features()` already enforces point-in-time
    correctness: every feature is computed from transactions strictly
    before CUTOFF_DATE. The label is the account snapshot.

    A strict temporal *split* would need accounts that did not exist
    at CUTOFF_DATE, which a single-snapshot account table cannot
    provide. Using `first_tx < CUTOFF_DATE` as the split rule is
    tautological after PIT filtering (always True), which is why the
    earlier version produced an empty test set.

    Point-in-time leak prevention is tested in
    tests/test_leakage.py::test_no_future_transactions_in_features.
    """
    X = feats[features.FEATURE_COLS].copy()
    return train_test_split(
        X, y, test_size=test_size, stratify=y,
        random_state=config.RANDOM_STATE,
    )


def main():
    tables = data_loader.load_all()
    quality = data_quality.audit(tables)
    print("Data quality issues:", json.dumps(quality, indent=2))
    tables = data_quality.clean(tables)

    feats = features.build_features(tables)
    y = labels.build_proxy_label(feats)

    print(f"Accounts: {len(feats)}  positives: {int(y.sum())} "
          f"({y.mean():.1%})")

    X_tr, X_te, y_tr, y_te = split_train_test(feats, y)
    print(f"Train: {X_tr.shape} positives={int(y_tr.sum())}")
    print(f"Test : {X_te.shape} positives={int(y_te.sum())}")

    if y_te.sum() == 0:
        raise RuntimeError(
            "Test set contains no positives. Increase positive_rate in "
            "labels.build_proxy_label or lower test_size."
        )

    baseline = Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("scale",  StandardScaler()),
        ("clf",    LogisticRegression(class_weight="balanced",
                                      max_iter=2000,
                                      random_state=config.RANDOM_STATE)),
    ])
    baseline.fit(X_tr, y_tr)

    pos = max(int(y_tr.sum()), 1)
    neg = int((y_tr == 0).sum())
    lgbm = LGBMClassifier(
        n_estimators=300,
        learning_rate=0.05,
        num_leaves=15,                 
        min_child_samples=10,
        scale_pos_weight=neg / pos,
        random_state=config.RANDOM_STATE,
        n_jobs=1,                      
        verbose=-1,
    )
    lgbm.fit(X_tr, y_tr)

    cv = StratifiedKFold(n_splits=5, shuffle=True,
                         random_state=config.RANDOM_STATE)
    cv_scores = {
        "baseline_cv_pr_auc": cross_val_score(
            baseline, X_tr, y_tr, cv=cv,
            scoring="average_precision", n_jobs=1).mean(),
        "lgbm_cv_pr_auc":     cross_val_score(
            lgbm, X_tr, y_tr, cv=cv,
            scoring="average_precision", n_jobs=1).mean(),
    }
    print("CV PR-AUC:", json.dumps(cv_scores, indent=2))

    joblib.dump(
        {"baseline": baseline, "lgbm": lgbm,
         "feature_cols": features.FEATURE_COLS,
         "model_version": config.MODEL_VERSION,
         "cv_scores": cv_scores},
        config.MODEL_DIR / "fraud_model.joblib",
    )
    print("Model saved", config.MODEL_DIR / "fraud_model.joblib")


if __name__ == "__main__":
    main()