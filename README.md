# PanelAssist

**An evidence-grounded pre-screener for hackathon judging. It reads a
submission, extracts a checkable evidence ledger, runs deterministic
verification against it, scores each rubric criterion with its own
specialist call, and hands a human judge an advisory report with cited
evidence per score. It never issues a final decision.**

Built solo for the **micro1 Agentic Workflows Hackathon** (Aug 28-31,
2026).

---

## The problem and the user

The user is a **micro1 hackathon judge**. This challenge alone drew 8,300+
registrations, all to be scored against a **published 100-point rubric**
with six criteria (Problem & User Value 15, Agent Solution & Engineering
30, End to End Quality 20, Measured Improvement 15, Reproducibility 15, Hot
Take/Insights 5). The rubric is transcribed verbatim in
[`rubric.py`](rubric.py).

The bottleneck is not "reading takes time" - it is that a tired judge
under time pressure, scoring their fortieth submission of the day, is
exactly who a **confidently-worded but evidence-free submission** slips
past. The rubric itself says "connect every claim about your results to
the evidence you submit" (ground rule 9), but nothing forces the judge to
check each claim against a specific file before awarding points for it. The
same judge also has to notice when a reproduction guide references files
that were never included, and when a "hot take" is generic AI-hype rather
than a real lesson. Doing that consistently across hundreds of submissions,
by hand, is where the process breaks.

PanelAssist does the mechanical part of that check once per submission,
cites what it found, flags what a human should look at, and stops there.

## What existed before the hackathon vs. what was built during it

**Pre-existing, used as-is:** Python 3.11 standard library; the `anthropic`
SDK; the Gemini / OpenAI-compatible REST APIs; `python-dotenv`; the
**LatentStack** inference gateway (used only as the transport to reach
`gemini-3.6-flash` without the AI Studio free tier's 20-requests/day cap -
see REPRODUCE.md). The rubric text is micro1's, not ours.

**Built during the hackathon (all of it):** every `.py` and `.md` file in
this repo. The single-prompt baseline; the four-stage agent (extract →
verify → score → aggregate); the shared evidence ledger and the
cross-criterion running memory; the deterministic verification checks; the
ten synthetic mock submissions and their hand-scored ground truth; the
eval, ablation, and trajectory-rendering harnesses. No code was carried in
from a prior project.

## The baseline

[`baseline/baseline_scorer.py`](baseline/baseline_scorer.py): one LLM call.
The whole submission plus the full rubric text goes in; a JSON object with
six sub-scores, a total, and one rationale paragraph comes out. No tools,
no evidence extraction, no verification. This is exactly what a time-pressed
judge does when they paste a submission into a chat window and ask "score
this against the rubric" - a fair, honest baseline, not a strawman.

## How PanelAssist works

One submission flows through a fixed pipeline:

1. **Extract** ([`extract.py`](agent/panelassist/extract.py)) - one LLM
   call builds a structured **evidence ledger**: target user, stated
   bottleneck, which agent capabilities the submission actually
   demonstrates, every headline claim *and whether a specific checkable
   file backs it*, every path and env var the reproduction guide tells you
   to use, and whether the hot take is tied to an observed failure. Built
   once, reused by every step below - this is the "context carried
   forward" piece.

2. **Verify** ([`verify.py`](agent/panelassist/verify.py)) - pure Python,
   **no LLM**. Do the reproduction guide's referenced paths exist in the
   submission's file listing? Does every headline claim point to a
   checkable file? Is the hot take grounded? Is there an env-var/provider
   mismatch? Each check returns a pass/flag plus a human-readable reason.
   A single prompt has no mechanism to do this; a deterministic check is
   also *reproducible* and *auditable* in a way a rationale sentence is
   not.

