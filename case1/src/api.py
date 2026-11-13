from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from src.predict import predict_batch

app = FastAPI(title="V-TEKI Fraud Risk API", version="1.0.0")


class Row(BaseModel):
    AccountID: int
    n_out_tx: float | None = None
    sum_out_amt: float | None = None
    mean_out_amt: float | None = None
    std_out_amt: float | None = None
    max_out_amt: float | None = None
    min_out_amt: float | None = None
    n_unique_dest: float | None = None
    active_days: float | None = None
    tx_per_day: float | None = None
    odd_hour_ratio: float | None = None
    round_amount_ratio: float | None = None
    account_age_days: float | None = None
    age: float | None = None
    Balance: float | None = None
    AccountTypeID: float | None = None
    AccountStatusID: float | None = None
    CustomerTypeID: float | None = None
    n_loans: float | None = None
    total_principal: float | None = None
    avg_interest: float | None = None
    max_interest: float | None = None
    has_suspended_loan: float | None = None
    amt_to_balance_ratio: float | None = None
    loan_to_balance_ratio: float | None = None


@app.post("/score")
def score(rows: list[Row]):
    if not rows:
        raise HTTPException(400, "empty batch")
    try:
        out = predict_batch([r.model_dump() for r in rows])
        return out.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(500, str(e))