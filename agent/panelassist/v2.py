"""
Lean mode: the cheaper pipeline the README recommended after the ablation.

    1. one holistic score, exactly the single-prompt baseline  (1 call)
    2. evidence ledger + deterministic verification as a side-car  (1 call + Python)
    3. re-score ONLY the rubric criteria that a failed check bears on,
       with the specialist prompt that treats the flag as a deduction
       (k calls, k = number of distinct criteria touched, usually 0-3)

Total LLM calls per submission: 2 + k, against 7 for the full pipeline and 1
for the baseline. The full pipeline in orchestrate.py is untouched so the two
stay comparable.

The output has the same shape as orchestrate.review_submission so the eval
scripts can read either. Advisory only: no accept/reject, no ranking.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from rubric import RUBRIC
from baseline.baseline_scorer import score_submission as holistic_score
from agent.panelassist.extract import build_evidence_ledger
from agent.panelassist.memory import ReviewMemory
from agent.panelassist.orchestrate import DISCLAIMER
from agent.panelassist.score import score_criterion, _clamp_score
from agent.panelassist.verify import run_all_checks

# Which rubric criterion each deterministic check is evidence about. A check
# that fails triggers a re-score of exactly these criteria and nothing else.
FLAG_TO_CRITERIA = {
    "repro_paths_exist": ["reproducibility"],
    "env_var_consistency": ["reproducibility"],
    "claims_have_evidence": ["measured_improvement"],
    "hot_take_grounded": ["hot_take_insights"],
}


def criteria_touched_by(verification_flags: list) -> list:
    """Criterion ids bearing on at least one failed check, in rubric order."""
    touched = set()
    for flag in verification_flags:
        if not flag["passed"]:
            touched.update(FLAG_TO_CRITERIA.get(flag["check"], []))
    return [c["id"] for c in RUBRIC if c["id"] in touched]


def review_submission_lean(sub: dict, *, extract=build_evidence_ledger,
                           holistic=holistic_score,
                           rescore=score_criterion) -> dict:
    """The three callables are injectable so tests can run with no network."""
    holistic_result = holistic(sub)
    evidence = extract(sub)
    flags = run_all_checks(evidence, sub["manifest"])
    touched = criteria_touched_by(flags)

    memory = ReviewMemory()
    per_criterion = {}
    total = 0
    for criterion in RUBRIC:
        cid = criterion["id"]
        if cid in touched:
            result = rescore(criterion, sub, evidence, flags, memory.snapshot())
            memory.add(criterion["name"], result.get("note_for_other_criteria", ""))
            result["source"] = "rescored_after_flag"
        else:
            result = {
                "criterion_id": cid,
                "max_points": criterion["points"],
                "score": _clamp_score(holistic_result.get(cid), criterion["points"]),
                "confidence": "medium",
                "rationale": "Holistic single-prompt score; no verification flag bears on this criterion.",
                "evidence_citations": [],
                "weaknesses_deducted_for": [],
                "note_for_other_criteria": "",
                "source": "holistic",
            }
        per_criterion[cid] = result
        total += result["score"]

    failed_checks = [f for f in flags if not f["passed"]]
    low_confidence = [c for c, r in per_criterion.items() if r.get("confidence") == "low"]
    return {
        "slug": sub["slug"],
        "mode": "lean",
        "evidence_ledger": evidence,
        "verification_flags": flags,
        "per_criterion": per_criterion,
        "criteria_rescored": touched,
        "holistic_rationale": str(holistic_result.get("rationale", "")),
        "total": total,
        "needs_human_attention": bool(low_confidence or failed_checks),
        "low_confidence_criteria": low_confidence,
        "flagged_checks": [f["check"] for f in failed_checks],
        "review_notes": memory.snapshot(),
        "disclaimer": DISCLAIMER,
    }
