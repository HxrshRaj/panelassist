"""
Ablation variants used to produce a real, measured changelog instead of just
a baseline-vs-final number. Each function isolates exactly one change on top
of the previous stage, reusing the same extract.py/verify.py/score.py
building blocks so the only thing that differs between stages is the one
thing each stage claims to add.

Stage 1 (ledger, still one combined call): does structured extraction alone
          help, before any specialization?
Stage 2 (specialist split, no verification): does splitting into one call
          per rubric criterion help beyond just having a ledger?
Stage 3 / Final (specialist split + verification): does the deterministic
          verification layer catch anything specialization alone doesn't?
          -- this is what orchestrate.review_submission() already computes.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from common.llm import call_json
from rubric import RUBRIC, rubric_as_prompt_block

COMBINED_SYSTEM = (
    "You are judging a hackathon submission for the micro1 Agentic "
    "Workflows Hackathon. Score it against the rubric below, using the "
    "structured evidence ledger provided (already extracted from the "
    "submission) rather than raw text."
)


def stage1_ledger_combined(sub: dict, evidence: dict) -> dict:
    """Same shape as the single-prompt baseline, but scoring from the
    extracted evidence ledger instead of the raw submission text -- isolates
    whether structured extraction alone changes anything, before any
    specialization or verification is added."""
    user = (
        f"{rubric_as_prompt_block()}\n\n"
        f"EVIDENCE LEDGER extracted from submission '{sub['slug']}':\n{evidence}\n\n"
        "Return ONLY a JSON object with this exact shape:\n"
        "{\n"
        '  "problem_user_value": <0-15>,\n'
        '  "agent_solution_engineering": <0-30>,\n'
        '  "end_to_end_quality": <0-20>,\n'
        '  "measured_improvement": <0-15>,\n'
        '  "reproducibility": <0-15>,\n'
        '  "hot_take_insights": <0-5>,\n'
        '  "total": <0-100>,\n'
        '  "rationale": "<one paragraph>"\n'
        "}"
    )
    result = call_json(COMBINED_SYSTEM, user, label=f"stage1:{sub['slug']}", max_tokens=1500)
    result["slug"] = sub["slug"]
    return result


def stage2_split_no_verification(sub: dict, evidence: dict, score_criterion_fn) -> dict:
    """Specialist per-criterion calls (with running memory notes, same as
    final), but verification_flags is deliberately passed empty -- isolates
    what specialization alone buys versus the full pipeline with
    verification."""
    from agent.panelassist.memory import ReviewMemory
    memory = ReviewMemory()
    per_criterion = {}
    total = 0
    for criterion in RUBRIC:
        result = score_criterion_fn(criterion, sub, evidence, [], memory.snapshot())
        memory.add(criterion["name"], result.get("note_for_other_criteria", ""))
        per_criterion[criterion["id"]] = result
        total += result["score"]
    return {"slug": sub["slug"], "per_criterion": per_criterion, "total": total}
