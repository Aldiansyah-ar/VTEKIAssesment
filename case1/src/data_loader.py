import pandas as pd
from src import config

DATE_COLS = {
    "accounts":     ["OpeningDate"],
    "customers":    ["DateOfBirth"],
    "loans":        ["StartDate", "EstimatedEndDate"],
    "transactions": ["TransactionDate"],
}

def load_all() -> dict[str, pd.DataFrame]:
    dfs = {
        "accounts":     pd.read_csv(config.ACCOUNTS_CSV),
        "customers":    pd.read_csv(config.CUSTOMERS_CSV),
        "loans":        pd.read_csv(config.LOANS_CSV),
        "transactions": pd.read_csv(config.TRANSACTIONS_CSV),
    }
    for name, cols in DATE_COLS.items():
        for c in cols:
            dfs[name][c] = pd.to_datetime(dfs[name][c], errors="coerce")
    return dfs