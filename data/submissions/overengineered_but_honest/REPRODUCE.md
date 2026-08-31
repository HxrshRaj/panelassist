# Reproduction guide

Tested on Python 3.11.6, `anthropic` 0.40.0, macOS and Ubuntu 22.04. Full
eval (8 calls x 60 faculty, baseline + agent): ~$1.40, ~30 minutes.

## Setup
```
git clone <repo>
cd grantmatch
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export ANTHROPIC_API_KEY=<your key>
```

## Run the baseline
```
python baseline/one_shot_rank.py --calls data/calls/ --faculty data/faculty.json --out results/baseline.json
```

## Run the agent
```
python src/grantmatch.py --calls data/calls/ --faculty data/faculty.json --out results/agent.json
```
Writes `results/agent.json` (ranked shortlist + reasons + hard-constraint
flags per call) and `results/agent_trace/` (per-agent inputs and outputs).

## Evaluate
```
python eval/score.py --gold eval/officer_rankings.json \
  --baseline results/baseline.json --agent results/agent.json --out eval/results.md
```
Reports nDCG@10, hard-constraint violation counts, and unsupported-reason
rate for both.

## Data
`data/calls/` - 8 real funding calls (public agency announcements, with
source URLs in `data/calls/SOURCES.md`).
`data/faculty.json` - 60 synthetic faculty profiles we generated (research
statement + 5 publication titles each); no real individuals.
`eval/officer_rankings.json` - the RD officer's own top-10 for each of the 8
calls, collected before they saw any agent output.
