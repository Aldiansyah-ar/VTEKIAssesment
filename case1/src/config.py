from pathlib import Path
import os

os.environ.setdefault("LOKY_MAX_CPU_COUNT", "1")

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
MODEL_DIR = ROOT / "models"
OUTPUT_DIR = ROOT / "outputs"
MODEL_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_PREDICTION_OUTPUT = OUTPUT_DIR / "predict_output.json"

ACCOUNTS_CSV   = DATA_DIR / "accounts.csv"
CUSTOMERS_CSV  = DATA_DIR / "customers.csv"
LOANS_CSV      = DATA_DIR / "loans.csv"
TRANSACTIONS_CSV = DATA_DIR / "transactions.csv"

RANDOM_STATE = 42
MODEL_VERSION = "v1.0.0"

CUTOFF_DATE = "2021-07-01"
MAX_VALID_DATE = "2022-06-01"

PII_COLUMNS = ["FirstName", "LastName", "DateOfBirth", "CustomerID", "AccountID"]