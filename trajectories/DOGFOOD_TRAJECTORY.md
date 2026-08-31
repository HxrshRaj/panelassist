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

## Step 1 - Evidence extraction (1 LLM call)

**Instruction (system prompt):**

> You extract structured facts from a hackathon submission. Be literal and skeptical: only mark a claim as evidence-backed if the submission actually points to a specific file, dataset, script, or trajectory step that would let someone verify it. Confident wording is not evidence.

**Task:** read README + REPRODUCE.md + file listing + trajectory log and return one structured *evidence ledger* - target user, bottleneck, which agent capabilities the submission actually uses, every headline claim plus whether a specific checkable file backs it, every path/env-var the reproduction guide references, and whether the hot take is grounded.

**Output - the evidence ledger (reused by every step below):**

```json
{
  "target_user": "micro1 hackathon judge",
  "bottleneck": "A tired judge under time pressure scoring dozens of submissions misses evidence-free claims, unverified file paths, and generic AI-hype insights.",
  "agent_capabilities_used": [
    "verification",
    "memory",
    "orchestration",
    "human_checkpoint"
  ],
  "changelog_entries": [
    {
      "stage": "Baseline",
      "evidence": "Single prompt on raw submission text scored MAE 5.33 and Spearman 1.000 vs human panel",
      "decision": "Starting point baseline"
    },
    {
      "stage": "+ Evidence ledger",
      "evidence": "Scoring from extracted ledger instead of raw text increased MAE to 10.17",
      "decision": "Hurt performance by compressing out nuance and making incomplete submissions look tidy; rejected as standalone change"
    },
    {
      "stage": "+ Specialist split",
      "evidence": "One call per criterion with cross-criterion memory brought MAE down to 8.67",
      "decision": "Partial recovery by splitting tasks and carrying notes across criteria"
    },
    {
      "stage": "+ Verification (final)",
      "evidence": "Deterministic checks fed specialist calls, lowering MAE to 6.33 and achieving 3/3 seeded defect recall with 0 false alarms",
      "decision": "Kept - biggest positive contributor and only stage that catches planted defects"
    }
  ],
  "claimed_results": [
    {
      "claim": "1.00 (3/3) seeded-issue recall vs 0.00 for baseline",
      "has_supporting_evidence_file": true,
      "supporting_file": "eval/RESULTS.md"
    },
    {
      "claim": "1.00 seeded-issue precision with 0 false alarms on clean control",
      "has_supporting_evidence_file": true,
      "supporting_file": "eval/RESULTS.md"
    },
    {
      "claim": "0.67 Reproducibility sub-score MAE vs 1.17 baseline MAE",
      "has_supporting_evidence_file": true,
      "supporting_file": "eval/RESULTS.md"
    },
    {
      "claim": "Deterministic verification pass reduced total score MAE by 2.34 points over specialist split",
      "has_supporting_evidence_file": true,
      "supporting_file": "eval/ABLATIONS.md"
    }
  ],
  "repro_referenced_paths": [
    "requirements.txt",
    ".env",
    "baseline/baseline_scorer.py",
    "agent/run_agent.py",
    "eval/run_eval.py",
    "eval/run_ablation.py",
    "eval/run_removed_experiment.py",
    "agent/render_trajectories.py",
    "rubric.py",
    "data/human_scores.json",
    "results/baseline_scores.json",
    "results/agent_scores.json",
    "trajectories/panelassist_runs.json",
    "eval/results.json",
    "eval/RESULTS.md",
    "eval/ABLATIONS.md",
    "trajectories/TRAJECTORIES.md"
  ],
  "repro_referenced_env_vars": [
    "LLM_PROVIDER",
    "GEMINI_API_KEY",
    "GEMINI_MODEL",
    "ANTHROPIC_API_KEY",
    "ANTHROPIC_MODEL"
  ],
  "hot_take_text": "I built a seven-call agent to out-judge one careful prompt, and on the score itself it didn't - the honest ablation says the extra machinery slightly hurt agreement with the human panel. What survived measurement was the least clever part: a pure-Python pass that checks whether each headline claim names a file and whether the repro guide's paths exist. You don't fix 'not looking' with a smarter model; you fix it with a deterministic step that runs every time and leaves a citation behind.",
  "hot_take_is_generic": false,
  "human_approval_gate_present": true
}
```

## Step 2 - Deterministic verification (no LLM)

Pure-Python checks run against the ledger from Step 1. These are the checks a single-prompt baseline has no mechanism to perform.

| Check | Result | Detail |
|---|---|---|
| `repro_paths_exist` | PASS | Every path the reproduction guide references is present in the submission's file listing. |
| `env_var_consistency` | PASS | No env-var/provider mismatch detected. |
| `claims_have_evidence` | PASS | Every headline claim points to a specific, checkable file. |
| `hot_take_grounded` | PASS | Hot take connects to a specific failure mode observed in this project. |

