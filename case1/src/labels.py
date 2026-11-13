import pandas as pd


def build_proxy_label(feats: pd.DataFrame, positive_rate: float = 0.10) -> pd.Series:
    """
    PROXY LABEL — not ground truth fraud.

    Composite risk score from documented signals, then label the top
    `positive_rate` fraction of accounts as 'suspect'. This yields a
    realistic analyst workload (~10% flagged) and avoids the degenerate
    7-positive training set produced by a hard `>= 3 signals` threshold.

    LIMITATIONS (also in README):
    - Threshold is quantile-based on THIS population. A different
      population requires re-calibration.
    - This is a screening target, not confirmed fraud. True fraud
      performance cannot be established without reviewed outcomes.
    """
    signal_score = (
        2 * (feats["AccountStatusID"] == 2).astype(int)
      + 1 * (feats["odd_hour_ratio"] >= 0.30).astype(int)
      + 1 * (feats["amt_to_balance_ratio"] >= 0.50).astype(int)
      + 1 * (feats["tx_per_day"] >= feats["tx_per_day"].median() * 2).astype(int)
      + 2 * (feats["has_suspended_loan"] == 1).astype(int)
    )
    thresh = signal_score.quantile(1 - positive_rate)
    return (signal_score > thresh).astype(int)