Python 3.11.

    pip install -r requirements.txt
    export API_KEY=<key>
    python src/pr_risk.py --prs data/prs/ --out results/pr_risk.csv
    python src/baseline_loc.py --prs data/prs/ --out results/baseline.csv
    python eval/score.py --labels eval/labels.csv --pred results/baseline.csv results/pr_risk.csv

3 minutes, about $0.10. The 90 PRs are synthetic.
