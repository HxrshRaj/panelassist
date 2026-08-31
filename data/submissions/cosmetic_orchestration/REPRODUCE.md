# Setup

```
pip install -r requirements.txt
export ANTHROPIC_API_KEY=<your key>
python baseline/single_prompt.py --input data/tickets20.json --out out/baseline.json
python swarm/controller.py --input data/tickets20.json --out out/swarm.json
python eval/score.py --gold data/labels20.json --baseline out/baseline.json --agent out/swarm.json
```

Expected: accuracy printed for both, matching the changelog table.
~11 minutes end-to-end for the swarm run (6 agents x 20 tickets = 120 calls),
~$0.9 total, versus ~40 seconds and $0.02 for the baseline.
