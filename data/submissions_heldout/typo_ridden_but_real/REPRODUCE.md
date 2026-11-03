# how to run
python 3.11
```
pip install -r requirements.txt
export API_KEY=...
python src/leaseflag.py --leases data/leases/ --out results/leaseflag.csv
python src/checklist_baseline.py --leases data/leases/ --out results/checklist.csv
python eval/score.py --planted eval/planted_clauses.csv --pred results/checklist.csv results/leaseflag.csv
```
10 minutes, about 1 dollar. leases are all synthetic.
