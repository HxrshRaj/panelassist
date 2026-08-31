"""Tests for the deterministic verification layer (agent/panelassist/verify.py).

These cover the checks the whole "measured improvement" story rests on:
the three seeded-issue catches, plus the directory-prefix / create-not-ship
logic that dogfooding surfaced. No LLM, no network.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.panelassist.verify import (
    check_claims_have_evidence,
    check_env_var_consistency,
    check_hot_take_is_grounded,
    check_repro_paths_exist,
    run_all_checks,
)


# --- claims_have_evidence -----------------------------------------------------

def test_claims_flag_when_a_headline_claim_has_no_file():
    claims = [
        {"claim": "94.7% accuracy", "has_supporting_evidence_file": False, "supporting_file": ""},
        {"claim": "F1 0.81", "has_supporting_evidence_file": True, "supporting_file": "eval/results.md"},
    ]
    r = check_claims_have_evidence(claims)
    assert r["passed"] is False
    assert "94.7% accuracy" in r["unsupported_claims"]
    assert "F1 0.81" not in r["unsupported_claims"]


def test_claims_pass_when_every_claim_names_a_file():
    claims = [
        {"claim": "F1 0.81", "has_supporting_evidence_file": True, "supporting_file": "eval/results.md"},
        {"claim": "89% recall", "has_supporting_evidence_file": True, "supporting_file": "eval/labels.csv"},
    ]
    assert check_claims_have_evidence(claims)["passed"] is True


def test_claims_pass_when_there_are_no_claims():
    assert check_claims_have_evidence([])["passed"] is True


# --- repro_paths_exist ------------------------------------------------------

MANIFEST = [
    "requirements.txt",
    "src/agent.py",
    "data/submissions/case_a/README.md",
    "eval/score.py",
]


def test_repro_flags_a_path_not_in_the_manifest():
    r = check_repro_paths_exist(["requirements.txt", "config/missing.yaml"], MANIFEST)
    assert r["passed"] is False
    assert r["missing_paths"] == ["config/missing.yaml"]


def test_repro_treats_a_directory_reference_as_present_if_files_live_under_it():
    # "data/submissions/" is not a literal manifest entry, but files are under it
    r = check_repro_paths_exist(["data/submissions/"], MANIFEST)
    assert r["passed"] is True


def test_repro_ignores_create_this_file_instructions_like_dotenv():
    r = check_repro_paths_exist([".env", "requirements.txt"], MANIFEST)
    assert r["passed"] is True
    assert ".env" not in r["missing_paths"]


def test_repro_passes_when_all_paths_present():
    assert check_repro_paths_exist(["requirements.txt", "src/agent.py"], MANIFEST)["passed"] is True


# --- hot_take_grounded ----------------------------------------------------

def test_hot_take_flag_when_generic():
    r = check_hot_take_is_grounded(True, "AI agents are the future of everything.")
    assert r["passed"] is False


def test_hot_take_pass_when_grounded():
    r = check_hot_take_is_grounded(False, "Retrieval quality set the ceiling, not the model.")
    assert r["passed"] is True


# --- env_var_consistency --------------------------------------------------

def test_env_var_mismatch_openai_key_but_anthropic_codebase():
    r = check_env_var_consistency(["OPENAI_API_KEY"], ["agent/anthropic_client.py", "requirements.txt"])
    assert r["passed"] is False


def test_env_var_consistency_no_mismatch():
    r = check_env_var_consistency(["ANTHROPIC_API_KEY"], ["agent/anthropic_client.py"])
    assert r["passed"] is True


# --- run_all_checks -----------------------------------------------------

def test_run_all_checks_returns_the_four_named_checks():
    evidence = {
        "repro_referenced_paths": ["requirements.txt"],
        "repro_referenced_env_vars": ["ANTHROPIC_API_KEY"],
        "claimed_results": [{"claim": "x", "has_supporting_evidence_file": True, "supporting_file": "a"}],
        "hot_take_is_generic": False,
        "hot_take_text": "specific lesson",
    }
    flags = run_all_checks(evidence, {"files": MANIFEST})
    assert {f["check"] for f in flags} == {
        "repro_paths_exist", "env_var_consistency", "claims_have_evidence", "hot_take_grounded",
    }
    assert all(f["passed"] for f in flags)


def test_run_all_checks_catches_a_seeded_issue():
    evidence = {
        "repro_referenced_paths": ["requirements.txt"],
        "repro_referenced_env_vars": [],
        "claimed_results": [{"claim": "94.7%", "has_supporting_evidence_file": False, "supporting_file": ""}],
        "hot_take_is_generic": True,
        "hot_take_text": "AI is the future",
    }
    flags = {f["check"]: f["passed"] for f in run_all_checks(evidence, {"files": MANIFEST})}
    assert flags["claims_have_evidence"] is False
    assert flags["hot_take_grounded"] is False
    assert flags["repro_paths_exist"] is True
