# Coding-agent use disclosure

Per the challenge rule *"Coding-agent use is required. You must disclose the
tools you used and submit the required trajectories or traces."*

## The coding agent

**Claude Code** (Anthropic's CLI coding agent), model **Claude Sonnet**
(`claude-sonnet-5`), run on Windows 11. One continuous session built this
project end to end. The full session transcript is included, key-redacted,
at [`agent_build_trace/claude_code_session.jsonl.gz`](agent_build_trace/claude_code_session.jsonl.gz)
(2,100+ turns), with a readable walk-through in
[`agent_build_trace/BUILD_LOG.md`](agent_build_trace/BUILD_LOG.md).

This is distinct from the agent trajectories in
[`trajectories/`](trajectories/), which are runs of *PanelAssist itself*
(the submitted solution) reviewing mock hackathon submissions.

## What the coding agent did vs. what the human did

**Coding agent (Claude Code):** wrote every `.py` and `.md` file in the
repo from a natural-language brief; debugged the LLM wrapper (the
`gemini-2.0` -> `gemini-3.6-flash` -> LatentStack-gateway path, timeout and
429 handling, native JSON mode); wrote the ten synthetic mock submissions
and drafted their rubric scores; built and ran the baseline / agent / eval
/ ablation / removed-experiment / dogfood harnesses; iterated the scoring
prompt after the first eval came back worse than the baseline; wrote this
documentation.

**Human (Harsh):** set the problem and scope; supplied the API key when the
Gemini free tier (20 req/day) blocked the run and told the agent which
provider path to take; decided to expand the eval from 6 cases to 10 after
reading the challenge PDF; is the qualified human reviewer who confirms the
ground-truth rubric scores in `data/human_scores.json` (rule 5) and the
final accept/adjust on every number in the README; records the solution
video.

## Other tools / services

- **LatentStack** inference gateway (`https://latentstack.dev/v1`,
  OpenAI-compatible) as the transport to `gemini-3.6-flash`, because the
  direct Google AI Studio free tier caps that model at 20 requests/day and
  a full run is ~180 calls. Same model, no method dependency on the gateway
  - see `REPRODUCE.md`.
- **Google `gemini-3.6-flash`** - the model doing all scoring/extraction in
  both the baseline and the agent.
- Python 3.11 standard library; `python-dotenv`. No other runtime deps on
  the default path.

## Credentials

No API keys are in this submission. `.env` is git-ignored and excluded from
the archive. The session transcript in `agent_build_trace/` has had both
the LatentStack and Gemini keys replaced with `*-REDACTED-*` placeholders
(verified: zero key-shaped strings remain); it is otherwise the unedited
trace.
