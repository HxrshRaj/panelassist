repro
- py 3.11, `pip install -r requirements.txt`
- `export API_KEY=...`
- baseline: `python src/baseline_doi.py --in data/sheets/ --out results/baseline.csv`
- tool: `python src/dedup_notes.py --in data/sheets/ --out results/tool.csv`
- score: `python eval/score.py --truth eval/true_dupes.csv --pred results/baseline.csv results/tool.csv`
- ~2 min, ~$0.05. all data synthetic.