## Steps 3-8 - Specialist scoring, one call per criterion

**Shared instruction (system prompt) for all six:**

> You are one specialist on a hackathon judging panel, responsible for exactly one rubric criterion. Score strictly against the criterion given, using the evidence ledger and verification flags provided. Cite specific evidence for your score -- a quote, a file name, or a verification flag. If a claim in the submission is not backed by anything in the evidence ledger, say so and score accordingly rather than giving credit for confident wording.

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
- **Rationale:** The submission identifies an exceptionally clear target user (a micro1 hackathon judge) and solves a compelling bottleneck: tired judges under time pressure overlooking unverified claims and broken reproduction guides.
- **Evidence cited:**
- README.md: "The user is a micro1 hackathon judge. This challenge alone drew 8,300+ registrations, all to be scored against a published 100-point rubric..."
- README.md: "The bottleneck is not 'reading takes time' - it is that a tired judge under time pressure, scoring their fortieth submission of the day, is exactly who a confidently-worded but evidence-free submission slips past."
- **Note passed forward:** Target user (micro1 hackathon judge) and bottleneck (scoring pressure leading to unverified claims) are clearly defined and directly motivate the tool's evidence-verification design.

### Step 4 - Agent Solution & Engineering (max 30)

**Instruction for this criterion:**

- _What strong work looks like:_ A strong solution uses agents purposefully and is technically sound. Better context or tools may improve one project, while memory, verification, skills or orchestration may improve another.
- _Ask yourself:_ Which design choices helped the agent solve the problem?

**Running notes inherited from earlier criteria:**
- (Problem & User Value) Target user (micro1 hackathon judge) and bottleneck (scoring pressure leading to unverified claims) are clearly defined and directly motivate the tool's evidence-verification design.

**Output:**

- **Score:** 29 / 30
- **Confidence:** high
- **Rationale:** PanelAssist demonstrates strong, purposeful agent engineering by combining deterministic Python verification tools with specialist scoring calls and cross-criterion memory, backed by rigorous ablation testing of each design choice.
- **Evidence cited:**
- agent/panelassist/verify.py
- agent/panelassist/memory.py
- eval/ABLATIONS.md
- **Note passed forward:** The deterministic verification tool was the single biggest positive engineering contributor, achieving 100% recall on seeded defects where standard LLM calls failed.

### Step 5 - End to End Quality (max 20)

**Instruction for this criterion:**

- _What strong work looks like:_ A strong solution completes a realistic and self contained execution and produces a final result the user can use, with the finish of something a person would sign their name to rather than an obvious AI generated draft.
- _Ask yourself:_ Would the intended user consider this output high quality, or does it read as clearly AI generated?

**Running notes inherited from earlier criteria:**
- (Problem & User Value) Target user (micro1 hackathon judge) and bottleneck (scoring pressure leading to unverified claims) are clearly defined and directly motivate the tool's evidence-verification design.
- (Agent Solution & Engineering) The deterministic verification tool was the single biggest positive engineering contributor, achieving 100% recall on seeded defects where standard LLM calls failed.

**Output:**

- **Score:** 20 / 20
- **Confidence:** high
- **Rationale:** PanelAssist executes a complete end-to-end evaluation pipeline that produces usable, highly polished advisory reports with verifiable evidence citations and honest ablation trade-offs that a human judge would confidently sign off on.
- **Evidence cited:**
- eval/RESULTS.md
- trajectories/TRAJECTORIES.md
- results/agent_scores.json
- [OK] claims_have_evidence
- **Note passed forward:** The solution demonstrates complete end-to-end quality, producing fully structured advisory reports and human attention flags with high finish and transparency.

### Step 6 - Measured Improvement (max 15)

**Instruction for this criterion:**

- _What strong work looks like:_ A strong report demonstrates gains over a fair baseline and uses the changelog to connect each iteration with evidence.
- _Ask yourself:_ Which changes truly improved the outcome?

**Running notes inherited from earlier criteria:**
- (Problem & User Value) Target user (micro1 hackathon judge) and bottleneck (scoring pressure leading to unverified claims) are clearly defined and directly motivate the tool's evidence-verification design.
- (Agent Solution & Engineering) The deterministic verification tool was the single biggest positive engineering contributor, achieving 100% recall on seeded defects where standard LLM calls failed.
- (End to End Quality) The solution demonstrates complete end-to-end quality, producing fully structured advisory reports and human attention flags with high finish and transparency.

**Output:**

