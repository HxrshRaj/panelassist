"""Score aggregation and per-criterion normalisation, with the LLM mocked.
No network, no key."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.panelassist import orchestrate, score
from rubric import RUBRIC, TOTAL_POINTS

SUB = {"slug": "demo", "readme": "# demo\nMaria reads 140 tickets a day.", "reproduce": "",
       "manifest": {"files": ["requirements.txt"]}, "trajectory": {}, "trajectory_raw": ""}

LEDGER = {"repro_referenced_paths": ["requirements.txt"], "repro_referenced_env_vars": [],
          "claimed_results": [], "hot_take_is_generic": False, "hot_take_text": ""}


def fake_scorer(per_criterion):
    def _s(criterion, sub, evidence, flags, notes):
        spec = per_criterion[criterion["id"]]
        spec = spec if isinstance(spec, dict) else {"score": spec}
        return {"criterion_id": criterion["id"], "max_points": criterion["points"],
                "confidence": "high", "rationale": "r", "evidence_citations": ["c"],
                "note_for_other_criteria": "", **spec}
    return _s


def run_full(monkeypatch, scores, ledger=LEDGER, **kw):
    monkeypatch.setattr(orchestrate, "build_evidence_ledger", lambda sub: ledger)
    monkeypatch.setattr(orchestrate, "score_criterion", fake_scorer(scores))
    return orchestrate.review_submission(SUB, **kw)


def test_total_is_the_sum_of_the_six_criterion_scores(monkeypatch):
    scores = {c["id"]: c["points"] // 2 for c in RUBRIC}
    r = run_full(monkeypatch, scores)
    assert r["total"] == sum(scores.values())
    assert list(r["per_criterion"]) == [c["id"] for c in RUBRIC]


def test_full_marks_total_the_published_maximum(monkeypatch):
    r = run_full(monkeypatch, {c["id"]: c["points"] for c in RUBRIC})
    assert r["total"] == TOTAL_POINTS == 100


def test_a_low_confidence_criterion_needs_human_attention(monkeypatch):
    scores = {c["id"]: c["points"] for c in RUBRIC}
    scores["reproducibility"] = {"score": 9, "confidence": "low"}
    r = run_full(monkeypatch, scores)
    assert r["needs_human_attention"] is True
    assert r["low_confidence_criteria"] == ["reproducibility"]


def test_a_failed_check_needs_human_attention_even_if_all_scores_are_confident(monkeypatch):
    ledger = dict(LEDGER, claimed_results=[{"claim": "94%", "has_supporting_evidence_file": False,
                                             "supporting_file": ""}])
    r = run_full(monkeypatch, {c["id"]: c["points"] for c in RUBRIC}, ledger=ledger)
    assert r["needs_human_attention"] is True
    assert "claims_have_evidence" in r["flagged_checks"]


def test_clean_confident_submission_does_not_need_attention(monkeypatch):
    r = run_full(monkeypatch, {c["id"]: c["points"] for c in RUBRIC}, writeup_check=False)
    assert r["needs_human_attention"] is False and r["flagged_checks"] == []


def test_writeup_check_can_be_switched_off_to_reproduce_the_stored_pipeline(monkeypatch):
    scores = {c["id"]: 1 for c in RUBRIC}
    on = run_full(monkeypatch, scores, writeup_check=True)
    off = run_full(monkeypatch, scores, writeup_check=False)
    assert "writeup_quality" in [f["check"] for f in on["verification_flags"]]
    assert "writeup_quality" not in [f["check"] for f in off["verification_flags"]]


def test_output_is_advisory_and_carries_no_decision_fields(monkeypatch):
    r = run_full(monkeypatch, {c["id"]: 1 for c in RUBRIC})
    assert "advisory" in r["disclaimer"].lower() and "final accept/reject" in r["disclaimer"]
    assert not {"decision", "accepted", "rejected", "rank", "winner", "prize"} & {k.lower() for k in r}


# --- score_criterion normalisation ---------------------------------------

def call_with(monkeypatch, payload):
    monkeypatch.setattr(score, "call_json", lambda *a, **k: payload)
    crit = next(c for c in RUBRIC if c["id"] == "measured_improvement")
    return score.score_criterion(crit, SUB, LEDGER, [], [])


def test_scores_are_clamped_to_the_criterion_maximum(monkeypatch):
    assert call_with(monkeypatch, {"score": 99})["score"] == 15
    assert call_with(monkeypatch, {"score": -3})["score"] == 0


def test_non_numeric_score_becomes_zero_instead_of_crashing(monkeypatch):
    assert call_with(monkeypatch, {"score": "twelve"})["score"] == 0
    assert call_with(monkeypatch, {"score": None})["score"] == 0


def test_numeric_string_and_float_scores_are_accepted(monkeypatch):
    assert call_with(monkeypatch, {"score": "11"})["score"] == 11
    assert call_with(monkeypatch, {"score": 10.6})["score"] == 11


def test_missing_or_odd_fields_get_safe_defaults(monkeypatch):
    r = call_with(monkeypatch, {"score": 5, "confidence": "WEIRD", "evidence_citations": "one cite"})
    assert r["confidence"] == "medium"
    assert r["evidence_citations"] == ["one cite"]
    assert r["weaknesses_deducted_for"] == [] and r["note_for_other_criteria"] == ""
    assert r["criterion_id"] == "measured_improvement" and r["max_points"] == 15


def test_flagged_checks_appear_in_the_scoring_prompt(monkeypatch):
    seen = {}

    def fake_call_json(system, user, **kw):
        seen["user"] = user
        return {"score": 3}
    monkeypatch.setattr(score, "call_json", fake_call_json)
    crit = next(c for c in RUBRIC if c["id"] == "end_to_end_quality")
    flags = [{"check": "writeup_quality", "passed": False, "detail": "padded prose"}]
    score.score_criterion(crit, SUB, LEDGER, flags, [])
    assert "[FLAGGED] writeup_quality" in seen["user"]
