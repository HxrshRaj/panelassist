# Reproduction
Python 3.11.
```
pip install -r requirements.txt
export API_KEY=<key>
python src/rules.py --tickets eval/tickets_labeled.csv --out results/rules.csv
python src/rules_tuned.py --tickets eval/tickets_labeled.csv --out results/rules_tuned.csv
python src/agent.py --tickets eval/tickets_labeled.csv --out results/agent_run1.csv
python eval/score.py --labels eval/tickets_labeled.csv --pred results/rules.csv results/rules_tuned.csv results/agent_run1.csv
```
About 8 minutes and $0.60 for three agent runs. Tickets are synthetic.
