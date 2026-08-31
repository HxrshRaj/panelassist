# Reproduction guide

Tested on Python 3.11.7, `anthropic` 0.40.0, macOS 14 and Ubuntu 22.04.
Full eval (30 labeled items, baseline + agent): ~$0.35, ~7 minutes.

## Setup
```
git clone <repo>
cd docsync-ai
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export ANTHROPIC_API_KEY=<your key>
```

## Run the baseline
```
python baseline/prompt_only.py --diff data/release_diffs/ --docs data/docs_snapshot/ --out results/baseline.json
```

## Run the agent
```
python src/docsync.py --diff data/release_diffs/ --docs data/docs_snapshot/ --out results/agent.json
```
Output: `results/agent.json` with one record per detected mismatch plus a
`docs.patch` file.

## Run the evaluation
```
python eval/score.py --labels eval/labeled_mismatches.json \
  --baseline results/baseline.json --agent results/agent.json --out eval/results.md
```
Prints precision / recall / F1 for both and regenerates the README table.

## Data
`data/release_diffs/` - 8 real release diffs from an MIT-licensed open-source
library, included with the license file.
`data/docs_snapshot/` - the matching docs-site markdown at each release.
`eval/labeled_mismatches.json` - 30 mismatches labeled by two maintainers.
