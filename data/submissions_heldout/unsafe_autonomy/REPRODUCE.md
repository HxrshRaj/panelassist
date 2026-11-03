# Reproduce
Python 3.11.
```
pip install -r requirements.txt
export API_KEY=<key>
export PAYMENTS_SANDBOX=1
python src/autoreply.py --emails eval/emails_labeled.jsonl --out results/autoreply.jsonl
python src/baseline_templates.py --emails eval/emails_labeled.jsonl --out results/templates.jsonl
python eval/score.py --labels eval/ratings.csv --pred results/templates.jsonl results/autoreply.jsonl
```
5 minutes, about $0.30. Emails are synthetic; the payments API is a sandbox stub.
