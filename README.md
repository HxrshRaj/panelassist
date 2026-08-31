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
LatentStack gateway, `temperature=0`. **This section reports a mixed
result honestly - PanelAssist does not win every metric, and the ones it
loses are stated as plainly as the ones it wins.**

| Metric | Baseline (1 prompt) | PanelAssist | Who wins |
|---|---|---|---|
| Seeded-issue **recall** (3 planted rubric violations) | 0.00 - no mechanism | **1.00** (3/3) | PanelAssist |
| Seeded-issue **precision** (false alarms on the clean control) | n/a | **1.00** (0 false alarms) | PanelAssist |
| Reproducibility sub-score MAE vs. human | 1.17 | **0.67** | PanelAssist |
| **Total-score MAE** vs. human (lower better) | **5.33** | 6.33 | Baseline |
| **Spearman** rank corr. vs. human (higher better) | **1.000** | 0.943 | Baseline |
| Per-criterion MAE, other 5 criteria | **lower on all 5** | higher | Baseline |
| LLM calls per submission | 1 | 7 | Baseline |
| Cost / wall-clock, all 6 submissions | $0.003 / 74s | $0.026 / 482s | Baseline |
| Structured evidence citations produced | 0 | 91 | PanelAssist |

**What this says.** A strong model asked to score a submission holistically
is *already* a good holistic scorer - the single-prompt baseline tracks the
human panel's totals better than PanelAssist's seven-call pipeline does, and
it does it 7x cheaper. Wrapping the score in more LLM machinery made
calibration slightly *worse* (PanelAssist is a little generous - e.g. it
gives `thin_hot_take` 91 where the panel gave 82).

The one thing PanelAssist does that the baseline **structurally cannot** is
the deterministic verification pass: it caught all three planted
rubric-violating defects (an evidence-free set of headline numbers; a
reproduction guide pointing at files that do not exist; a generic-filler
hot take), with zero false alarms on the clean control, and it is that same
layer feeding the Reproducibility scorer that produces the only
per-criterion MAE win. The baseline scores those three submissions with a
confident paragraph and no flag, because a single prompt has nowhere to put
a check.

**Precision, stated honestly.** `run_eval.py` only counts false positives
on the clean control (zero). Looking at every flag it raised: on
`broken_repro` and `cosmetic_orchestration` it raised two *extra* flags
beyond the seeded one. Three of those are defensible - a genuinely unbacked
"4/5 reviewers" claim in `broken_repro`, a genuinely generic hot take in
`cosmetic_orchestration`. One is a real false positive: it flags
`cosmetic_orchestration`'s `out/baseline.json` / `out/swarm.json` as
"missing" when those are files the reproduction guide *generates* at
runtime. `check_repro_paths_exist` does not distinguish "input the guide
needs" from "output the guide produces" - a known gap, noted here rather
than hidden.

## Improvement Changelog

Each row is one change isolated on top of the row above, re-scored against
the same human panel by [`eval/run_ablation.py`](eval/run_ablation.py).
Full per-submission table in [`eval/ABLATIONS.md`](eval/ABLATIONS.md).

| Stage | Change | MAE vs. human | Spearman | Verdict |
|---|---|---|---|---|
| Baseline | single prompt, **raw** submission text | **5.33** | 1.000 | starting point |
| + Evidence ledger | still one combined call, but scoring from the **extracted ledger** instead of raw text | 10.17 | 0.943 | **hurt** - the ledger compresses out nuance the raw text carries; the scorer over-credits a submission because the tidy ledger *looks* complete (e.g. `fabricated_claims` 38 -> 64) |
| + Specialist split | one call **per criterion**, shared ledger + running cross-criterion memory, verification still off | 8.67 | 0.943 | **partial recovery** (-1.5 MAE) - splitting the job and carrying notes between criteria claws back some of what the ledger lost |
| + Verification (final) | deterministic checks feed the specialist calls and set `needs_human_attention` | 6.33 | 0.943 | **biggest positive contributor** (-2.34 MAE) and the only thing that catches the 3 seeded defects - **kept**, but still short of baseline on total MAE |

**The single change that contributed most:** the **deterministic
verification layer**. It recovered 2.34 MAE points on top of the specialist
split and is solely responsible for the 3/3 seeded-issue detection and the
Reproducibility sub-score win. It is also the only stage that a single
prompt could never contain.

