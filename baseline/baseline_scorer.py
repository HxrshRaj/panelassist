"""
Baseline: one direct prompt with basic instructions.

This is the "reasonable basic way to handle the task" the hackathon PDF
asks for -- exactly what a judge would do if they pasted a submission into
a chat window and asked "score this against the rubric." No tools, no
evidence extraction, no verification pass, one LLM call per submission.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.llm import call_json, get_call_log, reset_call_log
from common.loader import load_all_submissions, full_text
from rubric import RUBRIC, rubric_as_prompt_block

SYSTEM = (
    "You are judging a hackathon submission for the micro1 Agentic "
    "Workflows Hackathon. Score it against the rubric below. Read the "
    "submission once and give your best judgment."
)


def score_submission(sub: dict) -> dict:
    user = (
        f"{rubric_as_prompt_block()}\n\n"
        f"SUBMISSION TO SCORE ({sub['slug']}):\n\n{full_text(sub)}\n\n"
        "Return ONLY a JSON object with this exact shape:\n"
        "{\n"
        '  "problem_user_value": <0-15>,\n'
        '  "agent_solution_engineering": <0-30>,\n'
        '  "end_to_end_quality": <0-20>,\n'
        '  "measured_improvement": <0-15>,\n'
        '  "reproducibility": <0-15>,\n'
        '  "hot_take_insights": <0-5>,\n'
        '  "total": <0-100>,\n'
        '  "rationale": "<one paragraph explaining the scores>"\n'
        "}"
    )
    result = call_json(SYSTEM, user, label=f"baseline:{sub['slug']}", max_tokens=1500)
    result["slug"] = sub["slug"]
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--submissions-dir", default="data/submissions")
    ap.add_argument("--out", default="results/baseline_scores.json")
    args = ap.parse_args()

    reset_call_log()
    subs = load_all_submissions(args.submissions_dir)
    results = {}
    for sub in subs:
        print(f"[baseline] scoring {sub['slug']}...", file=sys.stderr)
        results[sub["slug"]] = score_submission(sub)

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w") as f:
        json.dump({"scores": results, "call_log": get_call_log()}, f, indent=2)
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
