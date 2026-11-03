"""Offline tests for the evaluation tooling: spread summary, run_eval's handling
of missing results, and the write-up eval's confusion matrix."""
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from eval.summarize_runs import render, summarise
from eval.writeup_check_eval import evaluate

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

HUMAN = {"a": {"total": 90}, "b": {"total": 50}, "c": {"total": 20}}


def write_run(tmp_path, name, totals):
    p = tmp_path / name
    p.write_text(json.dumps({"scores": {k: {"total": v} for k, v in totals.items()}}), encoding="utf-8")


def test_spread_reports_min_mean_max_across_runs(tmp_path):
    write_run(tmp_path, "full_run1.json", {"a": 90, "b": 50, "c": 20})      # MAE 0
    write_run(tmp_path, "full_run2.json", {"a": 80, "b": 60, "c": 30})      # MAE 10
    write_run(tmp_path, "full_run3.json", {"a": 85, "b": 55, "c": 25})      # MAE 5
    s = summarise(HUMAN, str(tmp_path))
    assert s["full"]["n_runs"] == 3
    assert s["full"]["mae"] == {"min": 0.0, "max": 10.0, "mean": 5.0}
    assert "baseline" not in s and "lean" not in s


def test_spread_does_not_pretend_missing_runs_exist(tmp_path):
    write_run(tmp_path, "baseline_run1.json", {"a": 70, "b": 50, "c": 20})
    md = render("dev", summarise(HUMAN, str(tmp_path)), wanted_runs=3)
    assert "only 1 of 3" in md


def test_spread_says_not_run_when_there_are_no_files(tmp_path):
    md = render("held-out", summarise(HUMAN, str(tmp_path)), wanted_runs=3)
    assert "Not run" in md


def test_run_eval_reports_not_run_instead_of_inventing_numbers(tmp_path):
    out_md = tmp_path / "r.md"
    out_json = tmp_path / "r.json"
    human = tmp_path / "h.json"
    human.write_text(json.dumps({"submissions": HUMAN}), encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, "eval/run_eval.py", "--human", str(human),
         "--baseline", str(tmp_path / "missing_b.json"), "--agent", str(tmp_path / "missing_a.json"),
         "--lean", str(tmp_path / "missing_l.json"), "--label", "held-out",
         "--out-md", str(out_md), "--out-json", str(out_json)],
        cwd=ROOT, capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
    text = out_md.read_text(encoding="utf-8")
    assert "Not run" in text
    assert json.loads(out_json.read_text(encoding="utf-8"))["status"] == "not_run"


def test_writeup_eval_confusion_matrix(tmp_path):
    (tmp_path / "slop").mkdir()
    (tmp_path / "slop" / "README.md").write_text(
        "In today's fast-paced world we leverage the power of cutting-edge agents.\n"
        "Firstly, a. Secondly, b. Thirdly, c.\n", encoding="utf-8")
    (tmp_path / "plain").mkdir()
    (tmp_path / "plain" / "README.md").write_text("Maria reads 140 tickets a day.\n", encoding="utf-8")
    labels = {"slop": {"filler": True}, "plain": {"filler": False}, "gone": {"filler": False}}
    r = evaluate(str(tmp_path), labels)
    assert (r["true_positive"], r["false_negative"], r["false_positive"], r["true_negative"]) == (1, 0, 0, 1)
    assert any(row.get("missing") for row in r["rows"])


def test_heldout_files_are_consistent():
    with open(os.path.join(ROOT, "data", "human_scores_heldout.json"), encoding="utf-8") as f:
        human = json.load(f)
    with open(os.path.join(ROOT, "data", "expected_checks_heldout.json"), encoding="utf-8") as f:
        exp = json.load(f)
    dirs = set(os.listdir(os.path.join(ROOT, "data", "submissions_heldout")))
    assert set(human["submissions"]) == dirs
    assert set(exp["planted"]) | set(exp["honest"]) == dirs
    assert not set(exp["planted"]) & set(exp["honest"])
    assert human["status"] == "drafted_pending_human_review"
    for slug, rec in human["submissions"].items():
        parts = [rec[k] for k in ("problem_user_value", "agent_solution_engineering", "end_to_end_quality",
                                  "measured_improvement", "reproducibility", "hot_take_insights")]
        assert rec["total"] == sum(parts), slug
        assert rec["rationale"], slug
