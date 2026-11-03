"""
Compares baseline vs. the full PanelAssist pipeline (and, when its results
file exists, lean mode) against the human-panel ground truth.

Default invocation evaluates the dev set and writes eval/results.json and
eval/RESULTS.md, exactly as before. The held-out set is evaluated with
explicit paths (see REPRODUCE.md) and writes separate files, so the two are
never mixed:

    python eval/run_eval.py \
        --human data/human_scores_heldout.json \
        --expected data/expected_checks_heldout.json \
        --baseline results/heldout/baseline_scores.json \
        --agent results/heldout/agent_scores.json \
        --lean results/heldout/lean_scores.json \
        --label "held-out" \
        --out-json eval/results_heldout.json --out-md eval/RESULTS_heldout.md

Results files that do not exist are reported as "not run", never invented.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.stats import spearman, mae
from rubric import RUBRIC
from common.llm import cost_estimate_usd

ORIGINAL_CHECKS = ("repro_paths_exist", "env_var_consistency",
                   "claims_have_evidence", "hot_take_grounded")

# Dev-set expectations, fixed before any run (so the metric is not retrofitted
# to whatever the model did): which original check each planted defect should
# trip, and which submissions are honest as far as those four checks go.
DEV_PLANTED = {
    "fabricated_claims": "claims_have_evidence",
    "broken_repro": "repro_paths_exist",
    "thin_hot_take": "hot_take_grounded",
}
DEV_HONEST = [
    "strong_baseline_done_right",
    "good_project_bad_writeup",
    "real_gains_no_changelog",
    "overengineered_but_honest",
    "scope_mismatch",
]
# The write-up check is evaluated separately: it should fire on this one dev
# case and stay quiet on the other honest ones.
DEV_WRITEUP_FLAGGED = ["good_project_bad_writeup"]


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_optional(path):
    return load(path) if path and os.path.exists(path) else None


def call_log_summary(call_log: list) -> dict:
    in_tok = sum(c["input_tokens"] for c in call_log)
    out_tok = sum(c["output_tokens"] for c in call_log)
    seconds = sum(c["seconds"] for c in call_log)
    provider = call_log[0]["provider"] if call_log else None  # works with no .env
    return {
        "num_calls": len(call_log),
        "input_tokens": in_tok,
        "output_tokens": out_tok,
        "seconds": round(seconds, 1),
        "cost_usd": round(cost_estimate_usd(in_tok, out_tok, provider), 4),
    }


def normalise_baseline(scores: dict) -> dict:
    """The baseline stores flat per-criterion scores and has no verification
    layer; give it the same shape as the pipeline output so one code path
    evaluates every system."""
    out = {}
    for slug, r in scores.items():
        out[slug] = {
            "total": r["total"],
            "per_criterion": {c["id"]: {"score": r[c["id"]]} for c in RUBRIC},
            "verification_flags": [],
        }
    return out


def failed_checks(review: dict) -> dict:
    return {f["check"]: (not f["passed"]) for f in review["verification_flags"]}


def detection(reviews: dict, planted: dict, honest: list) -> dict:
    """Recall on planted defects and false alarms on honest submissions,
    over the four original checks, restricted to submissions that were run."""
    per, tp, fn, fp, honest_flagged = {}, 0, 0, 0, 0
    honest_evaluated = 0
    for slug, check in planted.items():
        if slug not in reviews:
            continue
        failed = failed_checks(reviews[slug])
        caught = failed.get(check, False)
        per[slug] = {"expected_check": check, "caught": caught}
        tp += int(caught)
        fn += int(not caught)
    for slug in honest:
        if slug not in reviews:
            continue
        honest_evaluated += 1
        fps = [c for c, bad in failed_checks(reviews[slug]).items() if bad and c in ORIGINAL_CHECKS]
        per[slug] = {"expected_check": None, "false_positive_flags": fps}
        fp += len(fps)
        honest_flagged += int(bool(fps))
    return {
        "per_submission": per,
        "planted_evaluated": tp + fn,
        "recall": round(tp / (tp + fn), 3) if (tp + fn) else None,
        "precision": round(tp / (tp + fp), 3) if (tp + fp) else None,
        "honest_evaluated": honest_evaluated,
        "false_alarm_rate": round(honest_flagged / honest_evaluated, 3) if honest_evaluated else None,
    }


def writeup_detection(reviews: dict, flagged: list, honest: list) -> dict:
    """Write-up quality check. Only evaluated for runs that include it."""
    present = [s for s, r in reviews.items() if "writeup_quality" in failed_checks(r)]
    in_run = [s for s, r in reviews.items()
              if any(f["check"] == "writeup_quality" for f in r["verification_flags"])]
    if not in_run:
        return {"evaluated": False,
                "note": "This run pre-dates the write-up check; see eval/WRITEUP_CHECK.md for the offline evaluation."}
    caught = [s for s in flagged if s in reviews and s in present]
    missed = [s for s in flagged if s in reviews and s not in present]
    false_alarms = [s for s in honest if s in reviews and s in present and s not in flagged]
    return {"evaluated": True, "caught": caught, "missed": missed, "false_alarms": false_alarms}


def system_block(name, reviews, human, slugs, call_log, planted, honest, wflag):
    totals = [reviews[s]["total"] for s in slugs]
    h = [human[s]["total"] for s in slugs]
    per_crit = {}
    for c in RUBRIC:
        cid = c["id"]
        per_crit[cid] = round(mae([reviews[s]["per_criterion"][cid]["score"] for s in slugs],
                                  [human[s][cid] for s in slugs]), 2)
    block = {
        "totals": dict(zip(slugs, totals)),
        "mae": round(mae(totals, h), 2),
        "spearman": round(spearman(totals, h), 3) if len(slugs) > 1 else None,
        "per_criterion_mae": per_crit,
        "cost": call_log_summary(call_log),
        "detection": detection(reviews, planted, honest),
        "writeup_check": writeup_detection(reviews, wflag, honest),
        "citations": sum(len(r.get("evidence_citations", []))
                         for s in slugs for r in reviews[s]["per_criterion"].values()),
    }
    block["calls_per_submission"] = round(block["cost"]["num_calls"] / len(slugs), 1)
    return block


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--human", default="data/human_scores.json")
    ap.add_argument("--baseline", default="results/baseline_scores.json")
    ap.add_argument("--agent", default="results/agent_scores.json")
    ap.add_argument("--lean", default="results/lean_scores.json")
    ap.add_argument("--expected", default=None,
                    help="JSON {planted: {slug: check}, honest: [slug], writeup_flagged: [slug]}; "
                         "default is the dev-set expectations built into this file")
    ap.add_argument("--label", default="dev")
    ap.add_argument("--out-json", default="eval/results.json")
    ap.add_argument("--out-md", default="eval/RESULTS.md")
    args = ap.parse_args()

    if args.expected:
        exp = load(args.expected)
        planted, honest, wflag = exp["planted"], exp["honest"], exp.get("writeup_flagged", [])
    else:
        planted, honest, wflag = DEV_PLANTED, DEV_HONEST, DEV_WRITEUP_FLAGGED

    human = load(args.human)["submissions"]
    base = load_optional(args.baseline)
    agent = load_optional(args.agent)
    lean = load_optional(args.lean)

    if not base or not agent:
        missing = [p for p, d in ((args.baseline, base), (args.agent, agent)) if not d]
        md = (f"# PanelAssist vs. baseline vs. human panel ({args.label})\n\n"
              f"**Not run.** Missing results file(s): {', '.join(missing)}.\n\n"
              "Generate them with `python baseline/baseline_scorer.py` and "
              "`python agent/run_agent.py` (they need a working LLM key). No number is "
              "reported for this set until then.\n")
        with open(args.out_md, "w", encoding="utf-8") as f:
            f.write(md)
        with open(args.out_json, "w", encoding="utf-8") as f:
            json.dump({"label": args.label, "status": "not_run", "missing": missing}, f, indent=2)
        print(md)
        return

    base = {"scores": normalise_baseline(base["scores"]), "call_log": base["call_log"]}
    systems = {"baseline": base, "full": agent}
    if lean:
        systems["lean"] = lean
    slugs = sorted(s for s in human if all(s in sysd["scores"] for sysd in systems.values()))
    not_run = sorted(s for s in human if s not in slugs)

    results = {"label": args.label, "status": "ok", "slugs": slugs, "not_run": not_run,
               "human_totals": {s: human[s]["total"] for s in slugs}, "systems": {}}
    for name, data in systems.items():
        results["systems"][name] = system_block(
            name, data["scores"], human, slugs, data["call_log"], planted, honest, wflag)
    results["lean_status"] = "measured" if lean else "not run (no results/lean_scores.json)"

    os.makedirs(os.path.dirname(args.out_json) or ".", exist_ok=True)
    with open(args.out_json, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    md = render_markdown(results)
    with open(args.out_md, "w", encoding="utf-8") as f:
        f.write(md)
    print(md)


def _fmt(v, suffix=""):
    return "n/a" if v is None else f"{v}{suffix}"


def render_markdown(r: dict) -> str:
    s = r["systems"]
    names = list(s)
    label = {"baseline": "Simple baseline", "full": "PanelAssist (full)", "lean": "PanelAssist (lean)"}
    n = len(r["slugs"])
    L = [f"# PanelAssist vs. baseline vs. human panel ({r['label']} set, {n} cases)\n"]

    L.append("## Per-submission totals (out of 100)\n")
    L.append("| Submission | Human panel | " + " | ".join(label[k] for k in names) + " |")
    L.append("|---|---|" + "---|" * len(names))
    for sl in r["slugs"]:
        L.append(f"| {sl} | {r['human_totals'][sl]} | " + " | ".join(str(s[k]["totals"][sl]) for k in names) + " |")
    L.append("")

    L.append("## Summary metrics\n")
    L.append("| Metric | " + " | ".join(label[k] for k in names) + " |")
    L.append("|---|" + "---|" * len(names))
    L.append("| Mean absolute error vs. human total (lower is better) | " + " | ".join(str(s[k]["mae"]) for k in names) + " |")
    L.append("| Spearman rank correlation vs. human (higher is better) | " + " | ".join(_fmt(s[k]["spearman"]) for k in names) + " |")

    def det_cell(k, key):
        d = s[k]["detection"]
        if k == "baseline":
            return "0.0 (no mechanism)" if key == "recall" else "n/a"
        return _fmt(d[key])
    L.append("| Recall on planted defects | " + " | ".join(det_cell(k, "recall") for k in names) + " |")
    L.append("| Precision (flags on honest submissions) | " + " | ".join(det_cell(k, "precision") for k in names) + " |")
    L.append("| False-alarm rate (honest submissions with any original-check flag) | " + " | ".join(
        "n/a" if k == "baseline" else _fmt(s[k]["detection"]["false_alarm_rate"]) for k in names) + " |")
    L.append("| LLM calls per submission | " + " | ".join(str(s[k]["calls_per_submission"]) for k in names) + " |")
    L.append(f"| Total cost, all {n} submissions (est., see common/llm.py rates) | " + " | ".join(f"${s[k]['cost']['cost_usd']}" for k in names) + " |")
    L.append(f"| Wall-clock time, all {n} submissions | " + " | ".join(f"{s[k]['cost']['seconds']}s" for k in names) + " |")
    L.append("")
    if r["lean_status"] != "measured":
        L.append("Lean mode: **not run** - no `results/lean_scores.json` (needs a working LLM key: "
                 "`python agent/run_agent.py --mode lean`). For an offline *estimate* from saved "
                 "outputs, clearly not a measurement, see `eval/LEAN_REPLAY.md`.\n")
    if r["not_run"]:
        L.append(f"Cases with human scores but no results in every system (excluded above): {', '.join(r['not_run'])}.\n")

    cit = s["full"]["citations"]
    L.append(
        "Human time per task is not measured here (that needs a real judging session). As a "
        "proxy: the baseline returns one rationale paragraph with zero structured citations, so a "
        "human has to re-find the evidence before trusting a score; the full pipeline returns "
        f"{cit} cited pieces of evidence across 6 criteria x {n} submissions. This is a citation "
        "count, not a minutes-saved number.\n")

    L.append("## Per-criterion mean absolute error vs. human (lower is better)\n")
    L.append("| Criterion | " + " | ".join(label[k] for k in names) + " |")
    L.append("|---|" + "---|" * len(names))
    for c in RUBRIC:
        L.append(f"| {c['name']} | " + " | ".join(str(s[k]["per_criterion_mae"][c["id"]]) for k in names) + " |")
    L.append("")

    L.append("## Planted-defect detection (the case the baseline structurally cannot handle)\n")
    for k in ("full", "lean"):
        if k not in s:
            continue
        L.append(f"### {label[k]}\n")
        for slug, d in s[k]["detection"]["per_submission"].items():
            if d.get("expected_check"):
                L.append(f"- **{slug}**: expected to trip `{d['expected_check']}` -> {'caught' if d['caught'] else 'MISSED'}")
            else:
                fps = d.get("false_positive_flags", [])
                L.append(f"- **{slug}** (honest): {'no false alarms' if not fps else 'false positive on ' + str(fps)}")
        w = s[k]["writeup_check"]
        if w.get("evaluated"):
            L.append(f"- write-up check: caught {w['caught']}, missed {w['missed']}, false alarms {w['false_alarms']}")
        else:
            L.append(f"- write-up check: not in this run. {w['note']}")
        L.append("")
    return "\n".join(L)


if __name__ == "__main__":
    main()
