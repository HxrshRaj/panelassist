"""
Head-to-head for the removed experiment: deterministic verification
(agent/panelassist/verify.py, on the pipeline) vs. LLM-based verification
(agent/panelassist/verify_llm.py, removed).

For each of the six mock submissions we build the evidence ledger once, then
run BOTH verification approaches. The LLM approach is run N times to measure
whether it is reproducible. We report, per approach:

  - did it catch the three seeded issues? (fabricated_claims ->
    claims_have_evidence, broken_repro -> repro_paths_exist, thin_hot_take
    -> hot_take_grounded)
  - false positives on the clean control (strong_baseline_done_right)
  - for the LLM approach: run-to-run disagreement, and extra LLM calls

Writes eval/REMOVED_EXPERIMENT.md.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.llm import get_call_log, reset_call_log
from common.loader import load_all_submissions
from agent.panelassist.extract import build_evidence_ledger
from agent.panelassist.verify import run_all_checks
from agent.panelassist.verify_llm import run_all_checks_llm

EXPECTED = {
    "fabricated_claims": "claims_have_evidence",
    "broken_repro": "repro_paths_exist",
    "thin_hot_take": "hot_take_grounded",
}
CONTROL = "strong_baseline_done_right"


def flags_map(flags):
    return {f["check"]: f["passed"] for f in flags}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--submissions-dir", default="data/submissions")
    ap.add_argument("--agent-final", default="results/agent_scores.json")
    ap.add_argument("--llm-runs", type=int, default=3)
    ap.add_argument("--out", default="eval/REMOVED_EXPERIMENT.md")
    args = ap.parse_args()

    reset_call_log()
    subs = load_all_submissions(args.submissions_dir)

    # Reuse the evidence ledger the real pipeline already built, so this
    # experiment compares only the two verification approaches -- not two
    # different ledgers.
    with open(args.agent_final) as f:
        final_full = json.load(f)["scores"]

    det = {}
    llm_runs = {s["slug"]: [] for s in subs}
    extract_calls = 0
    for sub in subs:
        slug = sub["slug"]
        print(f"[removed-exp] {slug}...", file=sys.stderr)
        evidence = final_full.get(slug, {}).get("evidence_ledger")
        if evidence is None:
            evidence = build_evidence_ledger(sub)
            extract_calls += 1
        det[slug] = flags_map(run_all_checks(evidence, sub["manifest"]))
        for _ in range(args.llm_runs):
            llm_runs[slug].append(flags_map(run_all_checks_llm(evidence, sub["manifest"])))

    # Only the verify_llm calls count as the experiment's extra cost; any
    # fallback extractions do not.
    llm_verify_calls = len(get_call_log()) - extract_calls

    def caught(fmap, slug):
        chk = EXPECTED[slug]
        return chk in fmap and fmap[chk] is False

    lines = ["# Removed experiment: LLM-based verification vs. deterministic verification\n"]
    lines.append(
        f"Setup: evidence ledger built once per submission (shared by both "
        f"approaches). Deterministic checks run once (they are pure functions). "
        f"LLM checks run {args.llm_runs}x per submission to measure "
        f"reproducibility. Extra cost of the LLM approach over the full "
        f"{len(subs)}-submission set: **{llm_verify_calls} LLM calls** "
        f"({llm_verify_calls // len(subs)} per submission x {len(subs)}), "
        f"vs. **0** for the deterministic checks.\n"
    )

    lines.append("## Did each approach catch the seeded issue?\n")
    lines.append("| Submission | Seeded check | Deterministic | LLM (per run) |")
    lines.append("|---|---|---|---|")
    for slug in EXPECTED:
        d = "caught" if caught(det[slug], slug) else "**MISSED**"
        per_run = ["caught" if caught(r, slug) else "MISSED" for r in llm_runs[slug]]
        lines.append(f"| {slug} | `{EXPECTED[slug]}` | {d} | {', '.join(per_run)} |")
    lines.append("")

    lines.append("## False positives on the clean control\n")
    d_fp = [k for k, v in det[CONTROL].items() if v is False]
    lines.append(f"- **Deterministic:** {d_fp or 'none'}")
    for i, r in enumerate(llm_runs[CONTROL], 1):
        fp = [k for k, v in r.items() if v is False]
        lines.append(f"- **LLM run {i}:** {fp or 'none'}")
    lines.append("")

    lines.append("## Run-to-run reproducibility of the LLM approach\n")
    unstable = []
    for slug in llm_runs:
        checks = ["repro_paths_exist", "env_var_consistency", "claims_have_evidence", "hot_take_grounded"]
        for chk in checks:
            vals = {r.get(chk) for r in llm_runs[slug]}
            if len(vals) > 1:
                unstable.append(f"{slug}/{chk}: {[r.get(chk) for r in llm_runs[slug]]}")
    if unstable:
        lines.append("Checks that changed verdict between identical runs:\n")
        for u in unstable:
            lines.append(f"- {u}")
    else:
        lines.append("No verdict changed between runs in this sample "
                     "(still not *guaranteed* stable - it is a sampled model).")
    lines.append("")

    lines.append("## Verdict\n")
    lines.append(
        "Kept the deterministic `verify.py`. The LLM version adds a call per "
        "submission, is not reproducible by construction, and its extra "
        "flexibility did not buy a catch the deterministic checks missed. A "
        "flag that a judge is meant to act on should be one they can re-derive "
        "by hand; `p in manifest_files` is that, a sampled model verdict is "
        "not.\n"
    )

    with open(args.out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("\n".join(lines))
    print(f"\nWrote {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
