import numpy as np
import pandas as pd
from src import config


def build_features(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """
    Build one row per AccountID using ONLY transactions with
    TransactionDate < CUTOFF_DATE, then label with the current
    account snapshot. This guarantees no leakage of post-cutoff
    activity into training features.
    """
    t = tables["transactions"]
    a = tables["accounts"]
    c = tables["customers"]
    l = tables["loans"]
    cutoff = pd.Timestamp(config.CUTOFF_DATE)

    t = t[t["TransactionDate"] < cutoff].copy()

    # ── Originator-side aggregate features ──────────────────────────────
    grp = t.groupby("AccountOriginID")
    feats = pd.DataFrame({
        "n_out_tx":        grp.size(),
        "sum_out_amt":     grp["Amount"].sum(),
        "mean_out_amt":    grp["Amount"].mean(),
        "std_out_amt":     grp["Amount"].std().fillna(0.0),
        "max_out_amt":     grp["Amount"].max(),
        "min_out_amt":     grp["Amount"].min(),
        "n_unique_dest":   grp["AccountDestinationID"].nunique(),
        "first_tx":        grp["TransactionDate"].min(),
        "last_tx":         grp["TransactionDate"].max(),
    })

    feats["active_days"] = (feats["last_tx"] - feats["first_tx"]).dt.days.clip(lower=0)
    feats["tx_per_day"]  = feats["n_out_tx"] / feats["active_days"].clip(lower=1)

    # ── Behavioural ratios ──────────────────────────────────────────────
    t2 = t.assign(
        hour = t["TransactionDate"].dt.hour,
        is_odd = t["TransactionDate"].dt.hour.between(0, 5),
        is_round = (t["Amount"] % 100 == 0),
    )
    g2 = t2.groupby("AccountOriginID")
    feats["odd_hour_ratio"]     = g2["is_odd"].mean()
    feats["round_amount_ratio"] = g2["is_round"].mean()

    feats = feats.reset_index().rename(columns={"AccountOriginID": "AccountID"})

    # ── Join account + customer context ─────────────────────────────────
    feats = feats.merge(a, on="AccountID", how="left")
    feats = feats.merge(c, on="CustomerID", how="left")

    feats["account_age_days"] = (cutoff - feats["OpeningDate"]).dt.days.clip(lower=0)
    feats["age"] = ((cutoff - feats["DateOfBirth"]).dt.days / 365.25)
    feats["age"] = feats["age"].fillna(feats["age"].median())

    # ── Loan aggregates ────────────────────────────────────────────────
    loans_agg = l.groupby("AccountID").agg(
        n_loans            = ("LoanID", "count"),
        total_principal    = ("PrincipalAmount", "sum"),
        avg_interest       = ("InterestRate", "mean"),
        max_interest       = ("InterestRate", "max"),
        has_suspended_loan = ("LoanStatusID", lambda s: int((s == 2).any())),
    )
    feats = feats.merge(loans_agg, on="AccountID", how="left")
    for col in ["n_loans", "total_principal", "avg_interest",
                "max_interest", "has_suspended_loan"]:
        feats[col] = feats[col].fillna(0.0)

    # ── Ratio features ────────────────────────────────────────────────
    safe_bal = feats["Balance"].replace(0, np.nan)
    feats["amt_to_balance_ratio"] = (feats["mean_out_amt"] / safe_bal)\
                                        .replace([np.inf, -np.inf], np.nan).fillna(0)
    feats["loan_to_balance_ratio"] = (feats["total_principal"] / safe_bal)\
                                        .replace([np.inf, -np.inf], np.nan).fillna(0)
    return feats


FEATURE_COLS = [
    "n_out_tx", "sum_out_amt", "mean_out_amt", "std_out_amt",
    "max_out_amt", "min_out_amt", "n_unique_dest", "active_days",
    "tx_per_day", "odd_hour_ratio", "round_amount_ratio",
    "account_age_days", "age", "Balance", "AccountTypeID", "AccountStatusID",
    "CustomerTypeID", "n_loans", "total_principal", "avg_interest",
    "max_interest", "has_suspended_loan",
    "amt_to_balance_ratio", "loan_to_balance_ratio",
]