# PanelAssist agent trajectories

Representative end-to-end runs, rendered from `results/agent_scores.json` by `agent/render_trajectories.py`. Each section walks one submission from the instructions the agent was given to its final aggregated (advisory) score. The machine-readable form of every run is in `trajectories/panelassist_runs.json`.

**Rendered submissions:** `panelassist_self`

---

# Trajectory - `panelassist_self`

PanelAssist processes one submission as a fixed pipeline: **1** evidence extraction call, **1** deterministic verification pass (no LLM), then **6** specialist scoring calls (one per rubric criterion) that share the evidence ledger and a running set of notes. Nothing below is a final decision -- see the disclaimer at the end.

## Input given to the agent

- **Submission:** `panelassist_self`
- **Files the agent was told exist in the submission:**
- README.md
- REPRODUCE.md
- VIDEO_SCRIPT.md
- requirements.txt
- rubric.py
- common/llm.py
- common/loader.py
- common/stats.py
- baseline/baseline_scorer.py
- agent/run_agent.py
- agent/render_trajectories.py
- agent/panelassist/extract.py
- agent/panelassist/verify.py
- agent/panelassist/verify_llm.py
- agent/panelassist/score.py
- agent/panelassist/memory.py
- agent/panelassist/orchestrate.py
- agent/panelassist/ablations.py
- eval/run_eval.py
- eval/run_ablation.py
- eval/run_removed_experiment.py
- eval/RESULTS.md
- eval/results.json
- eval/ABLATIONS.md
- eval/REMOVED_EXPERIMENT.md
- results/baseline_scores.json
- results/agent_scores.json
- trajectories/panelassist_runs.json
- trajectories/TRAJECTORIES.md
- data/human_scores.json
- data/submissions/strong_baseline_done_right/README.md
- data/submissions/weak_single_prompt/README.md
- data/submissions/fabricated_claims/README.md
- data/submissions/broken_repro/README.md
- data/submissions/thin_hot_take/README.md
- data/submissions/cosmetic_orchestration/README.md
- data/submissions/good_project_bad_writeup/README.md
- data/submissions/real_gains_no_changelog/README.md
- data/submissions/overengineered_but_honest/README.md
- data/submissions/scope_mismatch/README.md

## Step 1 - Evidence extraction (1 LLM call)

**Instruction (system prompt):**

> You extract structured facts from a hackathon submission. Be literal and skeptical: only mark a claim as evidence-backed if the submission actually points to a specific file, dataset, script, or trajectory step that would let someone verify it. Confident wording is not evidence.

**Task:** read README + REPRODUCE.md + file listing + trajectory log and return one structured *evidence ledger* - target user, bottleneck, which agent capabilities the submission actually uses, every headline claim plus whether a specific checkable file backs it, every path/env-var the reproduction guide references, and whether the hot take is grounded.

**Output - the evidence ledger (reused by every step below):**

