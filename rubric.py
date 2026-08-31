"""
The exact judging rubric published in the micro1 Agentic Workflows Hackathon
challenge PDF (page 5, "How judging works"). Transcribed verbatim so both the
baseline scorer and PanelAssist score against the real criteria the human
panel will use -- not a rubric we invented.

Source: "Agentic Workflows Hackathon" challenge PDF, page 5.
"""

RUBRIC = [
    {
        "id": "problem_user_value",
        "name": "Problem & User Value",
        "points": 15,
        "strong_work": (
            "A strong project solves a meaningful problem for a clearly "
            "defined user."
        ),
        "ask_yourself": (
            "Who experiences the bottleneck and why does solving it matter?"
        ),
    },
    {
        "id": "agent_solution_engineering",
        "name": "Agent Solution & Engineering",
        "points": 30,
        "strong_work": (
            "A strong solution uses agents purposefully and is technically "
            "sound. Better context or tools may improve one project, while "
            "memory, verification, skills or orchestration may improve "
            "another."
        ),
        "ask_yourself": (
            "Which design choices helped the agent solve the problem?"
        ),
    },
    {
        "id": "end_to_end_quality",
        "name": "End to End Quality",
        "points": 20,
        "strong_work": (
            "A strong solution completes a realistic and self contained "
            "execution and produces a final result the user can use, with "
            "the finish of something a person would sign their name to "
            "rather than an obvious AI generated draft."
        ),
        "ask_yourself": (
            "Would the intended user consider this output high quality, or "
            "does it read as clearly AI generated?"
        ),
    },
    {
        "id": "measured_improvement",
        "name": "Measured Improvement",
        "points": 15,
        "strong_work": (
            "A strong report demonstrates gains over a fair baseline and "
            "uses the changelog to connect each iteration with evidence."
        ),
        "ask_yourself": "Which changes truly improved the outcome?",
    },
    {
        "id": "reproducibility",
        "name": "Reproducibility",
        "points": 15,
        "strong_work": (
            "A reproducible project gives another person a clear path to "
            "run the solution and baseline and reach the main result."
        ),
        "ask_yourself": "Could they do it from a clean environment?",
    },
    {
        "id": "hot_take_insights",
        "name": "Hot Take / Insights",
        "points": 5,
        "strong_work": (
            "A strong insight turns an observed failure mode into a "
            "practical lesson for building more reliable agents."
        ),
        "ask_yourself": (
            "What did you learn and how would it change what you build "
            "next?"
        ),
    },
]

TOTAL_POINTS = sum(c["points"] for c in RUBRIC)
assert TOTAL_POINTS == 100

GROUND_RULES_FOR_VERIFICATION = [
    "Every claim about results must connect to evidence in the submission.",
    "The submission should make clear what existed before the competition "
    "and what was added during it.",
    "Consequential/agentic actions should be sandboxed or simulated with "
    "human approval before they happen.",
]


def rubric_as_prompt_block() -> str:
    """Render the rubric as the exact text an LLM scorer should see."""
    lines = ["JUDGING RUBRIC (100 points total, from the official challenge PDF):", ""]
    for c in RUBRIC:
        lines.append(f"- {c['name']} ({c['points']} points)")
        lines.append(f"  What strong work looks like: {c['strong_work']}")
        lines.append(f"  Ask yourself: {c['ask_yourself']}")
        lines.append("")
    return "\n".join(lines)


def criterion_by_id(criterion_id: str) -> dict:
    for c in RUBRIC:
        if c["id"] == criterion_id:
            return c
    raise KeyError(criterion_id)
