# Reproduce

```
pip install -r requirements.txt
cp config/prod.yaml.example config/prod.yaml
bash scripts/seed_db.sh
export API_KEY=<your key>
python src/tripbrief.py --config config/prod.yaml --trips eval/trips_labeled.json
python eval/score.py
```

You also need the `.env.production` file from the team vault.
