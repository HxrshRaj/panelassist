# Reproduction guide

Everything below was run on **Windows 11, Python 3.11.9**, model
**`gemini-3.6-flash`** reached through the **LatentStack** gateway
(`https://latentstack.dev/v1`, an OpenAI-compatible endpoint) via plain
`urllib` - no SDK. The same code runs unchanged against the direct Google
AI Studio Gemini API or against Anthropic Claude by editing `.env` (see
*Provider choice* below). macOS/Linux: replace `py -m venv` with
`python3 -m venv` and `.venv\Scripts\activate` with
`source .venv/bin/activate`.

**Why the gateway and not the Gemini API directly:** the direct AI Studio
free tier caps `gemini-3.6-flash` at **20 requests/day**, and a full run of
this project is ~180 LLM calls (10 baseline + 70 agent + ~66 ablation + 30
removed-experiment + 7 dogfood). The gateway removes that cap; it routes to
the same model. Nothing about the method depends on the gateway - point
`.env` at the direct API (with billing enabled) and the numbers reproduce.

Full end-to-end wall-clock for all scripts via the gateway: roughly
**40-55 minutes** (sequential LLM calls, ~9-15s each; the model spends part
of each response on hidden reasoning). Measured API cost for the whole run:
**well under $1** (the gateway returns a `cost_usd` per call; `eval/RESULTS.md`
reports $0.006 for the baseline and $0.057 for the agent over all 10 cases).

---

## 1. Setup from a clean environment

```bash
git clone <repo-url>
cd panelassist

py -m venv .venv
.venv\Scripts\activate            # Windows
# source .venv/bin/activate       # macOS / Linux

pip install -r requirements.txt
```

`requirements.txt` has exactly one hard dependency, `python-dotenv`. Every
model call in the default (LatentStack / Gemini) path uses only the Python
standard library. `anthropic` is listed commented-out - uncomment it only
if you set `LLM_PROVIDER=anthropic`. Verified from a clean venv with only
`python-dotenv` installed: `run_eval.py`, `render_trajectories.py`, and a
live `call_json` all run.

## 2. Provide an API key

Create a file named `.env` in the project root (it is git-ignored - see
`.gitignore` - so it never lands in the submission):

```
LLM_PROVIDER=latentstack
LATENTSTACK_API_KEY=your-key-here
LATENTSTACK_MODEL=gemini-3.6-flash
LATENTSTACK_BASE_URL=https://latentstack.dev/v1
```

### Provider choice (reproducibility, not a code change)

`common/llm.py` is the only file that talks to a model, and it supports
three providers picked from `.env` alone - nothing else in the codebase
changes.

**Direct Google AI Studio Gemini** (free tier = 20 requests/day for
`gemini-3.6-flash`, which is *not* enough for a full run - enable billing
on the project first):

```
LLM_PROVIDER=gemini
GEMINI_API_KEY=your-key-here       # from https://aistudio.google.com/apikey
GEMINI_MODEL=gemini-3.6-flash
```

**Anthropic Claude** (uncomment `anthropic` in `requirements.txt` and
`pip install -r requirements.txt` again first):

```
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=your-key-here
ANTHROPIC_MODEL=claude-sonnet-4-5-20250929
```

The numbers in `README.md` are from the `gemini-3.6-flash` run. Re-running
on a different model shifts the absolute scores; the *comparison* (baseline
vs. PanelAssist, the ablation ordering, the 3/3 seeded-issue detection) is
the result, not any single score.

## 3. Run the baseline (single-prompt scorer)

```bash
python baseline/baseline_scorer.py
```

Writes `results/baseline_scores.json` - one score object per mock
submission (`data/submissions/`, 10 synthetic cases) plus a call log with
per-call token counts and latency. ~2 minutes.

## 4. Run PanelAssist (the agent)

```bash
python agent/run_agent.py
```

Writes:
- `results/agent_scores.json` - the full advisory review per submission:
  the evidence ledger, the deterministic verification flags, all six
  per-criterion specialist calls with their citations and confidence, the
  aggregated total, and the `needs_human_attention` / disclaimer fields.
- `trajectories/panelassist_runs.json` - the machine-readable trajectory
  for every run.

~13-16 minutes (7 LLM calls per submission x 10, ~10-15s each via the gateway).

## 5. Compare baseline vs. PanelAssist vs. the human panel

```bash
python eval/run_eval.py
```

Reads `results/baseline_scores.json`, `results/agent_scores.json`, and the
human ground truth in `data/human_scores.json`. Writes
`eval/results.json` and `eval/RESULTS.md`, and prints the report. No LLM
calls - this step is pure arithmetic and is instant.