```json
{
  "target_user": "micro1 hackathon judge",
  "bottleneck": "A tired judge under time pressure scoring dozens of submissions easily misses evidence-free claims, ungrounded hot takes, and broken reproduction file references.",
  "agent_capabilities_used": [
    "verification",
    "memory",
    "orchestration",
    "human_checkpoint"
  ],
  "changelog_entries": [
    {
      "stage": "Baseline",
      "evidence": "Single prompt on raw submission text scored MAE 5.33, Spearman 1.000 vs. human panel.",
      "decision": "Starting point baseline."
    },
    {
      "stage": "+ Evidence ledger",
      "evidence": "Scoring from extracted ledger instead of raw text degraded MAE to 10.17 by compressing out context nuance.",
      "decision": "Rejected / hurt performance."
    },
    {
      "stage": "+ Specialist split",
      "evidence": "One call per criterion with shared ledger and running memory improved MAE to 8.67.",
      "decision": "Partial recovery (-1.5 MAE)."
    },
    {
      "stage": "+ Verification (final)",
      "evidence": "Deterministic Python checks reduced total MAE to 6.33, improved Reproducibility MAE to 0.67, and achieved 1.00 recall/precision on planted defects.",
      "decision": "Kept as primary positive contributor."
    }
  ],
  "claimed_results": [
    {
      "claim": "Seeded-issue recall 1.00 (3/3 planted defects caught)",
      "has_supporting_evidence_file": true,
      "supporting_file": "eval/RESULTS.md"
    },
    {
      "claim": "Seeded-issue precision 1.00 (0 false alarms on clean control)",
      "has_supporting_evidence_file": true,
      "supporting_file": "eval/RESULTS.md"
    },
    {
      "claim": "Reproducibility sub-score MAE 0.67 vs. human (vs 1.17 baseline)",
      "has_supporting_evidence_file": true,
      "supporting_file": "eval/RESULTS.md"
    },
    {
      "claim": "Total-score MAE vs. human 6.33 (Baseline 5.33)",
      "has_supporting_evidence_file": true,
      "supporting_file": "eval/RESULTS.md"
    },
    {
      "claim": "Spearman rank correlation 0.943 vs. human (Baseline 1.000)",
      "has_supporting_evidence_file": true,
      "supporting_file": "eval/RESULTS.md"
    }
  ],
  "repro_referenced_paths": [
    "requirements.txt",
    ".env",
    "common/llm.py",
    "baseline/baseline_scorer.py",
    "results/baseline_scores.json",
    "data/submissions/",
    "agent/run_agent.py",
    "results/agent_scores.json",
    "trajectories/panelassist_runs.json",
    "eval/run_eval.py",
    "data/human_scores.json",
    "eval/results.json",
    "eval/RESULTS.md",
    "eval/run_ablation.py",
    "eval/ABLATIONS.md",
    "eval/run_removed_experiment.py",
    "agent/panelassist/verify_llm.py",
    "agent/panelassist/verify.py",
    "eval/REMOVED_EXPERIMENT.md",
    "dogfood/panelassist_self/",
    "results/dogfood_scores.json",
    "trajectories/dogfood_runs.json",
    "agent/render_trajectories.py",
    "trajectories/DOGFOOD_TRAJECTORY.md",
    "trajectories/TRAJECTORIES.md",
    "rubric.py"
  ],
  "repro_referenced_env_vars": [
    "LLM_PROVIDER",
    "LATENTSTACK_API_KEY",
    "LATENTSTACK_MODEL",
    "LATENTSTACK_BASE_URL",
    "GEMINI_API_KEY",
    "GEMINI_MODEL",
    "ANTHROPIC_API_KEY",
    "ANTHROPIC_MODEL"
  ],
  "hot_take_text": "I built a seven-call agent to out-judge one careful prompt, and on the score itself it didn't - the honest ablation says the extra machinery slightly hurt agreement with the human panel. What survived measurement was the least clever part: a pure-Python pass that checks whether each headline claim names a file and whether the repro guide's paths exist. That is the failure a rushed judge actually makes - not misjudging, but not looking - and you don't fix 'not looking' with a smarter model, because the strong model is already a decent holistic judge. You fix it with a deterministic step that runs every time and leaves a citation behind. The lesson I am taking to the next agent: when a cheap deterministic check and an LLM call can do the same job, measure both before you assume the LLM is the upgrade - here the check won on accuracy, cost, and reproducibility, and the six extra model calls were the thing to cut.",
  "hot_take_is_generic": false,
  "human_approval_gate_present": true
}
```

## Step 2 - Deterministic verification (no LLM)

Pure-Python checks run against the ledger from Step 1. These are the checks a single-prompt baseline has no mechanism to perform.

| Check | Result | Detail |
|---|---|---|
| `repro_paths_exist` | **FLAGGED** | The reproduction guide references 4 path(s) not present anywhere in the submission: ['dogfood/panelassist_self/', 'results/dogfood_scores.json', 'trajectories/dogfood_runs.json', 'trajectories/DOGFOOD_TRAJECTORY.md']. A judge following this guide from a clean environment would fail here. |
| `env_var_consistency` | PASS | No env-var/provider mismatch detected. |
| `claims_have_evidence` | PASS | Every headline claim points to a specific, checkable file. |
| `hot_take_grounded` | PASS | Hot take connects to a specific failure mode observed in this project. |

