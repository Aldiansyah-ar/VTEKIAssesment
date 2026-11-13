# Case 2 — Document Intelligence

## Setup
python -m venv env 
pip install -r requirements.txt

## Run
python -m src.make_synthetic_samples.py                   # create the synthetic samples, writes in samples/
python -m src.cli extract samples/invoice.pdf --output outputs/invoice.json   # extract data from invoice.pdf, writes in outputs/invoice.json
python -m src.evaluate --output outputs/evaluation.json      # writes evaluate metric in outputs/evaluation.json

## Tests
pytest -q