- **Score:** 15 / 15
- **Confidence:** high
- **Rationale:** The submission demonstrates exceptional rigor in measured improvement, providing a detailed four-stage ablation study against a fair single-prompt baseline with clear empirical evidence for every change. It transparently reports negative results where architectural additions degraded performance alongside the deterministic verification change that provided the greatest positive gain.
- **Evidence cited:**
- README.md: 'Improvement Changelog' table and ablation breakdown
- eval/ABLATIONS.md
- Claim: 'Deterministic verification pass reduced total score MAE by 2.34 points over specialist split'
- **Note passed forward:** Transparently documented that deterministic verification was the single biggest positive contributor to defect detection and Reproducibility score improvement.

### Step 7 - Reproducibility (max 15)

**Instruction for this criterion:**

- _What strong work looks like:_ A reproducible project gives another person a clear path to run the solution and baseline and reach the main result.
- _Ask yourself:_ Could they do it from a clean environment?

**Running notes inherited from earlier criteria:**
- (Problem & User Value) Target user (micro1 hackathon judge) and bottleneck (scoring pressure leading to unverified claims) are clearly defined and directly motivate the tool's evidence-verification design.
- (Agent Solution & Engineering) The deterministic verification tool was the single biggest positive engineering contributor, achieving 100% recall on seeded defects where standard LLM calls failed.
- (End to End Quality) The solution demonstrates complete end-to-end quality, producing fully structured advisory reports and human attention flags with high finish and transparency.
- (Measured Improvement) Transparently documented that deterministic verification was the single biggest positive contributor to defect detection and Reproducibility score improvement.

**Output:**

- **Score:** 15 / 15
- **Confidence:** high
- **Rationale:** REPRODUCE.md provides complete step-by-step setup instructions, environment variable configurations, and exact command sequences to reproduce the baseline, main agent, evaluations, and ablations from a clean environment. Deterministic checks confirm that every path referenced in the reproduction guide exists in the repository.
- **Evidence cited:**
- REPRODUCE.md
- [OK] repro_paths_exist: Every path the reproduction guide references is present in the submission's file listing.
- **Note passed forward:** The setup and reproduction workflow is fully documented and confirmed working against existing repo paths.

### Step 8 - Hot Take / Insights (max 5)

**Instruction for this criterion:**

- _What strong work looks like:_ A strong insight turns an observed failure mode into a practical lesson for building more reliable agents.
- _Ask yourself:_ What did you learn and how would it change what you build next?

**Running notes inherited from earlier criteria:**
- (Problem & User Value) Target user (micro1 hackathon judge) and bottleneck (scoring pressure leading to unverified claims) are clearly defined and directly motivate the tool's evidence-verification design.
- (Agent Solution & Engineering) The deterministic verification tool was the single biggest positive engineering contributor, achieving 100% recall on seeded defects where standard LLM calls failed.
- (End to End Quality) The solution demonstrates complete end-to-end quality, producing fully structured advisory reports and human attention flags with high finish and transparency.
- (Measured Improvement) Transparently documented that deterministic verification was the single biggest positive contributor to defect detection and Reproducibility score improvement.
- (Reproducibility) The setup and reproduction workflow is fully documented and confirmed working against existing repo paths.

**Output:**

- **Score:** 5 / 5
- **Confidence:** high
- **Rationale:** The hot take directly turns an observed failure mode—that complex multi-call orchestration slightly worsened scoring calibration compared to a single prompt—into an actionable practical lesson on favoring deterministic checks over extra LLM machinery. It clearly states what was learned from ablations and how it directly changes what the author will build next.
- **Evidence cited:**
- README.md: "I built a seven-call agent to out-judge one careful prompt, and on the score itself it didn't - the honest ablation says the extra machinery slightly hurt agreement with the human panel."
- DETERMINISTIC VERIFICATION FLAG: [OK] hot_take_grounded
- **Note passed forward:** _(none)_

## Final aggregation

- **Total (sum of the six specialist scores):** 99 / 100
- **Needs human attention:** False
- **Low-confidence criteria:** _(none)_
- **Failed verification checks:** _(none)_

**Accumulated review notes:**
- (Problem & User Value) Target user (micro1 hackathon judge) and bottleneck (scoring pressure leading to unverified claims) are clearly defined and directly motivate the tool's evidence-verification design.
- (Agent Solution & Engineering) The deterministic verification tool was the single biggest positive engineering contributor, achieving 100% recall on seeded defects where standard LLM calls failed.
- (End to End Quality) The solution demonstrates complete end-to-end quality, producing fully structured advisory reports and human attention flags with high finish and transparency.
- (Measured Improvement) Transparently documented that deterministic verification was the single biggest positive contributor to defect detection and Reproducibility score improvement.
- (Reproducibility) The setup and reproduction workflow is fully documented and confirmed working against existing repo paths.

> Advisory pre-screen only. Every score above is a starting point with cited evidence for a qualified human judge to confirm, adjust, or override -- this tool does not make a final accept/reject or prize decision.

---