## Steps 3-8 - Specialist scoring, one call per criterion

**Shared instruction (system prompt) for all six:**

> You are one specialist on a hackathon judging panel, responsible for exactly ONE rubric criterion. Follow these rules:
1. Judge only your criterion. Strength on other dimensions is irrelevant here -- a brilliant idea earns nothing for End to End Quality, a polished write-up earns nothing for Problem & User Value, a strong result earns nothing for Measured Improvement if the iteration story is missing.
2. Start from full marks, then deduct for each specific weakness you can name. Award more than 85% of the points ONLY if you cannot name a concrete weakness. Most real submissions have at least one.
3. Treat every FLAGGED verification result as a real deduction on the criterion it bears on, not a footnote.
4. Confident wording is not evidence. A claim with no backing file in the ledger scores as unsupported.
5. Cite the specific quote, file name, or verification flag behind your score, and name the weakness(es) you deducted for.

Each call additionally sees: the exact rubric text for its one criterion, the Step 1 evidence ledger, the Step 2 verification flags, and the running notes left by criteria scored before it.

### Step 3 - Problem & User Value (max 15)

**Instruction for this criterion:**

- _What strong work looks like:_ A strong project solves a meaningful problem for a clearly defined user.
- _Ask yourself:_ Who experiences the bottleneck and why does solving it matter?

**Running notes inherited from earlier criteria:**
_(none)_

**Output:**

- **Score:** 15 / 15
- **Confidence:** high
- **Rationale:** The project defines an exceptionally clear target user (micro1 hackathon judges) and articulates a precise bottleneck (rushed judges missing evidence-free claims and broken repro paths), demonstrating deep user understanding without any identifiable gaps in problem formulation.
- **Evidence cited:**
- README.md: "The user is a micro1 hackathon judge. This challenge alone drew 8,300+ registrations, all to be scored against a published 100-point rubric..."
- README.md: "The bottleneck is not 'reading takes time' - it is that a tired judge under time pressure, scoring their fortieth submission of the day, is exactly who a confidently-worded but evidence-free submission slips past."
- **Note passed forward:** Target user and problem framing focus specifically on pre-screening submissions to assist human hackathon judges.

### Step 4 - Agent Solution & Engineering (max 30)

**Instruction for this criterion:**

- _What strong work looks like:_ A strong solution uses agents purposefully and is technically sound. Better context or tools may improve one project, while memory, verification, skills or orchestration may improve another.
- _Ask yourself:_ Which design choices helped the agent solve the problem?

**Running notes inherited from earlier criteria:**
- (Problem & User Value) Target user and problem framing focus specifically on pre-screening submissions to assist human hackathon judges.

**Output:**

- **Score:** 22 / 30
- **Confidence:** high
- **Rationale:** While the agent design features good modularity, deterministic Python verification tools, and cross-criterion memory, points are deducted because the multi-call LLM orchestration/ledger compression hurt core scoring performance compared to the baseline, and a deterministic verification flag was triggered for missing referenced dogfood trajectory paths.
- **Evidence cited:**
- [FLAGGED] repro_paths_exist: The reproduction guide references 4 path(s) not present anywhere in the submission: ['dogfood/panelassist_self/', 'results/dogfood_scores.json', 'trajectories/dogfood_runs.json', 'trajectories/DOGFOOD_TRAJECTORY.md'].
- README.md: 'Scoring from extracted ledger instead of raw text degraded MAE to 10.17 by compressing out context nuance.'
- README.md: 'Total-score MAE vs. human 6.33 (Baseline 5.33)'
- **Note passed forward:** The deterministic Python verification module succeeded in catching 100% of seeded defects, demonstrating that pure-Python checks outperformed LLM verification tools in the pipeline.

