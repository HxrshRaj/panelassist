# Reproduction guide

Tested on Python 3.11.6, `anthropic` SDK 0.40.0, macOS and Ubuntu 22.04.
Approximate cost for the full eval set (40 labeled tickets, baseline + agent):
$0.34, ~9 minutes wall-clock.

## Setup
```
git clone <repo>
cd ticket-triage
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export ANTHROPIC_API_KEY=<your key>
```

## Run the baseline
```
python baseline/baseline_triage.py --input data/tickets.jsonl --out results/baseline.jsonl
```
Expected output: `results/baseline.jsonl`, one triage decision per ticket line.

## Run the agent
```
python src/agent_triage.py --input data/tickets.jsonl --out results/agent.jsonl
```
Expected output: `results/agent.jsonl`, same schema plus `verification_flag`
and `evidence_quote` fields.

## Run the evaluation
```
python eval/score_against_labels.py --labels eval/labels.csv \
  --baseline results/baseline.jsonl --agent results/agent.jsonl \
  --out eval/results.md
```
This regenerates the table in the README's changelog section and prints
per-category accuracy plus P0/P1 recall to stdout.

## Data
`data/tickets.jsonl` — 40 synthetic support tickets we wrote ourselves,
modeled on common SaaS support categories. No real customer data.
`eval/labels.csv` — our own urgency/category labels for those 40 tickets,
double-checked by two of the four support agents on the team.
