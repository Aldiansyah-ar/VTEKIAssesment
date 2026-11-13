# Case 3: Enterprise Knowledge Chatbot

## Setup
python -m venv env 
pip install -r requirements.txt

## Run Chatbot
python src/cli.py --role passenger                  # interactive mode
python src/cli.py --role passenger --query "What is the carry-on weight limit for Economy Class?"   # single query
python src/cli.py --role passenger --query "What is the escalation code ESC-BAG-03?" # Role-Based Access Control, if passenger ask about staff document then rejected
python src/cli.py --role passenger --query "What is the carry-on weight limit for Economy Class?" --output-name outputs/results.json                  # writes in outputs/results.json
python eval/evaluate.py --output-name outputs/evaluation.json   # writes evaluate metric in outputs/evaluation.json

## Tests
pytest -q