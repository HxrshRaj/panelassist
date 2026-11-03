"""
Summarise repeated runs so the spread is visible next to every headline number.

Looks for  results/repeats/<set>/<config>_run<N>.json  (written by
eval/run_repeats.py), where <config> is baseline, full or lean. For each config
it reports, per run and across runs, MAE and Spearman against the human scores,
plus min / max / mean. It never fills in a missing run: if a config has fewer
than the requested number of runs, the table says how many it actually has.

    python eval/summarize_runs.py --set dev
    python eval/summarize_runs.py --set held-out --human data/human_scores_heldout.json

Writes eval/SPREAD_<set>.md and eval/spread_<set>.json. No key, no network.
"""
import argparse
import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.stats import mae, spearman

CONFIGS = ("baseline", "full", "lean")
RUN_RE = re.compile(r"^(?P<config>[a-z]+)_run(?P<n>\d+)\.json$")


def totals_from(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        scores = json.load(f)["scores"]
    return {slug: rec["total"] for slug, rec in scores.items()}


def summarise(human: dict, run_dir: str) -> dict:
    out = {}
    for config in CONFIGS:
        runs = []
        for path in sorted(glob.glob(os.path.join(run_dir, f"{config}_run*.json"))):
            m = RUN_RE.match(os.path.basename(path))
            if not m:
                continue
            totals = totals_from(path)
            slugs = sorted(s for s in human if s in totals)
            if len(slugs) < 2:
                continue
            h = [human[s]["total"] for s in slugs]
            t = [totals[s] for s in slugs]
            runs.append({"run": int(m.group("n")), "cases": len(slugs),
                         "mae": round(mae(t, h), 2), "spearman": round(spearman(t, h), 3)})
        if runs:
            maes = [r["mae"] for r in runs]
            rhos = [r["spearman"] for r in runs]
            out[config] = {
                "runs": runs, "n_runs": len(runs),
                "mae": {"min": min(maes), "max": max(maes), "mean": round(sum(maes) / len(maes), 2)},
                "spearman": {"min": min(rhos), "max": max(rhos), "mean": round(sum(rhos) / len(rhos), 3)},
            }
    return out


def render(set_name: str, summary: dict, wanted_runs: int) -> str:
    L = [f"# Run-to-run spread - {set_name} set\n"]
    if not summary:
        L += ["**Not run.** No files found under `results/repeats/` for this set. "
              "Generate them with `python eval/run_repeats.py` (needs a working LLM key), then re-run "
              "`python eval/summarize_runs.py`. No spread is reported until then.", ""]
        return "\n".join(L)
    L += [f"Each configuration was run up to {wanted_runs} times on identical inputs. Single-run numbers elsewhere "
          "in this repo should be read as one draw from this spread.", "",
          "| Configuration | Runs | MAE min | MAE mean | MAE max | Spearman min | Spearman mean | Spearman max |",
          "|---|---|---|---|---|---|---|---|"]
    for config, s in summary.items():
        flag = "" if s["n_runs"] >= wanted_runs else f" (only {s['n_runs']} of {wanted_runs})"
        L.append(f"| {config} | {s['n_runs']}{flag} | {s['mae']['min']} | {s['mae']['mean']} | {s['mae']['max']} | "
                 f"{s['spearman']['min']} | {s['spearman']['mean']} | {s['spearman']['max']} |")
    L += ["", "## Every run", "", "| Configuration | Run | Cases | MAE | Spearman |", "|---|---|---|---|---|"]
    for config, s in summary.items():
        for r in s["runs"]:
            L.append(f"| {config} | {r['run']} | {r['cases']} | {r['mae']} | {r['spearman']} |")
    L.append("")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", default="dev")
    ap.add_argument("--human", default="data/human_scores.json")
    ap.add_argument("--runs-dir", default=None, help="default results/repeats/<set>")
    ap.add_argument("--runs", type=int, default=3, help="how many runs were requested")
    args = ap.parse_args()
    with open(args.human, encoding="utf-8") as f:
        human = json.load(f)["submissions"]
    run_dir = args.runs_dir or os.path.join("results", "repeats", args.set)
    summary = summarise(human, run_dir)
    safe = args.set.replace(" ", "_")
    with open(f"eval/spread_{safe}.json", "w", encoding="utf-8") as f:
        json.dump({"set": args.set, "summary": summary}, f, indent=2)
    md = render(args.set, summary, args.runs)
    with open(f"eval/SPREAD_{safe}.md", "w", encoding="utf-8") as f:
        f.write(md)
    print(md)


if __name__ == "__main__":
    main()
