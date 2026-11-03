"""
Offline REPLAY estimate of lean mode. This is NOT a live run of lean mode.

It answers one narrow question using only outputs that are already saved:
"if lean mode kept the baseline's per-criterion scores and swapped in the
full pipeline's specialist score only for criteria a failed check touches,
what total would it have produced, and how many LLM calls would that have
needed?"

Why it is only an estimate (and why no result here may be quoted as lean
mode's measured error):
  * the baseline scores and the full-pipeline scores come from two different
    stored runs, so run-to-run noise is mixed in;
  * a real lean re-score sees different context (no running notes from the
    criteria it did not re-score), so its scores could differ from the full
    pipeline's specialist scores;
  * it only models the four original checks, because the stored full run
    pre-dates the write-up check.

Needs no API key and makes no network call. Writes eval/LEAN_REPLAY.md and
eval/lean_replay.json.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.stats import mae, spearman
from rubric import RUBRIC
from agent.panelassist.v2 import criteria_touched_by


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--human", default="data/human_scores.json")
    ap.add_argument("--baseline", default="results/baseline_scores.json")
    ap.add_argument("--agent", default="results/agent_scores.json")
    ap.add_argument("--out-md", default="eval/LEAN_REPLAY.md")
    ap.add_argument("--out-json", default="eval/lean_replay.json")
    args = ap.parse_args()

    human = load(args.human)["submissions"]
    base = load(args.baseline)["scores"]
    agent = load(args.agent)["scores"]
    slugs = sorted(s for s in human if s in base and s in agent)
    caps = {c["id"]: c["points"] for c in RUBRIC}

    rows, h_tot, b_tot, a_tot, r_tot, calls = [], [], [], [], [], []
    for s in slugs:
        touched = criteria_touched_by(agent[s]["verification_flags"])
        replay = 0
        for c in RUBRIC:
            cid = c["id"]
            if cid in touched:
                replay += agent[s]["per_criterion"][cid]["score"]
            else:
                replay += max(0, min(int(base[s][cid]), caps[cid]))
        h_tot.append(human[s]["total"])
        b_tot.append(base[s]["total"])
        a_tot.append(agent[s]["total"])
        r_tot.append(replay)
        calls.append(2 + len(touched))
        rows.append((s, human[s]["total"], base[s]["total"], agent[s]["total"], replay, touched))

    result = {
        "n_cases": len(slugs),
        "mae_vs_human": {"baseline": round(mae(b_tot, h_tot), 2),
                         "full": round(mae(a_tot, h_tot), 2),
                         "lean_replay_estimate": round(mae(r_tot, h_tot), 2)},
        "spearman_vs_human": {"baseline": round(spearman(b_tot, h_tot), 3),
                              "full": round(spearman(a_tot, h_tot), 3),
                              "lean_replay_estimate": round(spearman(r_tot, h_tot), 3)},
        "llm_calls_per_submission": {"baseline": 1, "full": 7,
                                     "lean_expected": round(sum(calls) / len(calls), 2)},
        "per_case": [{"slug": r[0], "human": r[1], "baseline": r[2], "full": r[3],
                      "lean_replay": r[4], "criteria_rescored": r[5]} for r in rows],
        "caveat": "Replay from stored outputs, not a live run of lean mode.",
    }
    with open(args.out_json, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    m, sp, lc = result["mae_vs_human"], result["spearman_vs_human"], result["llm_calls_per_submission"]
    lines = [
        "# Lean mode - offline replay estimate",
        "",
        "> **This is not a measured result for lean mode.** It replays saved outputs (see "
        "`eval/replay_lean.py` for exactly how and why it can differ from a live run). "
        "Nothing here may be quoted as lean mode's MAE. A live run is `python agent/run_agent.py "
        "--mode lean` followed by `python eval/run_eval.py`.",
        "",
        f"Cases: {result['n_cases']} (dev set). Same stored runs as `eval/RESULTS.md`.",
        "",
        "| | Baseline (stored run) | Full pipeline (stored run) | Lean (replay estimate) |",
        "|---|---|---|---|",
        f"| MAE vs. human (lower better) | {m['baseline']} | {m['full']} | {m['lean_replay_estimate']} |",
        f"| Spearman vs. human | {sp['baseline']} | {sp['full']} | {sp['lean_replay_estimate']} |",
        f"| LLM calls per submission | {lc['baseline']} | {lc['full']} | {lc['lean_expected']} (expected: 2 + criteria re-scored) |",
        "",
        "## Per case",
        "",
        "| Submission | Human | Baseline | Full | Lean replay | Criteria re-scored |",
        "|---|---|---|---|---|---|",
    ]
    for r in rows:
        lines.append(f"| {r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]} | {', '.join(r[5]) or '-'} |")
    lines += ["", f"Mean criteria re-scored per submission: {round(sum(c - 2 for c in calls) / len(calls), 2)}.", ""]
    with open(args.out_md, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