3. **Score** ([`score.py`](agent/panelassist/score.py)) - **six specialist
   calls, one per rubric criterion**, in rubric order. Each sees its own
   criterion's exact text, the shared evidence ledger, **all** the
   verification flags, and the **running notes left by criteria already
   scored earlier in this review** ([`memory.py`](agent/panelassist/memory.py))
   - so when Problem & User Value notes that a headline metric is
   unbacked, the later Measured Improvement call sees that note and does
   not credit the same number twice. Each call returns a score, a 1-2
   sentence rationale, **explicit evidence citations**, and a confidence
   level.

4. **Aggregate** ([`orchestrate.py`](agent/panelassist/orchestrate.py)) -
   sum the six scores, collect low-confidence criteria and failed checks
   into `needs_human_attention`, attach a disclaimer, and return. **No
   accept/reject, no ranking, no prize decision** - that stays with the
   human panel (ground rule 5).

## Running it

See [REPRODUCE.md](REPRODUCE.md) for the clean-environment walkthrough. In
short: `pip install -r requirements.txt`, put a key in `.env`, then

```bash
python baseline/baseline_scorer.py        # -> results/baseline_scores.json
python agent/run_agent.py                 # -> results/agent_scores.json, trajectories/panelassist_runs.json
python eval/run_eval.py                   # -> eval/RESULTS.md
python eval/run_ablation.py               # -> eval/ABLATIONS.md
python eval/run_removed_experiment.py     # -> eval/REMOVED_EXPERIMENT.md
python agent/render_trajectories.py       # -> trajectories/TRAJECTORIES.md
```

## Evaluation setup

**Ten fully synthetic** mock submissions ([`data/submissions/`](data/submissions/)),
written for this project to span the failure space a real judge faces.
Human totals span 25-92 with the mid-band deliberately populated:

| Slug | Human total | What it is | Weakness (if any) |
|---|---|---|---|
| `strong_baseline_done_right` | 92 | genuinely strong entry | none (control) |
| `overengineered_but_honest` | 84 | disciplined 4-agent pipeline, exemplary changelog | proportionality of the architecture is a judgement call (**the challenging case**) |
| `thin_hot_take` | 82 | strong everywhere except the insight | hot take is generic boilerplate |
| `good_project_bad_writeup` | 78 | solid agent + real eval + real gains | README reads as an obvious unedited AI draft |
| `real_gains_no_changelog` | 78 | strong solution, real fair-baseline comparison | no improvement changelog at all |
| `scope_mismatch` | 76 | well-built agent, near-perfect reproduction | problem & user value is thin ("my Downloads folder") |
| `broken_repro` | 63 | good design, unrunnable | REPRODUCE.md references files not in the submission |
| `cosmetic_orchestration` | 38 | 6 "agents", ~1 pt gain at 5.8x cost | orchestration adds cost/latency, no real gain |
| `fabricated_claims` | 36 | confident tone, no evidence | headline numbers with no eval data or script |
| `weak_single_prompt` | 25 | one prompt, no evaluation | no baseline, no data, vague user |

Only three carry a defect the deterministic verification layer targets
(`fabricated_claims` -> unbacked claims, `broken_repro` -> missing repro
paths, `thin_hot_take` -> generic hot take); the other seven should trip
nothing. Ground truth: [`data/human_scores.json`](data/human_scores.json),
scored by the author as the qualified human reviewer, never shown to either
scorer. No real people's data appears anywhere in the set (ground rule
6-7).

## Results

Numbers below are copied from `eval/RESULTS.md` and `eval/ABLATIONS.md`,
both generated by scripts in `eval/`. Run on `gemini-3.6-flash` via the
LatentStack gateway, `temperature=0`, over the **10** mock submissions.

| Metric | Baseline (1 prompt) | PanelAssist | Who wins |
|---|---|---|---|
| **Total-score MAE** vs. human (lower better) | 11.2 | **7.8** | PanelAssist (-3.4) |
| **Spearman** rank corr. vs. human (higher better) | 0.857 | **0.875** | PanelAssist |
| Seeded-issue **recall** (3 planted rubric violations) | 0.00 - no mechanism | **1.00** (3/3) | PanelAssist |
| Seeded-issue **precision** (flags on the 5 honest submissions) | n/a | **1.00** (0 false alarms) | PanelAssist |
| LLM calls per submission | **1** | 7 | Baseline |
| Cost / wall-clock, all 10 submissions | **$0.006 / 112s** | $0.057 / 932s | Baseline |
| Structured evidence citations produced | 0 | 148 | PanelAssist |

