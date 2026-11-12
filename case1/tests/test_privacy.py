import io, logging, pandas as pd
from src import privacy

def test_pii_is_dropped_from_scoring_input():
    df = pd.DataFrame([{
        "AccountID": 200094, "CustomerID": 10123,
        "FirstName": "Nyla", "LastName": "Aguirre",
        "DateOfBirth": "1974-02-07", "n_out_tx": 5,
    }])
    masked = privacy.mask_pii(df, keep=["AccountID"])
    for col in ["FirstName", "LastName", "DateOfBirth"]:
        assert col not in masked.columns
    assert masked["CustomerID"].iloc[0] != 10123  # pseudonymized

def test_pii_not_in_logs():
    record = {"AccountID": 1, "FirstName": "Nyla", "risk_score": 0.9}
    safe = privacy.safe_log(record)
    assert safe["FirstName"] == "<redacted>"
    assert safe["AccountID"] == "<redacted>"
    # A regression test: the log stream itself must not contain PII.
    stream = io.StringIO()
    h = logging.StreamHandler(stream)
    logging.getLogger("fraud").addHandler(h)
    logging.getLogger("fraud").setLevel(logging.INFO)
    logging.getLogger("fraud").info(str(safe))
    assert "Nyla" not in stream.getvalue()