"""
Deterministic verification tools -- no LLM calls. This is the "verification
can catch errors before they reach the user" capability from the challenge
PDF, applied to the submission itself rather than to a coding task: does the
reproduction guide actually match the files that exist, and are the
headline claims backed by something a judge could check?
"""
import re


# A reproduction guide that says "create a .env with your key" is not
# referencing a file the submission should ship -- the opposite, per the
# "keep credentials out of the submission" rule. Don't count these as
# missing artifacts.
_CREATE_NOT_SHIP = {".env", ".env.local", ".env.example"}


def check_repro_paths_exist(repro_referenced_paths: list, manifest_files: list) -> dict:
    manifest_set = set(manifest_files)

    def is_present(p: str) -> bool:
        if p in manifest_set:
            return True
        if p.rstrip("/") != p or p.endswith("/"):
            # A directory reference ("data/submissions/") is satisfied if any
            # shipped file lives under it.
            prefix = p.rstrip("/") + "/"
            return any(f.startswith(prefix) for f in manifest_set)
        # Also treat "foo/" written without the slash as a dir if the manifest
        # has children but not the bare path.
        return any(f.startswith(p.rstrip("/") + "/") for f in manifest_set)

    missing = [
        p for p in repro_referenced_paths
        if p and p not in _CREATE_NOT_SHIP and not is_present(p)
    ]
    return {
        "check": "repro_paths_exist",
        "passed": len(missing) == 0,
        "missing_paths": missing,
        "detail": (
            "Every path the reproduction guide references is present in the "
            "submission's file listing."
            if not missing else
            f"The reproduction guide references {len(missing)} path(s) not "
            f"present anywhere in the submission: {missing}. A judge "
            "following this guide from a clean environment would fail here."
        ),
    }


def check_env_var_consistency(repro_referenced_env_vars: list, manifest_files: list) -> dict:
    """Cheap heuristic: if the repro guide asks for an OpenAI-style key but
    every source file in the manifest looks Anthropic-flavored (or vice
    versa), flag a likely mismatch."""
    joined_files = " ".join(manifest_files).lower()
    flags = []
    wants_openai = any("openai" in v.lower() for v in repro_referenced_env_vars)
    wants_anthropic = any("anthropic" in v.lower() for v in repro_referenced_env_vars)
    if wants_openai and not wants_anthropic and "anthropic" in joined_files:
        flags.append("REPRODUCE.md asks for an OPENAI_*_KEY but the codebase looks Anthropic-flavored.")
    return {
        "check": "env_var_consistency",
        "passed": len(flags) == 0,
        "detail": flags[0] if flags else "No env-var/provider mismatch detected.",
    }


def check_claims_have_evidence(claimed_results: list) -> dict:
    unsupported = [c["claim"] for c in claimed_results if not c.get("has_supporting_evidence_file")]
    return {
        "check": "claims_have_evidence",
        "passed": len(unsupported) == 0,
        "unsupported_claims": unsupported,
        "detail": (
            "Every headline claim points to a specific, checkable file."
            if not unsupported else
            f"{len(unsupported)} claim(s) have no specific file/dataset a "
            f"judge could check: {unsupported}. Per ground rule 9 "
            "('connect every claim about your results to the evidence you "
            "submit'), these should not be taken at face value."
        ),
    }


def check_hot_take_is_grounded(hot_take_is_generic: bool, hot_take_text: str) -> dict:
    return {
        "check": "hot_take_grounded",
        "passed": not hot_take_is_generic,
        "detail": (
            "Hot take connects to a specific failure mode observed in this project."
            if not hot_take_is_generic else
            f"Hot take reads as generic AI-hype rather than a lesson tied to "
            f"an observed failure in this specific project: \"{hot_take_text[:160]}...\""
        ),
    }


def run_all_checks(evidence: dict, manifest: dict) -> list:
    manifest_files = manifest.get("files", [])
    return [
        check_repro_paths_exist(evidence.get("repro_referenced_paths", []), manifest_files),
        check_env_var_consistency(evidence.get("repro_referenced_env_vars", []), manifest_files),
        check_claims_have_evidence(evidence.get("claimed_results", [])),
        check_hot_take_is_grounded(evidence.get("hot_take_is_generic", False), evidence.get("hot_take_text", "")),
    ]