### Step 5 - End to End Quality (max 20)

**Instruction for this criterion:**

- _What strong work looks like:_ A strong solution completes a realistic and self contained execution and produces a final result the user can use, with the finish of something a person would sign their name to rather than an obvious AI generated draft.
- _Ask yourself:_ Would the intended user consider this output high quality, or does it read as clearly AI generated?

**Running notes inherited from earlier criteria:**
- (Problem & User Value) Target user and problem framing focus specifically on pre-screening submissions to assist human hackathon judges.
- (Agent Solution & Engineering) The deterministic Python verification module succeeded in catching 100% of seeded defects, demonstrating that pure-Python checks outperformed LLM verification tools in the pipeline.

**Output:**

- **Score:** 12 / 20
- **Confidence:** high
- **Rationale:** The output artifacts, reports, and code reflect high polish and professional craftsmanship rather than an unedited AI draft. However, the end-to-end execution is incomplete because the dogfooding directory referenced in REPRODUCE.md Step 8 was omitted from the repository files, breaking that execution path.
- **Evidence cited:**
- [FLAGGED] repro_paths_exist: The reproduction guide references 4 path(s) not present anywhere in the submission: ['dogfood/panelassist_self/', 'results/dogfood_scores.json', 'trajectories/dogfood_runs.json', 'trajectories/DOGFOOD_TRAJECTORY.md'].
- **Note passed forward:** The missing dogfood directory directly impacts execution of Step 8 in REPRODUCE.md.

### Step 6 - Measured Improvement (max 15)

**Instruction for this criterion:**

- _What strong work looks like:_ A strong report demonstrates gains over a fair baseline and uses the changelog to connect each iteration with evidence.
- _Ask yourself:_ Which changes truly improved the outcome?

**Running notes inherited from earlier criteria:**
- (Problem & User Value) Target user and problem framing focus specifically on pre-screening submissions to assist human hackathon judges.
- (Agent Solution & Engineering) The deterministic Python verification module succeeded in catching 100% of seeded defects, demonstrating that pure-Python checks outperformed LLM verification tools in the pipeline.
- (End to End Quality) The missing dogfood directory directly impacts execution of Step 8 in REPRODUCE.md.

**Output:**

- **Score:** 12 / 15
- **Confidence:** high
- **Rationale:** The submission provides an exemplary, highly disciplined changelog and ablation methodology that isolates each step's quantitative impact against a fair baseline. However, points are deducted because the iterated agent ultimately regressed on overall total-score MAE and Spearman correlation relative to the simple single-prompt baseline.
- **Evidence cited:**
- eval/RESULTS.md: Total-score MAE vs. human 6.33 (Baseline 5.33)
- eval/RESULTS.md: Spearman rank correlation 0.943 vs. human (Baseline 1.000)
- eval/ABLATIONS.md: Baseline (5.33 MAE) -> + Evidence ledger (10.17 MAE) -> + Specialist split (8.67 MAE) -> + Verification (6.33 MAE)
- **Note passed forward:** While total score accuracy regressed overall, the deterministic verification layer specifically delivered clear gains in defect recall (1.00 vs 0.00) and Reproducibility sub-score MAE (0.67 vs 1.17).

### Step 7 - Reproducibility (max 15)

**Instruction for this criterion:**

- _What strong work looks like:_ A reproducible project gives another person a clear path to run the solution and baseline and reach the main result.
- _Ask yourself:_ Could they do it from a clean environment?

**Running notes inherited from earlier criteria:**
- (Problem & User Value) Target user and problem framing focus specifically on pre-screening submissions to assist human hackathon judges.
- (Agent Solution & Engineering) The deterministic Python verification module succeeded in catching 100% of seeded defects, demonstrating that pure-Python checks outperformed LLM verification tools in the pipeline.
- (End to End Quality) The missing dogfood directory directly impacts execution of Step 8 in REPRODUCE.md.
- (Measured Improvement) While total score accuracy regressed overall, the deterministic verification layer specifically delivered clear gains in defect recall (1.00 vs 0.00) and Reproducibility sub-score MAE (0.67 vs 1.17).

