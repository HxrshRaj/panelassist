"""Lean mode, tested offline: the three LLM-backed steps are injected as fakes,
so no network, key or cost is involved."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.panelassist.v2 import FLAG_TO_CRITERIA, criteria_touched_by, review_submission_lean
from rubric import RUBRIC

SUB = {"slug": "demo", "readme": "# demo", "reproduce": "", "manifest": {"files": ["requirements.txt"]},
       "trajectory": {}, "trajectory_raw": ""}

HOLISTIC = {"problem_user_value": 13, "agent_solution_engineering": 25, "end_to_end_quality": 16,
            "measured_improvement": 12, "reproducibility": 13, "hot_take_insights": 4,
            "total": 999, "rationale": "fine overall"}  # total is deliberately wrong


def fake_extract(evidence):
    return lambda sub: evidence


def fake_rescore(calls):
    def _rescore(criterion, sub, evidence, flags, notes):
        calls.append(criterion["id"])
        return {"criterion_id": criterion["id"], "max_points": criterion["points"], "score": 1,
                "confidence": "high", "rationale": "docked", "evidence_citations": ["flag"],
                "note_for_other_criteria": ""}
    return _rescore


CLEAN = {"repro_referenced_paths": ["requirements.txt"], "repro_referenced_env_vars": [],
         "claimed_results": [{"claim": "x", "has_supporting_evidence_file": True, "supporting_file": "a"}],
         "hot_take_is_generic": False, "hot_take_text": "specific"}


def test_clean_submission_makes_no_rescore_calls():
    calls = []
    r = review_submission_lean(SUB, extract=fake_extract(CLEAN), holistic=lambda s: dict(HOLISTIC),
                               rescore=fake_rescore(calls))
    assert calls == []
    assert r["criteria_rescored"] == []
    assert not r["flagged_checks"]
    # total is recomputed from the clamped sub-scores, not taken from the model's own total
    assert r["total"] == 13 + 25 + 16 + 12 + 13 + 4
    assert all(c["source"] == "holistic" for c in r["per_criterion"].values())


def test_a_failed_check_rescores_only_the_criterion_it_bears_on():
    evidence = dict(CLEAN, claimed_results=[{"claim": "94%", "has_supporting_evidence_file": False,
                                              "supporting_file": ""}])
    calls = []
    r = review_submission_lean(SUB, extract=fake_extract(evidence), holistic=lambda s: dict(HOLISTIC),
                               rescore=fake_rescore(calls))
    assert calls == ["measured_improvement"]
    assert r["per_criterion"]["measured_improvement"]["source"] == "rescored_after_flag"
    assert r["per_criterion"]["measured_improvement"]["score"] == 1
    assert r["per_criterion"]["reproducibility"]["source"] == "holistic"
    assert r["needs_human_attention"] is True
    assert r["flagged_checks"] == ["claims_have_evidence"]


def test_holistic_scores_are_clamped_to_each_criterion_maximum():
    over = dict(HOLISTIC, problem_user_value=99, hot_take_insights=-4)
    r = review_submission_lean(SUB, extract=fake_extract(CLEAN), holistic=lambda s: over,
                               rescore=fake_rescore([]))
    assert r["per_criterion"]["problem_user_value"]["score"] == 15
    assert r["per_criterion"]["hot_take_insights"]["score"] == 0


def test_two_checks_on_one_criterion_trigger_a_single_rescore():
    evidence = dict(CLEAN, repro_referenced_paths=["requirements.txt", "config/missing.yaml"],
                    repro_referenced_env_vars=["OPENAI_API_KEY"])
    manifest = {"files": ["requirements.txt", "agent/anthropic_client.py"]}
    sub = dict(SUB, manifest=manifest)
    calls = []
    r = review_submission_lean(sub, extract=fake_extract(evidence), holistic=lambda s: dict(HOLISTIC),
                               rescore=fake_rescore(calls))
    assert set(r["flagged_checks"]) == {"repro_paths_exist", "env_var_consistency"}
    assert calls == ["reproducibility"]


def test_every_flag_maps_to_a_real_rubric_criterion():
    ids = {c["id"] for c in RUBRIC}
    for check, crits in FLAG_TO_CRITERIA.items():
        assert crits and set(crits) <= ids, check


def test_criteria_touched_by_returns_rubric_order_and_ignores_passes():
    flags = [{"check": "hot_take_grounded", "passed": False},
             {"check": "claims_have_evidence", "passed": False},
             {"check": "repro_paths_exist", "passed": True}]
    assert criteria_touched_by(flags) == ["measured_improvement", "hot_take_insights"]


def test_output_never_contains_a_decision_field():
    r = review_submission_lean(SUB, extract=fake_extract(CLEAN), holistic=lambda s: dict(HOLISTIC),
                               rescore=fake_rescore([]))
    assert "advisory" in r["disclaimer"].lower()
    for forbidden in ("accept", "reject", "decision", "rank", "prize"):
        assert forbidden not in {k.lower() for k in r}