**What this says.** PanelAssist agrees with the human panel better than the
single-prompt baseline, for ~8x the cost. The gap comes almost entirely
from the six mid-band submissions - the ones with a single *localized*
rubric flaw (an AI-slop write-up, a missing changelog, a thin problem
statement). A holistic single pass reads those as strong-overall and scores
them near the top: baseline gave `good_project_bad_writeup` **98** where the
panel gave 78, `overengineered_but_honest` 98 vs 84, `real_gains_no_changelog`
96 vs 78, `scope_mismatch` 93 vs 76. It cannot dock one criterion without
being told to look at that criterion alone. PanelAssist's per-criterion
specialists, told to judge one criterion in isolation and deduct from full
marks for a *named* weakness, land much closer (94, 92, 88, 88) - not
perfect, still a little high on `good_project_bad_writeup`, but no longer
80th-percentile-for-everything.

An earlier version of this eval used only 6 submissions with large score
gaps (25 / 36 / 38 / 63 / 82 / 92). On that set the baseline actually won
on MAE - ranking six well-separated cases is easy for a holistic pass. The
challenge PDF asks for ten or more cases; adding the mid-band is what
exposed the difference, and it is also where the baseline turned out to be
**unstable**: MAE 8.6 on one 10-case run, 11.2 on the next, same inputs.

**Seeded-issue detection.** All three planted defects caught (an
evidence-free set of headline numbers -> `claims_have_evidence`; a
reproduction guide pointing at files that do not exist -> `repro_paths_exist`;
a generic-filler hot take -> `hot_take_grounded`), zero false alarms across
all five honest submissions. The baseline scores those three with a
confident paragraph and no flag, because a single prompt has nowhere to put
a check. This part is fully deterministic - it does not move between runs.

## Improvement Changelog

Each row is one change isolated on top of the row above, re-scored against
the same 10-case human panel by [`eval/run_ablation.py`](eval/run_ablation.py).
Full per-submission table in [`eval/ABLATIONS.md`](eval/ABLATIONS.md).

| Stage | Change | MAE vs. human | Spearman | Verdict |
|---|---|---|---|---|
| Baseline | single prompt, **raw** submission text | 11.2 | 0.857 | starting point |
| + Evidence ledger | still one combined call, but scoring from the **extracted ledger** instead of raw text | 12.2 | 0.893 | **mixed** - MAE slightly worse (the ledger compresses out nuance), but rank correlation improves; the scorer still over-credits a tidy-looking ledger (`fabricated_claims` 42 -> 65) |
| + Specialist split | one call **per criterion** with a strict "deduct from full marks for a named weakness" prompt, shared ledger + running memory, verification still off | 11.2 | 0.894 | **returns MAE to baseline** - splitting the job and forcing per-criterion deductions undoes the ledger's calibration cost but does not beat the single prompt on its own |
| + Verification (final) | the deterministic flags are passed to the specialist calls, which are told to treat any FLAGGED result as a real deduction | **7.8** | 0.875 | **the change that matters (-3.4 MAE)** - and the only thing that catches the 3 seeded defects - **kept** |

**The single change that contributed most:** feeding the **deterministic
verification flags** into the scorers as mandatory deductions. It moved MAE
from 11.2 (specialist split alone, no better than the baseline) to 7.8, and
it is 100% reproducible. The six specialist scoring calls on their own were
*not* the improvement - the ablation is explicit about that.

