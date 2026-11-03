"""
Glue between the web app and the PanelAssist pipeline.

Three honest report sources, always labelled in the response:

  live                 the pipeline ran now against a configured model
  offline_demo         a STORED real run (results/agent_scores.json) replayed;
                       no model is called and nothing here is live
  deterministic_only   no model key: only the checks that need no model ran

The app never presents one source as another. Set PANELASSIST_OFFLINE=1 to
force offline behaviour even when a key exists (used for demos and tests).
"""
import json
import os

import common.llm  # noqa: F401  (loads .env if python-dotenv is present)
from agent.panelassist.v2 import FLAG_TO_CRITERIA
from agent.panelassist.verify import check_writeup_quality
from common.loader import load_submission
from rubric import RUBRIC

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SAMPLE_SETS = {
    "dev": os.path.join(ROOT, "data", "submissions"),
    "held-out": os.path.join(ROOT, "data", "submissions_heldout"),
}
STORED_RUNS = os.path.join(ROOT, "results", "agent_scores.json")
CRITERIA_NAME = {c["id"]: c["name"] for c in RUBRIC}

FLAG_TITLES = {
    "repro_paths_exist": "Reproduction guide references missing files",
    "env_var_consistency": "Provider / env-var mismatch",
    "claims_have_evidence": "Headline claims without a checkable file",
    "hot_take_grounded": "Hot take not tied to an observed failure",
    "writeup_quality": "Write-up reads as padded boilerplate",
}

DISCLAIMER = ("Advisory pre-screen only. Every score is a starting point with cited evidence for a qualified "
              "human judge to confirm, adjust or override. This tool does not accept, reject, rank or award anything.")


def llm_configured() -> bool:
    if os.environ.get("PANELASSIST_OFFLINE") == "1":
        return False
    return bool(os.environ.get("LATENTSTACK_API_KEY") or os.environ.get("GEMINI_API_KEY")
                or os.environ.get("ANTHROPIC_API_KEY"))


# -- samples ------------------------------------------------------------------

def list_samples() -> list:
    stored = _stored_runs()
    out = []
    for set_name, root in SAMPLE_SETS.items():
        if not os.path.isdir(root):
            continue
        for slug in sorted(os.listdir(root)):
            readme = os.path.join(root, slug, "README.md")
            if os.path.exists(readme):
                with open(readme, encoding="utf-8") as f:
                    first = next((ln[2:].strip() for ln in f if ln.startswith("# ")), slug)
                out.append({"slug": slug, "set": set_name, "title": first,
                            "has_stored_run": set_name == "dev" and slug in stored, "synthetic": True})
    return out


def get_sample(slug: str) -> dict | None:
    for root in SAMPLE_SETS.values():
        path = os.path.join(root, slug)
        if os.path.isdir(path) and os.path.basename(path) == slug and ".." not in slug:
            sub = load_submission(path)
            return {"slug": slug, "title": _title(sub), "readme": sub["readme"], "reproduce": sub["reproduce"],
                    "trajectory": sub["trajectory_raw"], "files": "\n".join(sub["manifest"].get("files", [])),
                    "synthetic": True}
    return None


def _title(sub):
    for ln in sub["readme"].splitlines():
        if ln.startswith("# "):
            return ln[2:].strip()
    return sub["slug"]


def _stored_runs() -> dict:
    if not os.path.exists(STORED_RUNS):
        return {}
    with open(STORED_RUNS, encoding="utf-8") as f:
        return json.load(f)["scores"]


# -- report building ----------------------------------------------------------

def _flags_view(flags: list) -> list:
    out = []
    for f in flags:
        out.append({
            "check": f["check"], "passed": f["passed"],
            "title": FLAG_TITLES.get(f["check"], f["check"]),
            "detail": f["detail"],
            "bears_on": [CRITERIA_NAME[c] for c in FLAG_TO_CRITERIA.get(f["check"], []) if c in CRITERIA_NAME],
        })
    return out


def _criteria_view(per_criterion: dict) -> list:
    out = []
    for c in RUBRIC:
        r = per_criterion.get(c["id"], {})
        out.append({
            "id": c["id"], "name": c["name"], "max_points": c["points"],
            "advisory_score": r.get("score"), "confidence": r.get("confidence"),
            "rationale": r.get("rationale", ""),
            "evidence_citations": r.get("evidence_citations", []),
            "weaknesses_deducted_for": r.get("weaknesses_deducted_for", []),
            "source": r.get("source", "specialist"),
        })
    return out


def report_from_review(review: dict, source: str, note: str, title: str, warnings: list) -> dict:
    flags = _flags_view(review["verification_flags"])
    return {
        "source": source, "source_note": note, "title": title,
        "advisory_total": review["total"],
        "criteria": _criteria_view(review["per_criterion"]),
        "flags": flags,
        "needs_human_attention": review["needs_human_attention"],
        "low_confidence_criteria": review.get("low_confidence_criteria", []),
        "input_warnings": warnings,
        "disclaimer": DISCLAIMER,
    }


def demo_report(slug: str, readme_text: str, warnings: list) -> dict | None:
    """Replay a stored real run. Adds the write-up check computed NOW from the
    README, labelled as such, because the stored run pre-dates that check."""
    stored = _stored_runs().get(slug)
    if not stored:
        return None
    rep = report_from_review(
        stored, "offline_demo",
        "This is a stored result from a real run of the full pipeline on this synthetic "
        "submission. No model was called just now.", _title_from(stored, slug), warnings)
    w = check_writeup_quality(readme_text)
    view = _flags_view([w])[0]
    view["computed_now"] = True
    rep["flags"].append(view)
    return rep


def _title_from(stored: dict, slug: str) -> str:
    return stored.get("slug", slug)


def deterministic_report(title: str, readme_text: str, warnings: list) -> dict:
    w = check_writeup_quality(readme_text)
    flags = _flags_view([w])
    return {
        "source": "deterministic_only",
        "source_note": "No model key is configured on this server, so no scores were produced. Only the write-up check, "
                       "which needs no model, ran. Add a key to the server environment to get scored reviews.",
        "title": title, "advisory_total": None,
        "criteria": [{"id": c["id"], "name": c["name"], "max_points": c["points"], "advisory_score": None,
                      "confidence": None, "rationale": "", "evidence_citations": [],
                      "weaknesses_deducted_for": [], "source": "none"} for c in RUBRIC],
        "flags": flags,
        "needs_human_attention": any(not f["passed"] for f in flags),
        "low_confidence_criteria": [], "input_warnings": warnings, "disclaimer": DISCLAIMER,
    }


def run_pipeline(sub: dict, mode: str) -> dict:
    """The only place the web app calls the model pipeline (patched in tests)."""
    if mode == "lean":
        from agent.panelassist.v2 import review_submission_lean
        return review_submission_lean(sub)
    from agent.panelassist.orchestrate import review_submission
    return review_submission(sub)
