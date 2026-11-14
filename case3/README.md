# Case 3: Enterprise Knowledge Chatbot

## Setup
python -m venv env 
pip install -r requirements.txt

## Run Chatbot
python -m src.cli --role passenger               # interactive mode
python -m src.cli --role passenger --query "What is the carry-on weight limit for Economy Class?"                                                # single query
python -m src.cli --role passenger --query "What is the escalation code ESC-BAG-03?" # Role-Based Access Control, if passenger ask about staff document then rejected
python -m src.cli --role passenger --query "What is the carry-on weight limit for Economy Class?"                                                # writes in outputs/results.json
python -m eval.evaluate                          # writes evaluate metric in outputs/evaluate.json

## Tests
pytest -q