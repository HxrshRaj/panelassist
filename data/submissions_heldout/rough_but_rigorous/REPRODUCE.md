# repro
python 3.11
```
pip install -r requirements.txt
export API_KEY=...
python src/logtriage.py --in eval/incidents_labeled.jsonl --out results/logtriage.jsonl
python src/grep_baseline.py --in eval/incidents_labeled.jsonl --out results/grep.jsonl
python src/single_prompt.py --in eval/incidents_labeled.jsonl --out results/single.jsonl
python eval/score.py --labels eval/incidents_labeled.jsonl --pred results/*.jsonl
```
~6 min, ~$0.40. incidents are synthetic.