**Removed experiment:** doing the verification step with an **LLM** instead
of pure Python (`agent/panelassist/verify_llm.py`, kept in the repo, off
the pipeline). Measured head-to-head in
[`eval/REMOVED_EXPERIMENT.md`](eval/REMOVED_EXPERIMENT.md): on all 10
submissions it caught the same 3/3 seeded defects with the same 0 false
alarms as the deterministic checks, and no verdict changed across 3 runs
each - it did *not* fail on accuracy. It was cut anyway: +30 LLM calls, and
"stable across 3 runs" is not "reproducible" for a sampled model. A flag a
judge acts on should be one they can re-derive by hand. This is the removed
experiment precisely because the result was "the cheap deterministic
version is just as good here" - the project's own thesis applied to itself.

**What I would ship next:** the ablation says the evidence-ledger step and
the bare specialist split each cost more than they return. A leaner v2 would
keep the single-prompt score, run the deterministic verification pass as a
side-car, and use one focused re-score call *only* on the criteria a flag
touches - most of the measured gain, a fraction of the calls.

## Main failure mode and hot take

**Where PanelAssist is weakest:** `good_project_bad_writeup` - a
substantively strong project wrapped in an obviously AI-generated write-up.
The panel scored it 78 (End to End Quality 10/20); PanelAssist scored it 94.
The End to End Quality specialist is told to judge the finish and voice of
the submission, and it still gave near-full marks - "reads as an unedited AI
draft" is a judgement no `os.path.exists` call makes, and the scoring model
is not reliably sensitive to it. Same shape on `cosmetic_orchestration`:
whether four agents earn their cost is a call the pipeline reasons out like
the baseline does.

**Hot take:** I expected the six specialist scoring calls to be the win.
They were not - the ablation shows the bare split scoring no better than one
holistic prompt, and the evidence-ledger step actively trading calibration
for ranking. What put the pipeline ahead was the least glamorous component:
a pure-Python pass that checks whether a claim names a file and whether the
repro paths exist, *plus a scoring instruction that forces the deduction
when a flag fires*. An LLM judge - one call or seven - is bad at **not
looking**: it reads a confident submission and scores the confidence. You do
not fix that with more judge calls. You fix it with a deterministic check
that runs every time, and a rule that the check's output is a subtraction,
not a footnote. Add the cheap check before you add the sixth model call.

## Dogfooding: PanelAssist on its own submission

This project is packaged as one of its own inputs in
[`dogfood/panelassist_self/`](dogfood/panelassist_self/) (a `manifest.json`
of what the submission ships, the real README/REPRODUCE, and one real run
from `trajectories/panelassist_runs.json` as the trajectory). Running
`python agent/run_agent.py --submissions-dir dogfood ...` points PanelAssist
at itself.

**It caught two real problems, on two passes.**

*Pass 1* flagged `repro_paths_exist` on `.env` and `data/submissions/` -
"referenced by the guide, not in the submission." Both were the *check*
being wrong, not the guide: `.env` is deliberately absent (ground rule 8)
and `data/submissions/` is a directory whose files are all shipped.
`check_repro_paths_exist` was a flat set-membership test with no notion of a
directory reference or a "create this file" instruction. Fixed in
[`verify.py`](agent/panelassist/verify.py) (`_CREATE_NOT_SHIP` +
directory-prefix matching); confirmed against all ten mock submissions that
the fix changes **zero** of their flags.

*Pass 2* (after REPRODUCE.md grew a dogfood section, then again after the
Results section was rewritten) flagged `repro_paths_exist` on files the
guide newly mentioned - `results/dogfood_scores.json`, `.gitignore`, and
others - that were real shipped files but missing from the hand-curated
self-manifest. Every doc edit that named a new filename re-tripped it. That
is precisely the gap the check is for (guide and package listing drifting
apart), and the fix was structural: generate
[`dogfood/panelassist_self/manifest.json`](dogfood/panelassist_self/manifest.json)'s
file list from `git ls-files` so it cannot fall out of sync with what
actually ships.

