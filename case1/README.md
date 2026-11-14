# Case 1: Fraud Risk Prediction

## Setup
python -m venv env 
pip install -r requirements.txt

## Run
python -m src.train          # clean data + train model, writes model in fraud_model.joblib
python -m src.evaluate       # writes evaluate metric in outputs/evaluate.json
python -m src.predict --input outputs/predict_input.json # predict, writes prediction in outputs/scored_input.json

## Tests
pytest -q