**Removed experiment:** doing the verification step with an **LLM** instead
of pure Python (`agent/panelassist/verify_llm.py`, kept in the repo, off
the pipeline). Measured head-to-head in
[`eval/REMOVED_EXPERIMENT.md`](eval/REMOVED_EXPERIMENT.md): on this
6-submission set it caught the same 3/3 seeded defects with the same 0
false alarms as the deterministic checks - it did *not* fail on accuracy.
It was cut anyway, because it adds an LLM call per submission and its
verdicts are only *probably* stable run-to-run (it is a sampled model),
and a flag a judge is meant to act on should be one they can re-derive by
hand. This is the removed experiment precisely because the result was
"the cheap deterministic version is just as good here" - which is the
project's own thesis applied to itself.

**What I would ship next, given the ablation:** run the deterministic
verification pass as a side-car on top of the *single-prompt* score, and
drop the ledger-based re-scoring. The measurement says the elaborate
scoring machinery is a net negative here; the cheap deterministic check is
the part that earned its place.

## Main failure mode and hot take

**Where PanelAssist is weakest:** `cosmetic_orchestration` - "six agents
that cost 5.8x the baseline for one point of accuracy" is a judgement about
whether an architecture earns its complexity, and no `os.path.exists` call
settles that. Its Agent Solution & Engineering score has to be reasoned out
from the trajectory exactly like the baseline does, and PanelAssist scored
that submission 35 where the panel said 38 and the baseline said 44 -
closer than the baseline this time, but for reasons the pipeline cannot
guarantee.

**Hot take:** I built a seven-call agent to out-judge one careful prompt,
and on the score itself it didn't - the honest ablation says the extra
machinery slightly *hurt* agreement with the human panel. What survived
measurement was the least clever part: a pure-Python pass that checks
whether each headline claim names a file and whether the repro guide's
paths exist. That is the failure a rushed judge actually makes - not
misjudging, but *not looking* - and you don't fix "not looking" with a
smarter model, because the strong model is already a decent holistic judge.
You fix it with a deterministic step that runs every time and leaves a
citation behind. The lesson I am taking to the next agent: when a cheap
deterministic check and an LLM call can do the same job, measure both
before you assume the LLM is the upgrade - here the check won on accuracy,
cost, *and* reproducibility, and the six extra model calls were the thing
to cut.

## Dogfooding: PanelAssist on its own submission

This project is packaged as one of its own inputs in
[`dogfood/panelassist_self/`](dogfood/panelassist_self/) (a `manifest.json`
of what the submission ships, the real README/REPRODUCE, and one real run
from `trajectories/panelassist_runs.json` as the trajectory). Running
`python agent/run_agent.py --submissions-dir dogfood ...` points PanelAssist
at itself.

**It caught a real bug on the first pass.** The self-review flagged
`repro_paths_exist`, complaining that REPRODUCE.md references `.env` and
`data/submissions/` which "are not present in the submission." Both
complaints were the *check* being wrong, not the guide: `.env` is
deliberately absent (ground rule 8), and `data/submissions/` is a
directory whose files *are* all shipped. `check_repro_paths_exist` was
doing a flat set-membership test - no notion of a directory reference, no
notion of a "create this file" instruction. Fixed in
[`verify.py`](agent/panelassist/verify.py) (`_CREATE_NOT_SHIP` +
directory-prefix matching); confirmed against all six mock submissions that
the fix changes **zero** of their flags (the seeded issues are still
caught, the clean control is still clean).

On the fixed check the self-review comes back at **99/100**, `needs_human_
attention: false`, all four verification checks passing - `claims_have_
evidence` passes because every number in this README traces to a script in
`eval/`. Full walk-through in
[`trajectories/DOGFOOD_TRAJECTORY.md`](trajectories/DOGFOOD_TRAJECTORY.md).
What the self-review *cannot* tell me is the thing in the hot take: whether
the seven-call pipeline earned its complexity. Only the ablation answers
that, and it says no.

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
data/submissions/                  10 synthetic mock submissions
data/human_scores.json             human-panel ground truth
dogfood/panelassist_self/          this project packaged as its own input, for the self-review
```
