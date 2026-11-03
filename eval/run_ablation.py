"""
Produces the real, measured changelog: baseline -> stage1 (ledger, combined
call) -> stage2 (specialist split, no verification) -> final (specialist
split + verification), each scored against the same human panel ground
truth. Reuses results/agent_scores.json for the "final" numbers instead of
re-running them (they're identical to what run_agent.py already computed).
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.llm import get_call_log, reset_call_log
from common.loader import load_all_submissions
from common.stats import mae, spearman
from rubric import RUBRIC
from agent.panelassist.extract import build_evidence_ledger
from agent.panelassist.score import score_criterion
from agent.panelassist.ablations import stage1_ledger_combined, stage2_split_no_verification


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--submissions-dir", default="data/submissions")
    ap.add_argument("--human", default="data/human_scores.json")
    ap.add_argument("--baseline", default="results/baseline_scores.json")
    ap.add_argument("--agent-final", default="results/agent_scores.json")
    ap.add_argument("--lean", default="results/lean_scores.json",
                    help="optional: adds a lean-mode row if this file exists")
    ap.add_argument("--out", default="eval/ABLATIONS.md")
    args = ap.parse_args()

    with open(args.human) as f:
        human = json.load(f)["submissions"]
    with open(args.baseline) as f:
        baseline = json.load(f)["scores"]
    with open(args.agent_final) as f:
        final = json.load(f)["scores"]

    reset_call_log()
    subs = load_all_submissions(args.submissions_dir)

    # Reuse the exact evidence ledger the final pipeline used (run_agent.py
    # already built and saved it) rather than re-extracting -- cheaper, and
    # it removes "the ledger differed between stages" as a confound. Falls
    # back to a fresh extraction if a slug is somehow missing.
    with open(args.agent_final) as f:
        final_full = json.load(f)["scores"]

    stage1_results, stage2_results = {}, {}
    for sub in subs:
        print(f"[ablation] {sub['slug']}...", file=sys.stderr)
        saved = final_full.get(sub["slug"], {})
        evidence = saved.get("evidence_ledger") or build_evidence_ledger(sub)
        stage1_results[sub["slug"]] = stage1_ledger_combined(sub, evidence)
        stage2_results[sub["slug"]] = stage2_split_no_verification(sub, evidence, score_criterion)

    slugs = sorted(human.keys())
    human_totals = [human[s]["total"] for s in slugs]
    stages = {
        "baseline (raw text, 1 call)": [baseline[s]["total"] for s in slugs],
        "+ evidence ledger (1 combined call)": [stage1_results[s]["total"] for s in slugs],
        "+ specialist split, no verification": [stage2_results[s]["total"] for s in slugs],
        "+ verification (final)": [final[s]["total"] for s in slugs],
    }

    lean_note = None
    if os.path.exists(args.lean):
        with open(args.lean, encoding="utf-8") as f:
            lean = json.load(f)["scores"]
        if all(sl in lean for sl in slugs):
            stages["lean (one holistic score + flagged re-score only)"] = [lean[sl]["total"] for sl in slugs]
        else:
            lean_note = "Lean results exist but do not cover every case; row omitted."
    else:
        lean_note = ("Lean mode: not run (no results/lean_scores.json; needs a working LLM key). "
                     "See eval/LEAN_REPLAY.md for an offline estimate that is not a measurement.")

    lines = ["# Ablation: what each change actually contributed\n"]
    lines.append("| Stage | MAE vs. human (lower better) | Spearman vs. human (higher better) |")
    lines.append("|---|---|---|")
    for name, totals in stages.items():
        lines.append(f"| {name} | {round(mae(totals, human_totals), 2)} | {round(spearman(totals, human_totals), 3)} |")
    lines.append("")
    if lean_note:
        lines.append(lean_note)
        lines.append("")
    lines.append("## Per-submission totals across every stage\n")
    lines.append("| Submission | Human | Baseline | +Ledger | +Split | Final |")
    lines.append("|---|---|---|---|---|---|")
    for s in slugs:
        lines.append(
            f"| {s} | {human[s]['total']} | {baseline[s]['total']} | "
            f"{stage1_results[s]['total']} | {stage2_results[s]['total']} | {final[s]['total']} |"
        )
    lines.append("")

    out = "\n".join(lines)
    os.makedirs(os.path.dirname(args.out), exist_ok=True) if os.path.dirname(args.out) else None
    with open(args.out, "w") as f:
        f.write(out)

    call_log = get_call_log()
    print(f"Ablation LLM calls: {len(call_log)}", file=sys.stderr)
    print(out)


if __name__ == "__main__":
    main()
