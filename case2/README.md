# Case 2 — Document Intelligence (Invoice Extraction)

Extracts structured invoice data from PDF with **offline regex parsing** (default) or
opt-in LLM path. Structured JSON with confidence, review routing, and PII masking.

## Setup
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# place your uploaded invoice as:
cp /path/to/invoice.pdf samples/invoice.pdf
python scripts/make_synthetic_samples.py