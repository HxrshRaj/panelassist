"""
PanelAssist end-to-end: extract -> verify -> score each criterion in turn,
carrying a shared evidence ledger and running memory -> aggregate.

Output is advisory only: a per-criterion score with cited evidence, a
verification-flag list, and a confidence level. It never issues a final
accept/reject or prize decision -- ground rule 5 requires a qualified human
reviewer stay in that loop, so this is designed to speed up and standardize
what the human panel looks at, not replace them.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from rubric import RUBRIC
from agent.panelassist.extract import build_evidence_ledger
from agent.panelassist.verify import run_all_checks
from agent.panelassist.score import score_criterion
from agent.panelassist.memory import ReviewMemory


DISCLAIMER = (
    "Advisory pre-screen only. Every score above is a starting "
    "point with cited evidence for a qualified human judge to "
    "confirm, adjust, or override -- this tool does not make a "
    "final accept/reject or prize decision."
)


def review_submission(sub: dict, writeup_check: bool = True) -> dict:
    """writeup_check=False reproduces the original four-check pipeline that
    produced the stored dev-set results in results/agent_scores.json."""
    evidence = build_evidence_ledger(sub)
    verification_flags = run_all_checks(
        evidence, sub["manifest"],
        readme_text=sub.get("readme") if writeup_check else None,
    )

    memory = ReviewMemory()
    per_criterion = {}
    total = 0
    for criterion in RUBRIC:
        result = score_criterion(
            criterion, sub, evidence, verification_flags, memory.snapshot(),
        )
        memory.add(criterion["name"], result.get("note_for_other_criteria", ""))
        per_criterion[criterion["id"]] = result
        total += result["score"]

    low_confidence = [
        c_id for c_id, r in per_criterion.items() if r.get("confidence") == "low"
    ]
    failed_checks = [f for f in verification_flags if not f["passed"]]

    return {
        "slug": sub["slug"],
        "evidence_ledger": evidence,
        "verification_flags": verification_flags,
        "per_criterion": per_criterion,
        "total": total,
        "needs_human_attention": bool(low_confidence or failed_checks),
        "low_confidence_criteria": low_confidence,
        "flagged_checks": [f["check"] for f in failed_checks],
        "review_notes": memory.snapshot(),
        "disclaimer": DISCLAIMER,
    }