The ground truth (`data/human_scores.json`) was scored by the author
acting as the qualified human reviewer (ground rule 5), from an initial
draft that was then reviewed and adjusted. It is never shown to either
scorer at inference time.

## 6. Reproduce the measured improvement changelog (ablation)

```bash
python eval/run_ablation.py
```

Re-runs two intermediate pipeline variants (evidence ledger + one combined
call; specialist split with verification disabled) and writes
`eval/ABLATIONS.md` - the table showing what each design step contributed,
scored against the same human panel. It reuses `results/baseline_scores.json`,
`results/agent_scores.json`, and the saved evidence ledgers for the other
rows. ~13-16 minutes.

## 7. Reproduce the removed experiment (LLM vs. deterministic verification)

```bash
python eval/run_removed_experiment.py
```

Runs `agent/panelassist/verify_llm.py` (the removed LLM-based verification)
3x per submission against the deterministic `verify.py`, and writes
`eval/REMOVED_EXPERIMENT.md`: did each catch the seeded issues, false
positives on the clean control, run-to-run stability, extra call cost.
~8-10 minutes (30 LLM calls, 3 per submission x 10).

## 8. Dogfood - run PanelAssist on its own submission

```bash
python agent/run_agent.py --submissions-dir dogfood \
  --out results/dogfood_scores.json \
  --trajectories-out trajectories/dogfood_runs.json
python agent/render_trajectories.py \
  --agent-scores results/dogfood_scores.json --submissions-dir dogfood \
  --slugs panelassist_self --out trajectories/DOGFOOD_TRAJECTORY.md
```

`dogfood/panelassist_self/` packages this project as one of PanelAssist's
own inputs. See the "Dogfooding" section of `README.md` for what the first
pass caught. ~2 minutes (7 LLM calls).

## 9. Render the readable agent trajectories

```bash
python agent/render_trajectories.py
```

Turns `results/agent_scores.json` into `trajectories/TRAJECTORIES.md` - a
step-by-step walk-through (instruction given -> evidence seen -> output
produced) for four representative submissions. No LLM calls. Pass
`--slugs a,b,c` to choose which submissions to render.

---

## What "the main result" is

`eval/RESULTS.md`, specifically:

1. **Seeded-issue detection.** Three of the ten mock submissions each
   contain one deliberately planted, rubric-violating defect (an
   evidence-free headline claim; a reproduction guide that points at files
   that do not exist; a hot take that is generic filler). PanelAssist's
   deterministic verification layer is built to catch exactly these. The
   single-prompt baseline has no mechanism to, by construction - that is
   the comparison.
2. **Agreement with the human panel** - total-score MAE (baseline 11.2,
   PanelAssist 7.8) and Spearman rank correlation (0.857 vs 0.875).
   PanelAssist is closer on both, driven by the six mid-band submissions
   that have one localized rubric flaw a holistic single pass scores over.
3. **Cost/latency delta** - PanelAssist is 7x the calls of the baseline
   ($0.006 -> $0.057, 112s -> 932s over all 10). `eval/RESULTS.md` has the
   measured token counts.
4. **The ablation** (`eval/ABLATIONS.md`) - which design step helped and
   which did not. The evidence-ledger stage trades calibration for ranking,
   the bare specialist split scores no better than the baseline, and the
   deterministic verification flags feeding the scorers are the -3.4 MAE
   that puts the pipeline ahead.

## Troubleshooting

- **`No LLM API key found`** - the `.env` file is missing or in the wrong
  directory. It must be in the project root, next to `rubric.py`.
- **`Gemini API 429 ... GenerateRequestsPerDayPerProjectPerModel-FreeTier`**
  - the direct AI Studio free tier is 20 requests/day; a full run needs ~180. Enable billing on the API project, or use `LLM_PROVIDER=latentstack`
  / `LLM_PROVIDER=anthropic`.
- **`Gemini API error 404 ... no longer available`** - the pinned model
  was retired. Set the model id in `.env` to a current one.
- **`... request failed after 3 attempts`** - network/timeout. The wrapper
  already retries with backoff; re-run the script, it is idempotent (it
  overwrites its output files).
- **`No module named 'anthropic'`** - you set `LLM_PROVIDER=anthropic`
  without uncommenting `anthropic` in `requirements.txt`. Uncomment it and
  reinstall, or use a different provider.
- **Scores differ from `README.md`** - expected. Live LLM calls at
  `temperature=0` are not perfectly deterministic, and model versions move.
  The *shape* of the result - verification catches the 3 seeded issues with
  no false alarms; the ablation shows the bare specialist split scoring no
  better than the single prompt and the verification flags being the step
  that puts the agent ahead on MAE - is what should reproduce, not any exact
  score. The baseline in particular is unstable run-to-run.
