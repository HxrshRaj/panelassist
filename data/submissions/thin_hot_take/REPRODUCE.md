# Reproduction guide

Tested on Python 3.11, `anthropic` SDK 0.40.0.

```
git clone <repo>
cd sortdesk
pip install -r requirements.txt
export ANTHROPIC_API_KEY=<your key>
python baseline/single_pass_sort.py --input data/overnight_queue.json --out out/baseline.json
python agent/three_bucket_sort.py --input data/overnight_queue.json --out out/agent.json
python eval/compare_to_manual.py --gold data/manual_sort.json --baseline out/baseline.json --agent out/agent.json
```

Expected: agreement percentages printed to stdout matching the changelog
table. ~4 minutes end-to-end, ~$0.05 total for the 35-ticket set.