**Output:**

- **Score:** 5 / 15
- **Confidence:** high
- **Rationale:** Although REPRODUCE.md contains setup instructions and provider options, deterministic verification flagged 4 referenced paths missing from the repository. Because a verification flag hits this criterion directly, the score falls into the <35% score band.
- **Evidence cited:**
- [FLAGGED] repro_paths_exist: The reproduction guide references 4 path(s) not present anywhere in the submission: ['dogfood/panelassist_self/', 'results/dogfood_scores.json', 'trajectories/dogfood_runs.json', 'trajectories/DOGFOOD_TRAJECTORY.md']
- REPRODUCE.md: '8. Dogfood - run PanelAssist on its own submission'
- **Note passed forward:** Execution of dogfooding instructions in Step 8 fails due to missing files in the submission.

### Step 8 - Hot Take / Insights (max 5)

**Instruction for this criterion:**

- _What strong work looks like:_ A strong insight turns an observed failure mode into a practical lesson for building more reliable agents.
- _Ask yourself:_ What did you learn and how would it change what you build next?

**Running notes inherited from earlier criteria:**
- (Problem & User Value) Target user and problem framing focus specifically on pre-screening submissions to assist human hackathon judges.
- (Agent Solution & Engineering) The deterministic Python verification module succeeded in catching 100% of seeded defects, demonstrating that pure-Python checks outperformed LLM verification tools in the pipeline.
- (End to End Quality) The missing dogfood directory directly impacts execution of Step 8 in REPRODUCE.md.
- (Measured Improvement) While total score accuracy regressed overall, the deterministic verification layer specifically delivered clear gains in defect recall (1.00 vs 0.00) and Reproducibility sub-score MAE (0.67 vs 1.17).
- (Reproducibility) Execution of dogfooding instructions in Step 8 fails due to missing files in the submission.

**Output:**

- **Score:** 5 / 5
- **Confidence:** high
- **Rationale:** The hot take is exemplary, turning an honest negative result from their ablation (that a 7-call agent slightly degraded total MAE vs a single prompt) into a profound, grounded lesson about using deterministic checks instead of LLM calls when applicable.
- **Evidence cited:**
- hot_take_text: 'I built a seven-call agent to out-judge one careful prompt, and on the score itself it didn't - the honest ablation says the extra machinery slightly hurt agreement with the human panel...'
- DETERMINISTIC VERIFICATION FLAGS: [OK] hot_take_grounded: Hot take connects to a specific failure mode observed in this project.
- **Note passed forward:** The author's hot take transparently highlights that deterministic checks were the primary positive contributor to performance gains over the baseline.

## Final aggregation

- **Total (sum of the six specialist scores):** 71 / 100
- **Needs human attention:** True
- **Low-confidence criteria:** _(none)_
- **Failed verification checks:** `repro_paths_exist`

**Accumulated review notes:**
- (Problem & User Value) Target user and problem framing focus specifically on pre-screening submissions to assist human hackathon judges.
- (Agent Solution & Engineering) The deterministic Python verification module succeeded in catching 100% of seeded defects, demonstrating that pure-Python checks outperformed LLM verification tools in the pipeline.
- (End to End Quality) The missing dogfood directory directly impacts execution of Step 8 in REPRODUCE.md.
- (Measured Improvement) While total score accuracy regressed overall, the deterministic verification layer specifically delivered clear gains in defect recall (1.00 vs 0.00) and Reproducibility sub-score MAE (0.67 vs 1.17).
- (Reproducibility) Execution of dogfooding instructions in Step 8 fails due to missing files in the submission.
- (Hot Take / Insights) The author's hot take transparently highlights that deterministic checks were the primary positive contributor to performance gains over the baseline.

> Advisory pre-screen only. Every score above is a starting point with cited evidence for a qualified human judge to confirm, adjust, or override -- this tool does not make a final accept/reject or prize decision.

---
