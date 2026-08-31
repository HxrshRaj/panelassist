# Build log - how the coding agent built PanelAssist

A readable walk-through of the Claude Code session that produced this
project. The raw, key-redacted transcript is
[`claude_code_session.jsonl.gz`](claude_code_session.jsonl.gz) - `gunzip` it
to get JSONL, one message per line (`type` is `user` / `assistant`, tool
calls and their results inline). This log is the "easy to follow from the
agent instructions through to the final result" view the challenge asks
for.

## 0. Starting point

The human handed the agent a brief (`HANDOFF_PROMPT.md`, kept in the repo):
build an evidence-grounded pre-screener for hackathon judging, with a
single-prompt baseline and a measured improvement, and *"don't fabricate a
single number."* A partial codebase existed (`rubric.py`, a first-draft
`common/llm.py`, six mock submissions); the LLM wrapper did not work.

## 1. Fix the model integration (the first real problem)

The agent's instruction was to get a real traceback before guessing. It ran
the baseline, read the error, and probed the API directly:

- The failure was **`TimeoutError`**, not the JSON-parse error the brief
  predicted. `gemini-3.6-flash` is a reasoning model; real scoring calls
  take 40-63s and the wrapper's 60s timeout killed them mid-response.
- Direct probing also confirmed thinking tokens count against
  `maxOutputTokens` (the older truncation symptom) and that thinking cannot
  be disabled on this model (`thinkingBudget: 0` -> HTTP 400).

Fixes: native JSON mode (`responseMimeType: application/json`), a separate
thinking-token budget on top of the caller's answer budget, 180s timeout,
retry/backoff. **Retries and this debugging loop are visible in the
transcript around the "get a clean traceback" instruction.**

## 2. The quota wall, and a human checkpoint

The full run needs ~180 LLM calls; the direct Gemini free tier is **20
requests/day**. The run hit `RESOURCE_EXHAUSTED` mid-way. The agent
**stopped and asked the human** rather than working around it. The human
supplied a LatentStack gateway key (`ls-...`, an OpenAI-compatible proxy to
the same `gemini-3.6-flash`). The agent added a third provider to
`common/llm.py` (`_call_latentstack`, plain urllib, JSON mode, 429
handling), picked from `.env` alone. **This is the "retries or human
checkpoints" beat - it's a genuine one.**

## 3. Baseline and agent runs

Baseline (`baseline_scorer.py`, one prompt) and the agent
(`run_agent.py`: extract -> verify -> 6 specialist score calls ->
aggregate) both run against the same mock submissions. First results on the
original **6** cases: baseline MAE 5.33, agent 6.33 - the agent *lost*. The
agent reported this honestly and did not tune numbers to hide it.

## 4. Expand the eval to 10 cases (human decision)

Reading the challenge PDF, the human decided to add the four mid-band cases
the PDF's "ten or more cases" line calls for
(`good_project_bad_writeup`, `real_gains_no_changelog`,
`overengineered_but_honest`, `scope_mismatch`) - each isolating one rubric
weakness. The agent wrote the four submissions and drafted their scores for
the human to confirm.

On 10 cases the story changed: the baseline over-scores the mid-band cases
badly (a holistic pass can't dock one criterion in isolation), MAE 8.6-11.2
and **unstable run-to-run**. The first 10-case agent run was *worse* (MAE
11.4) - the specialist calls were even more generous.

## 5. The scoring-prompt iteration (the change that mattered)

The agent rewrote `score.py`'s prompt: judge one criterion in isolation,
start from full marks and deduct for a *named* weakness, and **treat every
verification flag as a real subtraction**. Re-run: agent MAE 7.8 vs
baseline 11.2. The ablation (`run_ablation.py`) then showed *why* - the six
scoring calls alone score no better than one prompt; the jump comes
entirely from the deterministic flags being wired into the scorer as forced
deductions.

## 6. Removed experiment, dogfooding, packaging

- LLM-based verification (`verify_llm.py`) was built, measured head-to-head
  against the deterministic checks on all 10 cases (matched on accuracy),
  and **removed** for cost + reproducibility. Kept in the repo.
- PanelAssist was run on its own submission package (`dogfood/`). It caught
  two real guide/manifest mismatches; fixed by generating the self-manifest
  from `git ls-files`.
- Clean-venv reproduction check, key-leak checks, zip packaging, ~13
  commits with messages that record each result as it landed.

## What to look for in the raw transcript

| Around | What happens |
|---|---|
| early | "get a clean traceback first" -> API probing -> the timeout finding |
| mid | `RESOURCE_EXHAUSTED` -> the agent asks the human -> LatentStack wired in |
| mid | first 6-case eval: agent loses on MAE, reported straight |
| later | human: "add 4 more to reach 10" -> submissions written, scored |
| later | `score.py` prompt rewrite -> agent MAE 11.4 -> 7.8 |
| late | ablation run -> "the scoring calls weren't the win" -> hot take rewritten |
| late | dogfood catches its own manifest gaps -> git ls-files fix |
