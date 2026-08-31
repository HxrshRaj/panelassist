"""
Per-criterion scoring. Each of the 6 rubric criteria gets its own focused
call, seeing only: the exact rubric text for that criterion, the shared
evidence ledger built once by extract.py, the deterministic verification
flags from verify.py, and the running notes left by criteria scored earlier
in this same review (the "memory carried forward" piece -- see
memory.py). This is the orchestration layer: one specialist call per
criterion instead of one generalist call trying to do all six at once.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from common.llm import call_json
from common.loader import full_text

SCORER_SYSTEM = (
    "You are one specialist on a hackathon judging panel, responsible for "
    "exactly one rubric criterion. Score strictly against the criterion "
    "given, using the evidence ledger and verification flags provided. "
    "Cite specific evidence for your score -- a quote, a file name, or a "
    "verification flag. If a claim in the submission is not backed by "
    "anything in the evidence ledger, say so and score accordingly rather "
    "than giving credit for confident wording."
)


def score_criterion(criterion: dict, sub: dict, evidence: dict,
                     verification_flags: list, running_notes: list) -> dict:
    notes_block = "\n".join(f"- {n}" for n in running_notes) or "(none yet)"
    flags_block = "\n".join(
        f"- [{'OK' if f['passed'] else 'FLAGGED'}] {f['check']}: {f['detail']}"
        for f in verification_flags
    )
    user = (
        f"CRITERION: {criterion['name']} ({criterion['points']} points max)\n"
        f"What strong work looks like: {criterion['strong_work']}\n"
        f"Ask yourself: {criterion['ask_yourself']}\n\n"
        f"EVIDENCE LEDGER (extracted from the submission):\n{evidence}\n\n"
        f"DETERMINISTIC VERIFICATION FLAGS:\n{flags_block}\n\n"
        f"NOTES FROM OTHER CRITERIA ALREADY SCORED THIS REVIEW:\n{notes_block}\n\n"
        f"FULL SUBMISSION TEXT (for direct quotes/citations if needed):\n{full_text(sub)}\n\n"
        "Return ONLY a JSON object:\n"
        "{\n"
        f'  "score": <0-{criterion["points"]}>,\n'
        '  "rationale": "<1-2 sentences>",\n'
        '  "evidence_citations": ["<specific quote, filename, or verification flag you relied on>"],\n'
        '  "confidence": "<low|medium|high>",\n'
        '  "note_for_other_criteria": "<one short sentence worth other scorers knowing, or empty string>"\n'
        "}"
    )
    result = call_json(
        SCORER_SYSTEM, user,
        label=f"score:{sub['slug']}:{criterion['id']}", max_tokens=1200,
    )
    # Normalise the model's output so the orchestrator can always sum scores
    # and read a confidence, even if a call returns a stray type or omits a
    # field.
    result["score"] = _clamp_score(result.get("score"), criterion["points"])
    conf = str(result.get("confidence", "medium")).strip().lower()
    result["confidence"] = conf if conf in ("low", "medium", "high") else "medium"
    if not isinstance(result.get("evidence_citations"), list):
        result["evidence_citations"] = (
            [str(result["evidence_citations"])] if result.get("evidence_citations") else []
        )
    result["note_for_other_criteria"] = str(result.get("note_for_other_criteria", "") or "")
    result["rationale"] = str(result.get("rationale", "") or "")
    result["criterion_id"] = criterion["id"]
    result["max_points"] = criterion["points"]
    return result


def _clamp_score(value, max_points: int) -> int:
    try:
        n = round(float(value))
    except (TypeError, ValueError):
        n = 0
    return max(0, min(int(n), max_points))
