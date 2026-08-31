# Reproduction guide

Tested on Python 3.11.5, `anthropic` 0.40.0, macOS 14 and Windows 11. Eval
(200 files, baseline + agent): ~$0.12, ~4 minutes.

## Setup
```
git clone <repo>
cd tidydrop
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export ANTHROPIC_API_KEY=<your key>
```

## Get the test data
```
python eval/make_fixtures.py --from eval/fixtures.tar.gz --out data/messy_folder/
```
This unpacks the bundled 200 synthetic files (generated names + content, no
personal data) from `eval/fixtures.tar.gz` into `data/messy_folder/` (a
committed copy is already there). `eval/handsort.csv` is the author's manual
label for each of the 200.

## Run the baseline
```
python baseline/by_extension.py --folder data/messy_folder/ --out results/baseline.json
```

## Run the agent (dry run, no files move)
```
python src/tidydrop.py --folder data/messy_folder/ --plan-only --out results/agent.json
```

## Evaluate
```
python eval/score.py --labels eval/handsort.csv \
  --baseline results/baseline.json --agent results/agent.json --out eval/results.md
```

## Notes
`--plan-only` is used for the eval so nothing is moved. A real run drops
`--plan-only`, prints the plan, waits for `y`, then moves files and writes
`.tidydrop_undo.json`. `python src/tidydrop.py --undo` reverses the last run.
