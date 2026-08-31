"""
REMOVED EXPERIMENT - kept in the repo so the claim in the changelog is
reproducible, not asserted.

This is the alternative we tried for the verification step (verify.py): ask
an LLM to do the four checks by reading the evidence ledger, instead of the
deterministic pure-Python version. The hypothesis was that an LLM would be
more flexible (catch a broken repro guide phrased in a way a set membership
test misses) and cost almost nothing at this scale.

`eval/run_removed_experiment.py` runs this head-to-head against verify.py on
the six mock submissions, several times each, and reports what actually
happened. The short version: it costs an extra LLM call per submission, it
is not reproducible run to run, and when it disagrees with the deterministic
check it is the LLM that is wrong. So verify.py stayed deterministic and
this file is not on the pipeline path.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from common.llm import call_json

_VERIFY_SYSTEM = (
    "You are a verification step in a hackathon-judging pipeline. You are "
    "given a structured evidence ledger already extracted from a submission, "
    "plus the submission's file listing. Decide, for each check, whether it "
    "passes. Be strict and literal: a claim is only backed if a specific "
    "named file in the listing would let someone check it; a reproduction "
    "path only exists if it is in the listing; a hot take is only grounded "
    "if it names a failure actually observed in this project."
)


def run_all_checks_llm(evidence: dict, manifest: dict) -> list:
    """Same output shape as verify.run_all_checks, but produced by one LLM
    call instead of four deterministic functions."""
    manifest_files = manifest.get("files", [])
    user = (
        f"EVIDENCE LEDGER:\n{evidence}\n\n"
        f"FILE LISTING:\n{manifest_files}\n\n"
        "Return ONLY a JSON object:\n"
        "{\n"
        '  "repro_paths_exist": {"passed": <bool>, "detail": "<why>"},\n'
        '  "env_var_consistency": {"passed": <bool>, "detail": "<why>"},\n'
        '  "claims_have_evidence": {"passed": <bool>, "detail": "<why>"},\n'
        '  "hot_take_grounded": {"passed": <bool>, "detail": "<why>"}\n'
        "}"
    )
    raw = call_json(_VERIFY_SYSTEM, user, label="verify_llm", max_tokens=900)
    out = []
    for check in ["repro_paths_exist", "env_var_consistency",
                  "claims_have_evidence", "hot_take_grounded"]:
        item = raw.get(check, {}) or {}
        out.append({
            "check": check,
            "passed": bool(item.get("passed", True)),
            "detail": str(item.get("detail", "")),
        })
    return out
