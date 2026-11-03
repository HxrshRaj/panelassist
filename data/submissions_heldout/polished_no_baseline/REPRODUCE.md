# Reproduction
Python 3.11.
```
pip install -r requirements.txt
export API_KEY=<your key>
python src/shiftswap.py --requests eval/swaps_labeled.csv --out results/agent.csv
python src/random_baseline.py --requests eval/swaps_labeled.csv --out results/random.csv
python eval/score.py --labels eval/swaps_labeled.csv --pred results/agent.csv results/random.csv
```
About 4 minutes and under $0.10. The 40 requests are synthetic.
