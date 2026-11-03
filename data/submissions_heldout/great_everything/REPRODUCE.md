# Reproduction guide
Tested on Python 3.11, macOS and Ubuntu 22.04.
```
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export API_KEY=<your key>
python src/baseline_keywords.py --syllabi data/syllabi/ --out results/keywords.json
python src/baseline_prompt.py   --syllabi data/syllabi/ --out results/prompt.json
python src/coursecheck.py       --syllabi data/syllabi/ --out results/coursecheck.json
python eval/score.py --gold eval/gold_maps.json --pred results/keywords.json results/prompt.json results/coursecheck.json
```
Expected: the table above. About 12 minutes and $0.80. All 45 syllabi are synthetic.
