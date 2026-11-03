"""Write-up quality check: deterministic, so every behaviour is pinned here."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.panelassist.verify import run_all_checks
from agent.panelassist.writeup import WRITEUP_SIGNALS_TO_FLAG, check_writeup_quality

SLOP = """# Tool

## Introduction
In today's fast-paced landscape, teams need help. The tool leverages the power of
cutting-edge agents to seamlessly bridge the gap.

- **Firstly**, it reads the diff.
- **Secondly**, it finds the docs.
- **Furthermore**, it checks them.
"""

PLAIN = """# Tool

Maria runs a four-person support team and reads about 140 tickets a day.

## Results
| Metric | Before | After |
|---|---|---|
| Accuracy | 61% | 89% |
"""


def test_filler_and_stacked_transitions_together_flag_the_readme():
    r = check_writeup_quality(SLOP)
    assert r["passed"] is False
    assert {s["name"] for s in r["signals"]} >= {"filler_phrases", "stacked_transitions"}
    assert "End to End Quality" in r["detail"]


def test_plain_specific_prose_with_numbers_passes_with_no_signals():
    r = check_writeup_quality(PLAIN)
    assert r["passed"] is True and r["signals"] == []


def test_a_single_signal_is_below_the_flag_threshold():
    one = "We leverage the power of it. It is cutting-edge and seamless. Fast-paced work, truly."
    r = check_writeup_quality(one)
    assert len(r["signals"]) == 1 and r["passed"] is True
    assert WRITEUP_SIGNALS_TO_FLAG == 2
    assert "below the flag threshold" in r["detail"]


def test_results_section_without_a_number_is_a_signal():
    text = ("# Thing\n\n## Results\nThe agent works great on the tickets we tried it on and the "
            "categories made sense and users would find it useful for their daily support work.\n")
    names = {s["name"] for s in check_writeup_quality(text)["signals"]}
    assert "results_without_numbers" in names


def test_numbers_inside_a_results_table_count_as_numbers():
    text = ("## Results\nThe table below shows the measured comparison between the baseline and the agent "
            "on the labelled cases.\n\n| a | b |\n|---|---|\n| 0.5 | 0.8 |\n")
    # the table row is stripped from prose, but the *section* still contains digits
    assert "results_without_numbers" not in {s["name"] for s in check_writeup_quality(text)["signals"]}


def test_code_fences_are_not_prose():
    text = "```\nfast-paced seamless cutting-edge transformative\nFirstly, Secondly, Thirdly\n```\nPlain text."
    assert check_writeup_quality(text)["signals"] == []


def test_empty_or_missing_readme_passes_without_crashing():
    assert check_writeup_quality("")["passed"] is True
    assert check_writeup_quality(None)["passed"] is True
    assert check_writeup_quality("   \n ")["passed"] is True


def test_check_is_deterministic():
    assert check_writeup_quality(SLOP) == check_writeup_quality(SLOP)


def test_run_all_checks_adds_writeup_only_when_readme_text_is_given():
    evidence = {"repro_referenced_paths": [], "repro_referenced_env_vars": [],
                "claimed_results": [], "hot_take_is_generic": False, "hot_take_text": ""}
    without = run_all_checks(evidence, {"files": []})
    with_text = run_all_checks(evidence, {"files": []}, readme_text=SLOP)
    assert [f["check"] for f in without] == ["repro_paths_exist", "env_var_consistency",
                                            "claims_have_evidence", "hot_take_grounded"]
    assert with_text[-1]["check"] == "writeup_quality" and with_text[-1]["passed"] is False
    assert len(with_text) == 5
