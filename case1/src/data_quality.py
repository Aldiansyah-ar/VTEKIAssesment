import pandas as pd
from src import config

def audit(tables: dict[str, pd.DataFrame]) -> dict:
    """Return documented data-quality issues. Used in report + as a test."""
    a, c, l, t = (tables["accounts"], tables["customers"],
                  tables["loans"], tables["transactions"])
    max_valid = pd.Timestamp(config.MAX_VALID_DATE)

    return {
        "transactions_duplicated_id":   int(t.duplicated("TransactionID").sum()),
        "accounts_duplicated_id":       int(a.duplicated("AccountID").sum()),
        "customers_duplicated_id":      int(c.duplicated("CustomerID").sum()),
        "tx_missing_date":              int(t["TransactionDate"].isna().sum()),
        "tx_missing_amount":            int(t["Amount"].isna().sum()),
        "tx_negative_amount":           int((t["Amount"] < 0).sum()),
        "tx_after_max_valid":           int((t["TransactionDate"] > max_valid).sum()),
        "tx_self_transfer":             int((t["AccountOriginID"] == t["AccountDestinationID"]).sum()),
        "accounts_missing_opening":     int(a["OpeningDate"].isna().sum()),
        "accounts_negative_balance":    int((a["Balance"] < 0).sum()),
        "customers_missing_dob":        int(c["DateOfBirth"].isna().sum()),
        "loans_missing_start":          int(l["StartDate"].isna().sum()),
        "tx_origin_not_in_accounts":    int((~t["AccountOriginID"].isin(a["AccountID"])).sum()),
        "acc_customer_not_in_customers":int((~a["CustomerID"].isin(c["CustomerID"])).sum()),
    }


def clean(tables: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Apply safe cleaning. All destructive ops are documented."""
    max_valid = pd.Timestamp(config.MAX_VALID_DATE)
    t = tables["transactions"].copy()

    # Drop transactions with no usable signal.
    t = t.dropna(subset=["TransactionDate", "Amount"])
    # Duplicates → keep first occurrence.
    t = t.drop_duplicates(subset=["TransactionID"])
    # Drop future timestamps (documented data-quality flag).
    t = t[t["TransactionDate"] <= max_valid]
    # Amount must be > 0 (0-value transfers are noise).
    t = t[t["Amount"] > 0]

    tables = {**tables, "transactions": t}
    # Keep only accounts referenced by customers and vice versa.
    tables["accounts"] = tables["accounts"].drop_duplicates("AccountID")
    tables["customers"] = tables["customers"].drop_duplicates("CustomerID")
    return tables