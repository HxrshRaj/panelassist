# Reproduction
```
pip install -r requirements.txt
export OPENAI_API_KEY=<your key>
python src/baseline_exact.py --stories data/stories/ --out results/exact.csv
python src/quotecheck.py --stories data/stories/ --out results/quotecheck.csv
python eval/score.py --altered eval/altered_quotes.csv --pred results/exact.csv results/quotecheck.csv
```
About 5 minutes and $0.20. Stories are synthetic.
