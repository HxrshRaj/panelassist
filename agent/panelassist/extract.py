"""
Evidence extraction pass -- built ONCE per submission and reused by every
criterion scorer below (this is the "memory carried forward" piece: instead
of re-reading the whole submission from scratch six times, one shared
evidence ledger is built and every criterion scorer sees the same facts and
each other's flags).
"""
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from common.llm import call_json
from common.loader import full_text

EXTRACT_SYSTEM = (
    "You extract structured facts from a hackathon submission. Be literal "
    "and skeptical: only mark a claim as evidence-backed if the submission "
    "actually points to a specific file, dataset, script, or trajectory "
    "step that would let someone verify it. Confident wording is not "
    "evidence."
)


def build_evidence_ledger(sub: dict) -> dict:
    user = (
        "Read this hackathon submission and extract the following as JSON:\n\n"
        f"{full_text(sub)}\n\n"
        "Return ONLY a JSON object:\n"
        "{\n"
        '  "target_user": "<who the README says has the problem, or \'not specified\' if vague>",\n'
        '  "bottleneck": "<the stated bottleneck, or \'not specified\'>",\n'
        '  "agent_capabilities_used": [<subset of: "tool_use","verification","memory","orchestration","human_checkpoint">],\n'
        '  "changelog_entries": [{"stage": "...", "evidence": "...", "decision": "..."}],\n'
        '  "claimed_results": [\n'
        '    {"claim": "<a HEADLINE RESULT claim only -- an accuracy / quality / '
        'improvement / effectiveness metric the submission rests its case on '
        '(e.g. \\"F1 0.52 -> 0.81\\", \\"89% urgency accuracy\\", \\"3/3 defects '
        'caught\\"). Do NOT list incidental operational figures like cost-per-task '
        'or latency-per-task; those are not results claims.>", '
        '"has_supporting_evidence_file": <true/false, true only if a specific file/dataset/script in the files list would let someone check this>, '
        '"supporting_file": "<filename or empty string>"}\n'
        "  ],\n"
        '  "repro_referenced_paths": ["<every file path or filename REPRODUCE.md tells the reader to use>"],\n'
        '  "repro_referenced_env_vars": ["<every env var name REPRODUCE.md tells the reader to set>"],\n'
        '  "hot_take_text": "<the hot take / insight section, verbatim or closely paraphrased>",\n'
        '  "hot_take_is_generic": <true/false -- true if it is generic AI-hype filler not tied to a specific observed failure in THIS project>,\n'
        '  "human_approval_gate_present": <true/false -- true only if the submission explicitly keeps a human in the loop before any consequential/customer-facing action>\n'
        "}"
    )
    return call_json(EXTRACT_SYSTEM, user, label=f"extract:{sub['slug']}", max_tokens=2500)
