"""
CLI entrypoint for the PanelAssist agent -- the advanced solution.
Mirrors baseline/baseline_scorer.py's interface so the two are a fair,
drop-in comparison over the same submissions.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.llm import get_call_log, reset_call_log
from common.loader import load_all_submissions
from agent.panelassist.orchestrate import review_submission


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--submissions-dir", default="data/submissions")
    ap.add_argument("--out", default="results/agent_scores.json")
    ap.add_argument("--trajectories-out", default="trajectories/panelassist_runs.json")
    args = ap.parse_args()

    reset_call_log()
    subs = load_all_submissions(args.submissions_dir)
    results = {}
    for sub in subs:
        print(f"[agent] reviewing {sub['slug']}...", file=sys.stderr)
        results[sub["slug"]] = review_submission(sub)

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w") as f:
        json.dump({"scores": results, "call_log": get_call_log()}, f, indent=2)
    print(f"Wrote {args.out}")

    os.makedirs(os.path.dirname(args.trajectories_out), exist_ok=True)
    with open(args.trajectories_out, "w") as f:
        json.dump(
            {
                slug: {
                    "evidence_ledger": r["evidence_ledger"],
                    "verification_flags": r["verification_flags"],
                    "per_criterion_calls": r["per_criterion"],
                    "review_notes_accumulated": r["review_notes"],
                }
                for slug, r in results.items()
            },
            f, indent=2,
        )
    print(f"Wrote {args.trajectories_out}")


if __name__ == "__main__":
    main()
