# Case 1 — Fraud Risk Prediction (V-TEKI)

## Setup
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

## Data
Place the four CSVs under data/raw/:
accounts.csv, customers.csv, loans.csv, transactions.csv

## Run
python -m src.train          # audit + clean + feature + train
python -m src.evaluate       # writes outputs/metrics.json
python -m src.predict --input outputs/scored_input.json
uvicorn src.api:app --reload # REST endpoint /score

## Tests
pytest -q

## Mapping to case requirements
| Requirement                       | Where                                       |
|-----------------------------------|---------------------------------------------|
| ≥3 related tables + DQ audit      | src/data_quality.py, README §Data-quality    |
| Behavioral features               | src/features.py (velocity, odd-hour, round)  |
| Prevent duplicate / PIT leakage   | tests/test_leakage.py, CUTOFF_DATE guard     |
| Baseline + alternative model      | src/train.py (LogReg + LightGBM)            |
| Risk score + reason codes + ver   | src/predict.py (SHAP)                       |
| Human review workflow             | `human_review_required`, `review_status`    |
| Precision/Recall/F1/CM/PR-AUC     | src/evaluate.py                             |
| Precision@K                       | src/evaluate.py                             |
| Privacy by Design (map/minimize)  | src/privacy.py, tests/test_privacy.py       |
| ≥2 security tests (incl. negative)| tests/test_privacy.py, tests/test_leakage.py |
| Architecture + cost estimate      | README §Architecture                        |
| Limitations                       | README §Limitations                         |
| AI-tool disclosure                | README §Disclosure                          |

## Data-quality issues found (documented)
- Duplicate TransactionID rows → dropped (keep first)
- TransactionDate missing → dropped (cannot be point-in-time)
- TransactionDate > 2022-06-01 (future/injected) → dropped
- Negative transaction amounts → dropped
- Self-transfer rows (Origin == Destination) → flagged, excluded
- customers.DateOfBirth: invalid format e.g. `07.04.1981`, `1985/07/09`,
  `NaT` → coerced to NaT, filled with median age
- accounts.OpeningDate missing → treated as unknown; `account_age_days` = 0
- accounts.Balance negative → kept (overdraft) but flagged in audit

## Architecture (data flow)