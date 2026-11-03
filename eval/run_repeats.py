"""
Run every configuration N times on one submission set, so the spread can be
reported. This makes real LLM calls (7 per submission per full run), so it
needs a working key and costs real money; it is never run in CI.

    python eval/run_repeats.py --set dev --runs 3
    python eval/run_repeats.py --set held-out --runs 3 \
        --submissions-dir data/submissions_heldout

Outputs results/repeats/<set>/<config>_run<N>.json. Summarise with
eval/summarize_runs.py.
"""
import argparse
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run(cmd):
    print("+", " ".join(cmd), file=sys.stderr)
    subprocess.run(cmd, cwd=ROOT, check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", default="dev")
    ap.add_argument("--submissions-dir", default="data/submissions")
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--configs", nargs="+", default=["baseline", "full", "lean"],
                    choices=["baseline", "full", "lean"])
    args = ap.parse_args()

    out_dir = os.path.join("results", "repeats", args.set.replace(" ", "_"))
    os.makedirs(os.path.join(ROOT, out_dir), exist_ok=True)
    py = sys.executable
    for n in range(1, args.runs + 1):
        for config in args.configs:
            out = os.path.join(out_dir, f"{config}_run{n}.json")
            if config == "baseline":
                run([py, "baseline/baseline_scorer.py", "--submissions-dir", args.submissions_dir, "--out", out])
            else:
                traj = os.path.join(out_dir, f"{config}_traj_run{n}.json")
                run([py, "agent/run_agent.py", "--mode", config, "--submissions-dir", args.submissions_dir,
                     "--out", out, "--trajectories-out", traj])


if __name__ == "__main__":
    main()
