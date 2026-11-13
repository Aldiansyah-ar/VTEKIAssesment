import hashlib
import pandas as pd


def pseudonymize(value: str, salt: str = "v-teki-demo-salt") -> str:
    return hashlib.sha256((salt + str(value)).encode()).hexdigest()[:16]


def mask_pii(df: pd.DataFrame, keep: list[str]) -> pd.DataFrame:
    """Drop / hash all PII columns except the ones in `keep`."""
    out = df.copy()
    for col in ["FirstName", "LastName", "DateOfBirth"]:
        if col in out.columns:
            out.drop(columns=col, inplace=True)
    for col in ["CustomerID"]:
        if col in out.columns:
            out[col] = out[col].map(pseudonymize)
    return out


def safe_log(record: dict) -> dict:
    """Redact PII before writing to logs."""
    forbidden = {"FirstName", "LastName", "DateOfBirth",
                 "CustomerID", "AccountID", "AddressID"}
    return {k: ("<redacted>" if k in forbidden else v) for k, v in record.items()}