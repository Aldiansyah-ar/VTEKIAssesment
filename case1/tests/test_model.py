import numpy as np
from src import config, data_loader, data_quality, features, labels
from src.train import split_train_test
import joblib

def test_model_outputs_probabilities():
    bundle = joblib.load(config.MODEL_DIR / "fraud_model.joblib")
    for name in ("baseline", "lgbm"):
        m = bundle[name]
        X = np.array([[1, 100, 50, 10, 80, 20, 3, 30, 1.5,
                       0.1, 0.05, 200, 40, 50000, 1, 1, 2,
                       0, 0, 0, 0, 0, 0.05, 0.0]])
        p = m.predict_proba(X)[:, 1]
        assert 0 <= p[0] <= 1

def test_reason_codes_are_human_readable():
    from src.predict import predict_batch
    rows = [{"AccountID": 200094, "n_out_tx": 50, "sum_out_amt": 200000,
             "mean_out_amt": 4000, "std_out_amt": 1000, "max_out_amt": 8000,
             "min_out_amt": 500, "n_unique_dest": 40, "active_days": 200,
             "tx_per_day": 5, "odd_hour_ratio": 0.5, "round_amount_ratio": 0.6,
             "account_age_days": 900, "age": 45, "Balance": 48000,
             "AccountTypeID": 3, "AccountStatusID": 2, "CustomerTypeID": 1,
             "n_loans": 2, "total_principal": 90000, "avg_interest": 0.1,
             "max_interest": 0.14, "has_suspended_loan": 1,
             "amt_to_balance_ratio": 0.08, "loan_to_balance_ratio": 1.9}]
    out = predict_batch(rows)
    assert out["human_review_required"].iloc[0] == 1
    assert "reason_codes" in out.columns