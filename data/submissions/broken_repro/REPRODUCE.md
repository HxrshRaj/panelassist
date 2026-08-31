# Reproduction guide

## Setup
```
pip install -r requirements.txt
export OPENAI_API_KEY=<your key>
```

## Run the baseline
```
python baseline/independent_scorer.py --input data/batch1.json
```

## Run the agent
```
python agent/batch_reranker.py --input data/batch1.json --config config/reranker.yaml
```

## Run evaluation
```
python evaluate.py --predictions out/predictions.json --gold data/manual_ranking.json
```

Expected output: a ranking agreement percentage printed to stdout, matching
the changelog table in the README.
