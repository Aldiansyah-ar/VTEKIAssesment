# Case 2: Document Intelligence

## Setup
python -m venv env 
pip install -r requirements.txt

## Run
python -m src.make_synthetic_samples                  # create the synthetic samples, writes in samples/
python -m src.cli extract samples/invoice.pdf         # extract data from invoice.pdf, writes in outputs/invoice.json
python -m src.evaluate                                # writes evaluate metric in outputs/evaluation.json

## Tests
pytest -q