"""
Render PanelAssist agent runs into a human-readable Markdown trajectory doc.

The hackathon asks for "agent trajectories for every agent used ... easy to
follow from agent instructions to final result". run_agent.py already dumps
the machine-readable version to trajectories/panelassist_runs.json; this
script turns the same data into trajectories/TRAJECTORIES.md, laid out as an
ordered walk-through: the instruction each step was given, what it saw, and
what it produced -- extraction -> deterministic verification -> the six
specialist scoring calls (each with the running memory it inherited) ->
final aggregation.

Reads results/agent_scores.json (the full review objects, including the
evidence ledger and every per-criterion call). Pass --slugs to render only
a representative subset.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rubric import RUBRIC
from agent.panelassist.extract import EXTRACT_SYSTEM
from agent.panelassist.score import SCORER_SYSTEM
from common.loader import load_all_submissions

CRITERION_BY_ID = {c["id"]: c for c in RUBRIC}


def _fmt_ledger(ledger: dict) -> str:
    return "```json\n" + json.dumps(ledger, indent=2) + "\n```"


def _fmt_list(items) -> str:
    items = list(items or [])
    if not items:
        return "_(none)_"
    return "\n".join(f"- {x}" for x in items)


def render_submission(slug: str, review: dict, sub_files: list) -> str:
    L = []
    L.append(f"# Trajectory - `{slug}`\n")
    L.append(
        "PanelAssist processes one submission as a fixed pipeline: **1** evidence "
        "extraction call, **1** deterministic verification pass (no LLM), then "
        "**6** specialist scoring calls (one per rubric criterion) that share the "
        "evidence ledger and a running set of notes. Nothing below is a final "
        "decision -- see the disclaimer at the end.\n"
    )

    L.append("## Input given to the agent\n")
    L.append(f"- **Submission:** `{slug}`")
    L.append(f"- **Files the agent was told exist in the submission:**")
    L.append(_fmt_list(sub_files))
    L.append("")

    # ---- Step 1: extraction ----
    L.append("## Step 1 - Evidence extraction (1 LLM call)\n")
    L.append("**Instruction (system prompt):**\n")
    L.append(f"> {EXTRACT_SYSTEM}\n")
    L.append(
        "**Task:** read README + REPRODUCE.md + file listing + trajectory log and "
        "return one structured *evidence ledger* - target user, bottleneck, which "
        "agent capabilities the submission actually uses, every headline claim "
        "plus whether a specific checkable file backs it, every path/env-var the "
        "reproduction guide references, and whether the hot take is grounded.\n"
    )
    L.append("**Output - the evidence ledger (reused by every step below):**\n")
    L.append(_fmt_ledger(review["evidence_ledger"]))
    L.append("")

    # ---- Step 2: verification ----
    L.append("## Step 2 - Deterministic verification (no LLM)\n")
    L.append(
        "Pure-Python checks run against the ledger from Step 1. These are the "
        "checks a single-prompt baseline has no mechanism to perform.\n"
    )
    L.append("| Check | Result | Detail |")
    L.append("|---|---|---|")
    for f in review["verification_flags"]:
        status = "PASS" if f["passed"] else "**FLAGGED**"
        detail = f["detail"].replace("\n", " ").replace("|", "\\|")
        L.append(f"| `{f['check']}` | {status} | {detail} |")
    L.append("")

    # ---- Steps 3-8: scoring ----
    L.append("## Steps 3-8 - Specialist scoring, one call per criterion\n")
    L.append("**Shared instruction (system prompt) for all six:**\n")
    L.append(f"> {SCORER_SYSTEM}\n")
    L.append(
        "Each call additionally sees: the exact rubric text for its one "
        "criterion, the Step 1 evidence ledger, the Step 2 verification flags, "
        "and the running notes left by criteria scored before it.\n"
    )

    running_notes = []
    per_criterion = review["per_criterion"]
    for i, criterion in enumerate(RUBRIC, start=3):
        cid = criterion["id"]
        r = per_criterion[cid]
        L.append(f"### Step {i} - {criterion['name']} (max {criterion['points']})\n")
        L.append(f"**Instruction for this criterion:**\n")
        L.append(f"- _What strong work looks like:_ {criterion['strong_work']}")
        L.append(f"- _Ask yourself:_ {criterion['ask_yourself']}\n")
        L.append("**Running notes inherited from earlier criteria:**")
        L.append(_fmt_list(running_notes))
        L.append("")
        L.append("**Output:**\n")
        L.append(f"- **Score:** {r['score']} / {criterion['points']}")
        L.append(f"- **Confidence:** {r.get('confidence', 'n/a')}")
        L.append(f"- **Rationale:** {r.get('rationale', '').strip()}")
        L.append(f"- **Evidence cited:**")
        L.append(_fmt_list(r.get("evidence_citations", [])))
        note = (r.get("note_for_other_criteria") or "").strip()
        L.append(f"- **Note passed forward:** {note or '_(none)_'}")
        L.append("")
        if note:
            running_notes.append(f"({criterion['name']}) {note}")

    # ---- Final ----
    L.append("## Final aggregation\n")
    L.append(f"- **Total (sum of the six specialist scores):** {review['total']} / 100")
    L.append(f"- **Needs human attention:** {review['needs_human_attention']}")
    L.append(f"- **Low-confidence criteria:** {_one_line(review['low_confidence_criteria'])}")
    L.append(f"- **Failed verification checks:** {_one_line(review['flagged_checks'])}")
    L.append("")
    L.append("**Accumulated review notes:**")
    L.append(_fmt_list(review["review_notes"]))
    L.append("")
    L.append(f"> {review['disclaimer']}")
    L.append("")
    return "\n".join(L)


def _one_line(items) -> str:
    items = list(items or [])
    return ", ".join(f"`{x}`" for x in items) if items else "_(none)_"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--agent-scores", default="results/agent_scores.json")
    ap.add_argument("--submissions-dir", default="data/submissions")
    ap.add_argument("--out", default="trajectories/TRAJECTORIES.md")
    ap.add_argument(
        "--slugs",
        default="strong_baseline_done_right,fabricated_claims,broken_repro,overengineered_but_honest",
        help="comma-separated submission slugs to render (default: 4 representative cases "
             "-- clean control, an evidence flag, a repro flag, and the ambiguous mid-band case)",
    )
    args = ap.parse_args()

    with open(args.agent_scores) as f:
        scores = json.load(f)["scores"]
    files_by_slug = {
        s["slug"]: s["manifest"].get("files", [])
        for s in load_all_submissions(args.submissions_dir)
    }

    slugs = [s.strip() for s in args.slugs.split(",") if s.strip()]
    parts = [
        "# PanelAssist agent trajectories\n",
        "Representative end-to-end runs, rendered from `results/agent_scores.json` "
        "by `agent/render_trajectories.py`. Each section walks one submission from "
        "the instructions the agent was given to its final aggregated (advisory) "
        "score. The machine-readable form of every run is in "
        "`trajectories/panelassist_runs.json`.\n",
        f"**Rendered submissions:** {', '.join('`'+s+'`' for s in slugs)}\n",
        "---\n",
    ]
    for slug in slugs:
        if slug not in scores:
            raise SystemExit(f"slug '{slug}' not found in {args.agent_scores}")
        parts.append(render_submission(slug, scores[slug], files_by_slug.get(slug, [])))
        parts.append("---\n")

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write("\n".join(parts))
    print(f"Wrote {args.out} ({len(slugs)} submissions)")


if __name__ == "__main__":
    main()
