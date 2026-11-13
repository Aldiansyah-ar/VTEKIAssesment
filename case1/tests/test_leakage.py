import pandas as pd
from src import config, data_loader, data_quality, features, labels


def test_no_future_transactions_in_features():
    """Post-cutoff transactions must not influence feature values."""
    tables = data_quality.clean(data_loader.load_all())
    cutoff = pd.Timestamp(config.CUTOFF_DATE)
    tx = tables["transactions"]
    after = tx[tx["TransactionDate"] >= cutoff]
    if len(after) == 0:
        return

    feats_full = features.build_features(tables)
    feats_pit  = features.build_features({**tables,
        "transactions": tx[tx["TransactionDate"] < cutoff]})

    merged = feats_full.merge(feats_pit, on="AccountID",
                              suffixes=("_full", "_pit"))
    affected   = set(after["AccountOriginID"])
    unaffected = merged[~merged["AccountID"].isin(affected)]

    for c in features.FEATURE_COLS:
        a = unaffected[f"{c}_full"].fillna(0).values
        b = unaffected[f"{c}_pit"].fillna(0).values
        assert (a == b).all(), f"leak in feature {c}"


def test_split_is_disjoint():
    """Rows in train and test must not overlap (each row = one account)."""
    from src.train import split_train_test
    tables = data_quality.clean(data_loader.load_all())
    feats = features.build_features(tables)
    y = labels.build_proxy_label(feats)
    Xtr, Xte, _, _ = split_train_test(feats, y)
    assert set(Xtr.index).isdisjoint(set(Xte.index))


def test_split_has_positives_on_both_sides():
    """Stratified split must not produce a degenerate test set."""
    from src.train import split_train_test
    tables = data_quality.clean(data_loader.load_all())
    feats = features.build_features(tables)
    y = labels.build_proxy_label(feats)
    _, _, y_tr, y_te = split_train_test(feats, y)
    assert y_tr.sum() > 0
    assert y_te.sum() > 0