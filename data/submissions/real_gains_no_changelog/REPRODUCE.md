# Reproduction guide

Tested on Python 3.11, `anthropic` 0.42.0, Ubuntu 22.04. The sandbox uses
`bubblewrap`; on macOS it falls back to a Docker container (`--runner
docker`). Full replay of 12 incidents, baseline + agent: ~$0.60, ~18 min.

## Setup
```
git clone <repo>
cd runbookrunner
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export ANTHROPIC_API_KEY=<your key>
```

## Run the baseline
The baseline is scripted replay of the human transcripts (no agent):
```
python baseline/manual_replay.py --incidents data/incidents/ --out results/baseline.json
```

## Run the agent
```
python src/runbookrunner.py --incidents data/incidents/ --replay --out results/agent.json
```
`--replay` feeds recorded command outputs instead of hitting real infra, and
auto-approves the state-change prompts using the recorded responder
decisions so the run is non-interactive.

## Evaluate
```
python eval/score.py --incidents data/incidents/ \
  --baseline results/baseline.json --agent results/agent.json --out eval/results.md
```

## Data
`data/incidents/` - 12 synthetic incidents we wrote, each with a runbook, an
alert payload, and recorded command outputs. No real infrastructure or
customer data. `data/runbooks/` - the 6 runbooks. `eval/rubric.md` - how
"correct first action" and "wrong branch" were judged, applied by two SREs.
