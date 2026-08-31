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
    "exactly ONE rubric criterion. Follow these rules:\n"
    "1. Judge only your criterion. Strength on other dimensions is "
    "irrelevant here -- a brilliant idea earns nothing for End to End "
    "Quality, a polished write-up earns nothing for Problem & User Value, a "
    "strong result earns nothing for Measured Improvement if the iteration "
    "story is missing.\n"
    "2. Start from full marks, then deduct for each specific weakness you "
    "can name. Award more than 85% of the points ONLY if you cannot name a "
    "concrete weakness. Most real submissions have at least one.\n"
    "3. Treat every FLAGGED verification result as a real deduction on the "
    "criterion it bears on, not a footnote.\n"
    "4. Confident wording is not evidence. A claim with no backing file in "
    "the ledger scores as unsupported.\n"
    "5. Cite the specific quote, file name, or verification flag behind your "
    "score, and name the weakness(es) you deducted for."
)

# Rough calibration anchor so the model does not collapse every criterion to
# near-max. Bands are fractions of the criterion's own point ceiling.
SCORE_BANDS = (
    "SCORE BANDS (fraction of this criterion's max):\n"
    "  ~90-100%: exemplary, no weakness you can name.\n"
    "  ~75-89%: strong, one minor named weakness.\n"
    "  ~55-74%: solid but with a real, named gap a judge would raise.\n"
    "  ~35-54%: the criterion is only partly met.\n"
    "  <35%: the criterion is largely unmet or a verification flag hits it directly."
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
        f"{SCORE_BANDS}\n\n"
        f"EVIDENCE LEDGER (extracted from the submission):\n{evidence}\n\n"
        f"DETERMINISTIC VERIFICATION FLAGS:\n{flags_block}\n\n"
        f"NOTES FROM OTHER CRITERIA ALREADY SCORED THIS REVIEW:\n{notes_block}\n\n"
        f"FULL SUBMISSION TEXT (for direct quotes/citations if needed):\n{full_text(sub)}\n\n"
        "Return ONLY a JSON object:\n"
        "{\n"
        f'  "score": <0-{criterion["points"]}>,\n'
        '  "weaknesses_deducted_for": ["<each specific weakness you subtracted points for; [] only if truly none>"],\n'
        '  "rationale": "<1-2 sentences, must reference the weakness list or state why none>",\n'
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
    if not isinstance(result.get("weaknesses_deducted_for"), list):
        result["weaknesses_deducted_for"] = []
    result["criterion_id"] = criterion["id"]
    result["max_points"] = criterion["points"]
    return result


def _clamp_score(value, max_points: int) -> int:
    try:
        n = round(float(value))
    except (TypeError, ValueError):
        n = 0
    return max(0, min(int(n), max_points))
