"""
Compares baseline vs. PanelAssist against the human-panel ground truth in
data/human_scores.json, using the same 6 mock submissions for both. Writes
eval/results.json (raw numbers) and eval/RESULTS.md (the report).
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.stats import spearman, mae
from rubric import RUBRIC
from common.llm import cost_estimate_usd

# Which deterministic verification check each seeded submission should trip,
# defined before any run happens -- so we're not retrofitting the metric to
# whatever the model happened to do.
EXPECTED_FLAGS = {
    "fabricated_claims": "claims_have_evidence",
    "broken_repro": "repro_paths_exist",
    "thin_hot_take": "hot_take_grounded",
}
EXPECTED_CLEAN = ["strong_baseline_done_right"]  # should trip none of the above


def load(path):
    with open(path) as f:
        return json.load(f)


def call_log_summary(call_log: list) -> dict:
    in_tok = sum(c["input_tokens"] for c in call_log)
    out_tok = sum(c["output_tokens"] for c in call_log)
    seconds = sum(c["seconds"] for c in call_log)
    # Use the provider recorded in the log, so this runs with no .env present.
    provider = call_log[0]["provider"] if call_log else None
    return {
        "num_calls": len(call_log),
        "input_tokens": in_tok,
        "output_tokens": out_tok,
        "seconds": round(seconds, 1),
        "cost_usd": round(cost_estimate_usd(in_tok, out_tok, provider), 4),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--human", default="data/human_scores.json")
    ap.add_argument("--baseline", default="results/baseline_scores.json")
    ap.add_argument("--agent", default="results/agent_scores.json")
    ap.add_argument("--out-json", default="eval/results.json")
    ap.add_argument("--out-md", default="eval/RESULTS.md")
    args = ap.parse_args()

    human = load(args.human)["submissions"]
    baseline = load(args.baseline)
    agent = load(args.agent)
    baseline_scores = baseline["scores"]
    agent_scores = agent["scores"]

    slugs = sorted(human.keys())

    human_totals = [human[s]["total"] for s in slugs]
    baseline_totals = [baseline_scores[s]["total"] for s in slugs]
    agent_totals = [agent_scores[s]["total"] for s in slugs]

    total_mae = {
        "baseline_vs_human": round(mae(baseline_totals, human_totals), 2),
        "agent_vs_human": round(mae(agent_totals, human_totals), 2),
    }
    ranking_correlation = {
        "baseline_vs_human_spearman": round(spearman(baseline_totals, human_totals), 3),
        "agent_vs_human_spearman": round(spearman(agent_totals, human_totals), 3),
    }

    per_criterion_mae = {"baseline": {}, "agent": {}}
    for c in RUBRIC:
        cid = c["id"]
        h = [human[s][cid] for s in slugs]
        b = [baseline_scores[s][cid] for s in slugs]
        a = [agent_scores[s]["per_criterion"][cid]["score"] for s in slugs]
        per_criterion_mae["baseline"][cid] = round(mae(b, h), 2)
        per_criterion_mae["agent"][cid] = round(mae(a, h), 2)

    # Seeded-issue detection: can the agent's deterministic verification
    # layer catch problems a confident single prompt has no mechanism to
    # catch at all? Baseline is 0/no-mechanism by construction -- that's the
    # point being measured, not an oversight.
    detection = {}
    tp = fn = 0
    for slug, expected_check in EXPECTED_FLAGS.items():
        flags = {f["check"]: f["passed"] for f in agent_scores[slug]["verification_flags"]}
        caught = (expected_check in flags) and (flags[expected_check] is False)
        detection[slug] = {"expected_check": expected_check, "caught_by_agent": caught}
        tp += int(caught)
        fn += int(not caught)
    fp = 0
    for slug in EXPECTED_CLEAN:
        flags = {f["check"]: f["passed"] for f in agent_scores[slug]["verification_flags"]}
        false_positives = [k for k, v in flags.items() if v is False]
        detection[slug] = {"expected_check": None, "false_positive_flags": false_positives}
        fp += len(false_positives)
    recall = tp / (tp + fn) if (tp + fn) else None
    precision = tp / (tp + fp) if (tp + fp) else None

    # Evidence-citation proxy for "human time per task": baseline returns one
    # rationale paragraph (0 structured citations); the agent returns cited
    # evidence per criterion. This is a proxy, not a measured minutes value --
    # flagged as an estimate in the report, not asserted as fact.
    agent_citation_counts = {
        s: sum(len(r.get("evidence_citations", [])) for r in agent_scores[s]["per_criterion"].values())
        for s in slugs
    }

    baseline_cost = call_log_summary(baseline["call_log"])
    agent_cost = call_log_summary(agent["call_log"])

    results = {
        "slugs": slugs,
        "human_totals": dict(zip(slugs, human_totals)),
        "baseline_totals": dict(zip(slugs, baseline_totals)),
        "agent_totals": dict(zip(slugs, agent_totals)),
        "total_score_mae_vs_human": total_mae,
        "ranking_correlation_vs_human": ranking_correlation,
        "per_criterion_mae_vs_human": per_criterion_mae,
        "seeded_issue_detection": {
            "per_submission": detection,
            "agent_recall_on_seeded_issues": round(recall, 3) if recall is not None else None,
            "agent_precision_on_seeded_issues": round(precision, 3) if precision is not None else None,
            "baseline_recall": 0.0,
            "baseline_note": "Single-prompt baseline has no verification mechanism to catch these by construction.",
        },
        "evidence_citations_per_submission": agent_citation_counts,
        "baseline_cost": baseline_cost,
        "agent_cost": agent_cost,
    }

    os.makedirs(os.path.dirname(args.out_json), exist_ok=True)
    with open(args.out_json, "w") as f:
        json.dump(results, f, indent=2)

    md = render_markdown(results, slugs)
    with open(args.out_md, "w") as f:
        f.write(md)

    print(md)


def render_markdown(r: dict, slugs: list) -> str:
    lines = ["# PanelAssist vs. baseline vs. human panel\n"]

    lines.append("## Per-submission totals (out of 100)\n")
    lines.append("| Submission | Human panel | Baseline | PanelAssist |")
    lines.append("|---|---|---|---|")
    for s in slugs:
        lines.append(f"| {s} | {r['human_totals'][s]} | {r['baseline_totals'][s]} | {r['agent_totals'][s]} |")
    lines.append("")

    lines.append("## Summary metrics\n")
    lines.append("| Metric | Simple baseline | PanelAssist agent | Change |")
    lines.append("|---|---|---|---|")
    b_mae = r["total_score_mae_vs_human"]["baseline_vs_human"]
    a_mae = r["total_score_mae_vs_human"]["agent_vs_human"]
    lines.append(f"| Mean absolute error vs. human total score (lower is better) | {b_mae} | {a_mae} | {round(b_mae - a_mae, 2):+} pts |")
    b_rho = r["ranking_correlation_vs_human"]["baseline_vs_human_spearman"]
    a_rho = r["ranking_correlation_vs_human"]["agent_vs_human_spearman"]
    lines.append(f"| Spearman rank correlation vs. human ranking (higher is better) | {b_rho} | {a_rho} | {round(a_rho - b_rho, 3):+} |")
    lines.append(f"| Recall on seeded issues (fabricated claim / broken repro / thin hot take) | {r['seeded_issue_detection']['baseline_recall']} (no mechanism) | {r['seeded_issue_detection']['agent_recall_on_seeded_issues']} | n/a |")
    lines.append(f"| Precision on seeded-issue flags (no false alarms on the clean submission) | n/a | {r['seeded_issue_detection']['agent_precision_on_seeded_issues']} | n/a |")
    lines.append(f"| LLM calls per submission | {r['baseline_cost']['num_calls'] // len(slugs)} | {r['agent_cost']['num_calls'] // len(slugs)} | {r['agent_cost']['num_calls'] // len(slugs) - r['baseline_cost']['num_calls'] // len(slugs):+} |")
    lines.append(f"| Total cost, all {len(slugs)} submissions (est., see common/llm.py rates) | ${r['baseline_cost']['cost_usd']} | ${r['agent_cost']['cost_usd']} | +${round(r['agent_cost']['cost_usd'] - r['baseline_cost']['cost_usd'], 4)} |")
    lines.append(f"| Wall-clock time, all {len(slugs)} submissions | {r['baseline_cost']['seconds']}s | {r['agent_cost']['seconds']}s | +{round(r['agent_cost']['seconds'] - r['baseline_cost']['seconds'], 1)}s |")
    lines.append("")

    lines.append(
        "Human time per task is not directly measured here (that needs a "
        "real judging session to time). As a proxy: the baseline returns "
        "one rationale paragraph with zero structured citations per "
        "submission, so a human still has to go re-find the evidence "
        "themselves before trusting a score; PanelAssist returns "
        f"{sum(r['evidence_citations_per_submission'].values())} total cited "
        "pieces of evidence across the 6 criteria x 6 submissions, one per "
        "sub-score. We're stating that as a citation count, not converting "
        "it into a minutes-saved number we can't actually back up.\n"
    )

    lines.append("## Per-criterion mean absolute error vs. human (lower is better)\n")
    lines.append("| Criterion | Baseline MAE | Agent MAE |")
    lines.append("|---|---|---|")
    for c in RUBRIC:
        cid = c["id"]
        lines.append(f"| {c['name']} | {r['per_criterion_mae_vs_human']['baseline'][cid]} | {r['per_criterion_mae_vs_human']['agent'][cid]} |")
    lines.append("")

    lines.append("## Seeded-issue detection (the case the baseline structurally cannot handle)\n")
    for slug, d in r["seeded_issue_detection"]["per_submission"].items():
        if "expected_check" in d and d["expected_check"]:
            lines.append(f"- **{slug}**: expected to trip `{d['expected_check']}` -> {'caught' if d['caught_by_agent'] else 'MISSED'}")
        else:
            fps = d.get("false_positive_flags", [])
            lines.append(f"- **{slug}** (should stay clean): {'no false alarms' if not fps else f'false positive on {fps}'}")
    lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    main()
