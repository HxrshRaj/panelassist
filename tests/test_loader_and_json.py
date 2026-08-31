"""Tests for common/loader.py (submission loading) and common/llm.py's
_extract_json_object (the JSON parser that tolerates fenced / prose-wrapped
model output). No LLM, no network."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.loader import full_text, load_all_submissions, load_submission
from common.llm import _extract_json_object

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SUBS_DIR = os.path.join(ROOT, "data", "submissions")


def test_load_all_submissions_finds_the_ten_mock_cases():
    subs = load_all_submissions(SUBS_DIR)
    slugs = {s["slug"] for s in subs}
    assert len(subs) == 10
    assert {"strong_baseline_done_right", "weak_single_prompt", "fabricated_claims",
            "broken_repro", "thin_hot_take", "cosmetic_orchestration",
            "good_project_bad_writeup", "real_gains_no_changelog",
            "overengineered_but_honest", "scope_mismatch"} <= slugs


def test_load_submission_shape():
    sub = load_submission(os.path.join(SUBS_DIR, "strong_baseline_done_right"))
    assert sub["slug"] == "strong_baseline_done_right"
    for key in ("readme", "reproduce", "manifest", "trajectory"):
        assert key in sub
    assert isinstance(sub["manifest"].get("files"), list) and sub["manifest"]["files"]


def test_full_text_includes_every_section_marker():
    sub = load_submission(os.path.join(SUBS_DIR, "broken_repro"))
    text = full_text(sub)
    for marker in ("=== README.md ===", "=== REPRODUCE.md ===",
                   "Files present in the submission", "Agent trajectory log"):
        assert marker in text


def test_extract_json_object_bare():
    assert _extract_json_object('{"score": 12, "ok": true}') == {"score": 12, "ok": True}


def test_extract_json_object_fenced():
    raw = 'Sure!\n```json\n{"score": 7}\n```\nDone.'
    assert _extract_json_object(raw) == {"score": 7}


def test_extract_json_object_prose_wrapped():
    raw = 'Here is the result: {"a": 1, "b": [2, 3]} -- hope that helps'
    assert _extract_json_object(raw) == {"a": 1, "b": [2, 3]}


def test_extract_json_object_returns_none_on_garbage():
    assert _extract_json_object("no json here at all") is None
    assert _extract_json_object("") is None