After both fixes the self-review runs with no `repro_paths_exist` /
`claims_have_evidence` / `hot_take_grounded` flags. Full walk-through in
[`trajectories/DOGFOOD_TRAJECTORY.md`](trajectories/DOGFOOD_TRAJECTORY.md).
What the self-review *cannot* tell me is the thing in the hot take: whether
the six specialist scoring calls earned their cost. Only the ablation
answers that, and it says the verification pass did, the scoring calls did
not.

## Ground-rules compliance

1. **Known tools** - Python standard library, the Gemini / OpenAI-compatible
   REST APIs, the `anthropic` SDK, and the LatentStack gateway as transport.
   All permitted; PDF says building with known tools and LLM APIs is fine.
2. **Before vs. during** - see "What existed before..." above; every `.py`
   and `.md` file here was written during the hackathon.
3. **Licenses / terms** - official APIs and a gateway the author has
   legitimate access to, used within their terms. The gateway is used only
   to avoid the AI Studio free-tier request cap; it routes to the same
   `gemini-3.6-flash` and the code runs identically against the direct API.
4. **Consequential actions sandboxed / human-approved** - PanelAssist takes
   **no actions**. It writes JSON and Markdown reports. Nothing to sandbox.
5. **Qualified human in the loop** - the output is advisory by
   construction; `orchestrate.py` returns a `disclaimer` and a
   `needs_human_attention` list and never a decision.
6-7. **Legal / ethical / synthetic data** - all ten eval submissions are
   synthetic and written for this project; no real customer or personal
   data.
8. **No credentials in the submission** - `.env` is git-ignored; the repo
   contains no keys. Check before zipping.
9. **Every result claim tied to evidence** - every number in this README
   is produced by a script in `eval/` and lives in `eval/RESULTS.md` or
   `eval/ABLATIONS.md`. No hand-typed metrics.
10. **Judges can reproduce** - [REPRODUCE.md](REPRODUCE.md), tested from a
   clean venv.

## Repo layout

```
rubric.py                          exact 100-point rubric, verbatim from the challenge PDF
common/llm.py                      provider-agnostic LLM wrapper (Gemini REST + Anthropic SDK)
common/loader.py                   loads a submission folder into a dict
common/stats.py                    dependency-free MAE + Spearman (no scipy)
baseline/baseline_scorer.py        the single-prompt baseline
agent/panelassist/extract.py       evidence-ledger extraction (1 call)
agent/panelassist/verify.py        deterministic verification checks (no LLM)
agent/panelassist/score.py         per-criterion specialist scoring (6 calls)
agent/panelassist/memory.py        running notes carried across criteria in one review
agent/panelassist/orchestrate.py   extract -> verify -> score -> aggregate
agent/panelassist/ablations.py     intermediate pipeline variants for the changelog
agent/run_agent.py                 CLI entrypoint for the full agent
agent/render_trajectories.py       renders trajectories/TRAJECTORIES.md
agent/panelassist/verify_llm.py    REMOVED experiment: LLM verification (off the pipeline, kept for reproducibility)
eval/run_eval.py                   baseline vs. agent vs. human ground truth
eval/run_ablation.py               the measured improvement changelog
eval/run_removed_experiment.py     deterministic vs. LLM verification, head-to-head
tests/                             pytest over the deterministic pieces (verify, stats, loader, JSON parse)
data/submissions/                  10 synthetic mock submissions
data/human_scores.json             human-panel ground truth
dogfood/panelassist_self/          this project packaged as its own input, for the self-review
TOOLS.md                           coding-agent-use disclosure (Claude Code)
agent_build_trace/                 key-redacted transcript of the build session + BUILD_LOG.md
```

**Tests:** `pip install pytest && python -m pytest tests/ -q` - 28 tests
over `verify.py` (the four checks, incl. the seeded-issue catches and the
directory-prefix / create-not-ship logic), `stats.py` (MAE / Spearman vs
hand-computed values), `loader.py`, and `common/llm._extract_json_object`.
No LLM, no network.

**How this was built:** see [TOOLS.md](TOOLS.md) and
[`agent_build_trace/BUILD_LOG.md`](agent_build_trace/BUILD_LOG.md).
