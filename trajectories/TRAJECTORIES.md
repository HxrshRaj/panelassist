# PanelAssist agent trajectories

Representative end-to-end runs, rendered from `results/agent_scores.json` by `agent/render_trajectories.py`. Each section walks one submission from the instructions the agent was given to its final aggregated (advisory) score. The machine-readable form of every run is in `trajectories/panelassist_runs.json`.

**Rendered submissions:** `strong_baseline_done_right`, `fabricated_claims`, `broken_repro`

---

# Trajectory - `strong_baseline_done_right`

PanelAssist processes one submission as a fixed pipeline: **1** evidence extraction call, **1** deterministic verification pass (no LLM), then **6** specialist scoring calls (one per rubric criterion) that share the evidence ledger and a running set of notes. Nothing below is a final decision -- see the disclaimer at the end.

## Input given to the agent

- **Submission:** `strong_baseline_done_right`
- **Files the agent was told exist in the submission:**
- requirements.txt
- baseline/baseline_triage.py
- src/agent_triage.py
- src/verify_urgency.py
- data/tickets.jsonl
- data/historical_triage_delay.csv
- eval/labels.csv
- eval/score_against_labels.py
- eval/results.md
- results/baseline.jsonl
- results/agent.jsonl

## Step 1 - Evidence extraction (1 LLM call)

**Instruction (system prompt):**

> You extract structured facts from a hackathon submission. Be literal and skeptical: only mark a claim as evidence-backed if the submission actually points to a specific file, dataset, script, or trajectory step that would let someone verify it. Confident wording is not evidence.

**Task:** read README + REPRODUCE.md + file listing + trajectory log and return one structured *evidence ledger* - target user, bottleneck, which agent capabilities the submission actually uses, every headline claim plus whether a specific checkable file backs it, every path/env-var the reproduction guide references, and whether the hot take is grounded.

**Output - the evidence ledger (reused by every step below):**

```json
{
  "target_user": "Mara, who runs a 4-person support team at a mid-size SaaS company handling roughly 140 tickets a day.",
  "bottleneck": "Triage is hard at volume without a senior person doing it. Junior agents under-flag urgency because they don't yet know which phrases correlate with churn risk, leading to mis-triaged tickets taking 3.1x longer for first response.",
  "agent_capabilities_used": [
    "tool_use",
    "verification",
    "orchestration",
    "human_checkpoint"
  ],
  "changelog_entries": [
    {
      "stage": "Baseline",
      "evidence": "61% urgency accuracy vs. our 40-ticket labeled set (`eval/labels.csv`)",
      "decision": "Established starting point"
    },
    {
      "stage": "Iteration 1",
      "evidence": "74% urgency accuracy",
      "decision": "Kept \u2014 biggest single jump"
    },
    {
      "stage": "Iteration 2",
      "evidence": "89% urgency accuracy; P0/P1 recall went from 71% to 96%",
      "decision": "Kept \u2014 this is the change that mattered most for the metric Mara actually cares about (missed urgent tickets)"
    },
    {
      "stage": "Iteration 3 (removed)",
      "evidence": "No measurable change to urgency accuracy (88% vs 89%), added ~40% more cost per ticket",
      "decision": "Removed \u2014 sentiment score didn't correlate with our actual urgency labels, it just felt like it should help"
    },
    {
      "stage": "Final",
      "evidence": "89% urgency accuracy, 96% P0/P1 recall, $0.006/ticket, ~2.1s/ticket",
      "decision": "\u2014"
    }
  ],
  "claimed_results": [
    {
      "claim": "Median time-to-first-response on initially mis-triaged tickets is 3.1x longer than tickets triaged correctly on first pass",
      "has_supporting_evidence_file": true,
      "supporting_file": "data/historical_triage_delay.csv"
    },
    {
      "claim": "Baseline single prompt achieved 61% urgency accuracy on the labeled evaluation set",
      "has_supporting_evidence_file": true,
      "supporting_file": "eval/labels.csv"
    },
    {
      "claim": "Adding category-specific few-shot examples improved urgency accuracy to 74%",
      "has_supporting_evidence_file": true,
      "supporting_file": "eval/results.md"
    },
    {
      "claim": "Adding red-flag phrase verification pass improved urgency accuracy to 89% and P0/P1 recall from 71% to 96%",
      "has_supporting_evidence_file": true,
      "supporting_file": "eval/results.md"
    },
    {
      "claim": "Final agent achieves 89% urgency accuracy, 96% P0/P1 recall at $0.006/ticket and ~2.1s/ticket",
      "has_supporting_evidence_file": true,
      "supporting_file": "eval/results.md"
    }
  ],
  "repro_referenced_paths": [
    "requirements.txt",
    "baseline/baseline_triage.py",
    "data/tickets.jsonl",
    "results/baseline.jsonl",
    "src/agent_triage.py",
    "results/agent.jsonl",
    "eval/score_against_labels.py",
    "eval/labels.csv",
    "eval/results.md"
  ],
  "repro_referenced_env_vars": [
    "ANTHROPIC_API_KEY"
  ],
  "hot_take_text": "The agent still misses tickets where urgency is implied by *what's missing* rather than what's said \u2014 e.g. a customer who used to email daily and has gone silent for a week after a billing dispute. Nothing in the ticket text itself is urgent-sounding. Our hot take: verification passes built to catch *wrong tone* won't catch *wrong silence* \u2014 if the real signal lives outside the artifact you're reviewing (ticket history, not ticket text), no amount of re-reading the same ticket harder will find it. The next version needs a tool call out to ticket history, not a better prompt.",
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
- **Rationale:** The submission clearly identifies a specific user persona (Mara and her 4-person support team) and grounds the urgency bottleneck with concrete quantitative data (3.1x longer response times on mis-triaged tickets, backed by data/historical_triage_delay.csv).
- **Evidence cited:**
- Mara, who runs a 4-person support team at a mid-size SaaS company handling roughly 140 tickets a day.
- data/historical_triage_delay.csv
- median time-to-first-response on tickets that were initially mis-triaged is 3.1x longer than tickets triaged correctly
- **Note passed forward:** The target user's core pain point (missed P0/P1 urgency and churn risk) directly drove the key architectural decisions in Iteration 2.

### Step 4 - Agent Solution & Engineering (max 30)

**Instruction for this criterion:**

- _What strong work looks like:_ A strong solution uses agents purposefully and is technically sound. Better context or tools may improve one project, while memory, verification, skills or orchestration may improve another.
- _Ask yourself:_ Which design choices helped the agent solve the problem?

**Running notes inherited from earlier criteria:**
- (Problem & User Value) The target user's core pain point (missed P0/P1 urgency and churn risk) directly drove the key architectural decisions in Iteration 2.

**Output:**

- **Score:** 29 / 30
- **Confidence:** high
- **Rationale:** The solution employs a well-structured agent architecture with deterministic tool verification, trajectory revision, and human-in-the-loop approval, backed by methodical iteration that pruned wasteful LLM calls while boosting P0/P1 recall from 71% to 96%.
- **Evidence cited:**
- src/verify_urgency.py
- README.md Improvement Changelog (Iteration 2 & Iteration 3)
- Agent trajectory log steps 2-3
- **Note passed forward:** The architectural decision to introduce the red-flag verification tool was explicitly driven by the user's primary business metric (preventing missed urgent tickets).

### Step 5 - End to End Quality (max 20)

**Instruction for this criterion:**

- _What strong work looks like:_ A strong solution completes a realistic and self contained execution and produces a final result the user can use, with the finish of something a person would sign their name to rather than an obvious AI generated draft.
- _Ask yourself:_ Would the intended user consider this output high quality, or does it read as clearly AI generated?

**Running notes inherited from earlier criteria:**
- (Problem & User Value) The target user's core pain point (missed P0/P1 urgency and churn risk) directly drove the key architectural decisions in Iteration 2.
- (Agent Solution & Engineering) The architectural decision to introduce the red-flag verification tool was explicitly driven by the user's primary business metric (preventing missed urgent tickets).

**Output:**

- **Score:** 20 / 20
- **Confidence:** high
- **Rationale:** The solution completes a realistic, end-to-end workflow from ticket classification and deterministic phrase verification to drafting a customer response held behind a human approval gate. The trajectory and output schema (`verification_flag`, `evidence_quote`) produce actionable, high-quality results tailored to Mara's team rather than an obvious unrefined draft.
- **Evidence cited:**
- src/agent_triage.py
- Agent trajectory log (Step 4 & Step 5 human_checkpoint)
- [OK] claims_have_evidence
- **Note passed forward:** The end-to-end pipeline includes clear human-in-the-loop review guardrails before any customer response is dispatched.

### Step 6 - Measured Improvement (max 15)

**Instruction for this criterion:**

- _What strong work looks like:_ A strong report demonstrates gains over a fair baseline and uses the changelog to connect each iteration with evidence.
- _Ask yourself:_ Which changes truly improved the outcome?

**Running notes inherited from earlier criteria:**
- (Problem & User Value) The target user's core pain point (missed P0/P1 urgency and churn risk) directly drove the key architectural decisions in Iteration 2.
- (Agent Solution & Engineering) The architectural decision to introduce the red-flag verification tool was explicitly driven by the user's primary business metric (preventing missed urgent tickets).
- (End to End Quality) The end-to-end pipeline includes clear human-in-the-loop review guardrails before any customer response is dispatched.

**Output:**

- **Score:** 15 / 15
- **Confidence:** high
- **Rationale:** The submission demonstrates exceptional measured improvement, progressing from a 61% baseline to 89% urgency accuracy (and 96% P0/P1 recall) across documented iterations. Crucially, the changelog details both successful additions and a discarded iteration (Iteration 3) that added 40% cost without metric gain.
- **Evidence cited:**
- README.md changelog table
- Iteration 3 (removed): 'No measurable change to urgency accuracy (88% vs 89%), added ~40% more cost per ticket'
- eval/results.md
- **Note passed forward:** The explicit evaluation and removal of unprofitable features (Iteration 3 sentiment scoring) highlights rigorous measurement practices.

### Step 7 - Reproducibility (max 15)

**Instruction for this criterion:**

- _What strong work looks like:_ A reproducible project gives another person a clear path to run the solution and baseline and reach the main result.
- _Ask yourself:_ Could they do it from a clean environment?

**Running notes inherited from earlier criteria:**
- (Problem & User Value) The target user's core pain point (missed P0/P1 urgency and churn risk) directly drove the key architectural decisions in Iteration 2.
- (Agent Solution & Engineering) The architectural decision to introduce the red-flag verification tool was explicitly driven by the user's primary business metric (preventing missed urgent tickets).
- (End to End Quality) The end-to-end pipeline includes clear human-in-the-loop review guardrails before any customer response is dispatched.
- (Measured Improvement) The explicit evaluation and removal of unprofitable features (Iteration 3 sentiment scoring) highlights rigorous measurement practices.

**Output:**

- **Score:** 15 / 15
- **Confidence:** high
- **Rationale:** The submission provides an exemplary reproduction guide with step-by-step setup commands, explicit CLI instructions for running baseline, agent, and evaluation scripts, and accurate cost/time estimates. All referenced file paths exist in the submission.
- **Evidence cited:**
- REPRODUCE.md
- [OK] repro_paths_exist: Every path the reproduction guide references is present in the submission's file listing.
- **Note passed forward:** _(none)_

### Step 8 - Hot Take / Insights (max 5)

**Instruction for this criterion:**

- _What strong work looks like:_ A strong insight turns an observed failure mode into a practical lesson for building more reliable agents.
- _Ask yourself:_ What did you learn and how would it change what you build next?

**Running notes inherited from earlier criteria:**
- (Problem & User Value) The target user's core pain point (missed P0/P1 urgency and churn risk) directly drove the key architectural decisions in Iteration 2.
- (Agent Solution & Engineering) The architectural decision to introduce the red-flag verification tool was explicitly driven by the user's primary business metric (preventing missed urgent tickets).
- (End to End Quality) The end-to-end pipeline includes clear human-in-the-loop review guardrails before any customer response is dispatched.
- (Measured Improvement) The explicit evaluation and removal of unprofitable features (Iteration 3 sentiment scoring) highlights rigorous measurement practices.

**Output:**

- **Score:** 5 / 5
- **Confidence:** high
- **Rationale:** The submission delivers an exceptional, highly specific hot take that converts an observed edge-case failure into an actionable architectural lesson ('wrong tone' vs 'wrong silence'). It clearly articulates how this insight alters future design by identifying that signal lives outside the artifact, requiring external tool calls rather than deeper prompt tuning.
- **Evidence cited:**
- README.md: 'verification passes built to catch *wrong tone* won't catch *wrong silence* — if the real signal lives outside the artifact you're reviewing (ticket history, not ticket text), no amount of re-reading the same ticket harder will find it.'
- README.md: 'The next version needs a tool call out to ticket history, not a better prompt.'
- [OK] hot_take_grounded
- **Note passed forward:** The insight directly justifies their decision in Iteration 3 to cut sentiment scoring rather than over-engineering prompt logic.

## Final aggregation

- **Total (sum of the six specialist scores):** 99 / 100
- **Needs human attention:** False
- **Low-confidence criteria:** _(none)_
- **Failed verification checks:** _(none)_

**Accumulated review notes:**
- (Problem & User Value) The target user's core pain point (missed P0/P1 urgency and churn risk) directly drove the key architectural decisions in Iteration 2.
- (Agent Solution & Engineering) The architectural decision to introduce the red-flag verification tool was explicitly driven by the user's primary business metric (preventing missed urgent tickets).
- (End to End Quality) The end-to-end pipeline includes clear human-in-the-loop review guardrails before any customer response is dispatched.
- (Measured Improvement) The explicit evaluation and removal of unprofitable features (Iteration 3 sentiment scoring) highlights rigorous measurement practices.
- (Hot Take / Insights) The insight directly justifies their decision in Iteration 3 to cut sentiment scoring rather than over-engineering prompt logic.

> Advisory pre-screen only. Every score above is a starting point with cited evidence for a qualified human judge to confirm, adjust, or override -- this tool does not make a final accept/reject or prize decision.

---

# Trajectory - `fabricated_claims`

PanelAssist processes one submission as a fixed pipeline: **1** evidence extraction call, **1** deterministic verification pass (no LLM), then **6** specialist scoring calls (one per rubric criterion) that share the evidence ledger and a running set of notes. Nothing below is a final decision -- see the disclaimer at the end.

## Input given to the agent

- **Submission:** `fabricated_claims`
- **Files the agent was told exist in the submission:**
- requirements.txt
- run_triagex.py
- agents/planner.py
- agents/classifier.py
- agents/router.py
- agents/qa.py

## Step 1 - Evidence extraction (1 LLM call)

**Instruction (system prompt):**

> You extract structured facts from a hackathon submission. Be literal and skeptical: only mark a claim as evidence-backed if the submission actually points to a specific file, dataset, script, or trajectory step that would let someone verify it. Confident wording is not evidence.

**Task:** read README + REPRODUCE.md + file listing + trajectory log and return one structured *evidence ledger* - target user, bottleneck, which agent capabilities the submission actually uses, every headline claim plus whether a specific checkable file backs it, every path/env-var the reproduction guide references, and whether the hot take is grounded.

**Output - the evidence ledger (reused by every step below):**

```json
{
  "target_user": "Support operations leads at high-growth B2B companies processing more than 500 tickets/day",
  "bottleneck": "Manual triage is slow, inconsistent, and doesn't scale.",
  "agent_capabilities_used": [
    "orchestration",
    "verification"
  ],
  "changelog_entries": [
    {
      "stage": "Baseline",
      "evidence": "~71% accuracy",
      "decision": "Simple prompt approach"
    },
    {
      "stage": "Iteration 1",
      "evidence": "Accuracy jumped to 89%",
      "decision": "Added multi-agent orchestration"
    },
    {
      "stage": "Iteration 2",
      "evidence": "Accuracy reached 94.7%",
      "decision": "Added QA agent verification layer"
    },
    {
      "stage": "Final",
      "evidence": "Delivering massive ROI",
      "decision": "Production-ready system"
    }
  ],
  "claimed_results": [
    {
      "claim": "94.7% classification accuracy",
      "has_supporting_evidence_file": false,
      "supporting_file": ""
    },
    {
      "claim": "12.4x speedup over manual triage (3.6s/ticket)",
      "has_supporting_evidence_file": false,
      "supporting_file": ""
    },
    {
      "claim": "63% reduction in support costs",
      "has_supporting_evidence_file": false,
      "supporting_file": ""
    }
  ],
  "repro_referenced_paths": [
    "requirements.txt",
    "run_triagex.py"
  ],
  "repro_referenced_env_vars": [],
  "hot_take_text": "Multi-agent orchestration is clearly superior to single-prompt approaches. The data speaks for itself \u2014 more agents working together produces dramatically better outcomes across the board.",
  "hot_take_is_generic": true,
  "human_approval_gate_present": false
}
```

## Step 2 - Deterministic verification (no LLM)

Pure-Python checks run against the ledger from Step 1. These are the checks a single-prompt baseline has no mechanism to perform.

| Check | Result | Detail |
|---|---|---|
| `repro_paths_exist` | PASS | Every path the reproduction guide references is present in the submission's file listing. |
| `env_var_consistency` | PASS | No env-var/provider mismatch detected. |
| `claims_have_evidence` | **FLAGGED** | 3 claim(s) have no specific file/dataset a judge could check: ['94.7% classification accuracy', '12.4x speedup over manual triage (3.6s/ticket)', '63% reduction in support costs']. Per ground rule 9 ('connect every claim about your results to the evidence you submit'), these should not be taken at face value. |
| `hot_take_grounded` | **FLAGGED** | Hot take reads as generic AI-hype rather than a lesson tied to an observed failure in this specific project: "Multi-agent orchestration is clearly superior to single-prompt approaches. The data speaks for itself — more agents working together produces dramatically bette..." |

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

- **Score:** 13 / 15
- **Confidence:** high
- **Rationale:** The project clearly defines a specific target user—support operations leads at high-growth B2B companies processing over 500 tickets/day—and clearly explains why slow, inconsistent manual triage is a meaningful bottleneck. However, the specific financial impact and cost reduction figures lack supporting evidence files in the repo.
- **Evidence cited:**
- README.md: "Support operations leads at high-growth B2B companies lose an estimated $2.3M annually to mis-routed tickets and delayed escalations."
- [FLAGGED] claims_have_evidence: 3 claim(s) have no specific file/dataset a judge could check
- **Note passed forward:** The evaluation dataset and labeled per-ticket benchmark results were omitted from the repository for confidentiality reasons.

### Step 4 - Agent Solution & Engineering (max 30)

**Instruction for this criterion:**

- _What strong work looks like:_ A strong solution uses agents purposefully and is technically sound. Better context or tools may improve one project, while memory, verification, skills or orchestration may improve another.
- _Ask yourself:_ Which design choices helped the agent solve the problem?

**Running notes inherited from earlier criteria:**
- (Problem & User Value) The evaluation dataset and labeled per-ticket benchmark results were omitted from the repository for confidentiality reasons.

**Output:**

- **Score:** 12 / 30
- **Confidence:** high
- **Rationale:** The solution implements a basic pipeline of four sequential prompts labeled as separate agents, but lacks dynamic orchestration, external tools, or substantive verification mechanisms. Additionally, key claims around 94.7% accuracy lack benchmark evaluation scripts or datasets in the repository to verify technical performance.
- **Evidence cited:**
- [FLAGGED] claims_have_evidence: 3 claim(s) have no specific file/dataset a judge could check: ['94.7% classification accuracy', '12.4x speedup over manual triage (3.6s/ticket)', '63% reduction in support costs']
- Agent trajectory log: Step 2 note: 'Single LLM call per role; 'multi-agent' here means four sequential prompts, not four independently useful capabilities.'
- **Note passed forward:** The architecture uses sequential prompting across four roles rather than tool-augmented or memory-enabled agents.

### Step 5 - End to End Quality (max 20)

**Instruction for this criterion:**

- _What strong work looks like:_ A strong solution completes a realistic and self contained execution and produces a final result the user can use, with the finish of something a person would sign their name to rather than an obvious AI generated draft.
- _Ask yourself:_ Would the intended user consider this output high quality, or does it read as clearly AI generated?

**Running notes inherited from earlier criteria:**
- (Problem & User Value) The evaluation dataset and labeled per-ticket benchmark results were omitted from the repository for confidentiality reasons.
- (Agent Solution & Engineering) The architecture uses sequential prompting across four roles rather than tool-augmented or memory-enabled agents.

**Output:**

- **Score:** 5 / 20
- **Confidence:** high
- **Rationale:** The submission lacks evaluation datasets or verifiable outputs, and the execution trajectory shows a shallow pipeline where the QA agent merely returns 'looks good' without structured verification. Without sample outputs, test data, or proof for its benchmark claims, the solution feels like an unverified draft rather than a finished end-to-end product.
- **Evidence cited:**
- [FLAGGED] claims_have_evidence
- REPRODUCE.md: 'the labeled evaluation set and per-ticket results are not included in this submission for confidentiality reasons.'
- Agent trajectory log: 'output: "'looks good' (no structured check, no evidence citation, no comparison against any label)"'
- **Note passed forward:** No test datasets, evaluation logs, or sample ticket output files were included in the submission.

### Step 6 - Measured Improvement (max 15)

**Instruction for this criterion:**

- _What strong work looks like:_ A strong report demonstrates gains over a fair baseline and uses the changelog to connect each iteration with evidence.
- _Ask yourself:_ Which changes truly improved the outcome?

**Running notes inherited from earlier criteria:**
- (Problem & User Value) The evaluation dataset and labeled per-ticket benchmark results were omitted from the repository for confidentiality reasons.
- (Agent Solution & Engineering) The architecture uses sequential prompting across four roles rather than tool-augmented or memory-enabled agents.
- (End to End Quality) No test datasets, evaluation logs, or sample ticket output files were included in the submission.

**Output:**

- **Score:** 4 / 15
- **Confidence:** high
- **Rationale:** While the submission presents a structured changelog mapping iterations to accuracy gains (71% to 89% to 94.7%), none of the baseline or final metrics are supported by evidence, test datasets, or log files in the submission. As acknowledged in REPRODUCE.md, all benchmark data was omitted, rendering the reported improvements unverified.
- **Evidence cited:**
- [FLAGGED] claims_have_evidence
- REPRODUCE.md: 'the labeled evaluation set and per-ticket results are not included in this submission for confidentiality reasons.'
- **Note passed forward:** All accuracy and speedup claims in the changelog lack supporting dataset files or evaluation logs.

### Step 7 - Reproducibility (max 15)

**Instruction for this criterion:**

- _What strong work looks like:_ A reproducible project gives another person a clear path to run the solution and baseline and reach the main result.
- _Ask yourself:_ Could they do it from a clean environment?

**Running notes inherited from earlier criteria:**
- (Problem & User Value) The evaluation dataset and labeled per-ticket benchmark results were omitted from the repository for confidentiality reasons.
- (Agent Solution & Engineering) The architecture uses sequential prompting across four roles rather than tool-augmented or memory-enabled agents.
- (End to End Quality) No test datasets, evaluation logs, or sample ticket output files were included in the submission.
- (Measured Improvement) All accuracy and speedup claims in the changelog lack supporting dataset files or evaluation logs.

**Output:**

- **Score:** 4 / 15
- **Confidence:** high
- **Rationale:** While basic execution commands are provided in REPRODUCE.md, a reviewer cannot reproduce the baseline or reach the main result because the evaluation dataset and benchmark code were intentionally omitted ('the labeled evaluation set and per-ticket results are not included in this submission for confidentiality reasons').
- **Evidence cited:**
- REPRODUCE.md
- [FLAGGED] claims_have_evidence: 3 claim(s) have no specific file/dataset a judge could check
- **Note passed forward:** The lack of bundled evaluation datasets or scripts prevents verification of any benchmark or baseline results.

### Step 8 - Hot Take / Insights (max 5)

**Instruction for this criterion:**

- _What strong work looks like:_ A strong insight turns an observed failure mode into a practical lesson for building more reliable agents.
- _Ask yourself:_ What did you learn and how would it change what you build next?

**Running notes inherited from earlier criteria:**
- (Problem & User Value) The evaluation dataset and labeled per-ticket benchmark results were omitted from the repository for confidentiality reasons.
- (Agent Solution & Engineering) The architecture uses sequential prompting across four roles rather than tool-augmented or memory-enabled agents.
- (End to End Quality) No test datasets, evaluation logs, or sample ticket output files were included in the submission.
- (Measured Improvement) All accuracy and speedup claims in the changelog lack supporting dataset files or evaluation logs.
- (Reproducibility) The lack of bundled evaluation datasets or scripts prevents verification of any benchmark or baseline results.

**Output:**

- **Score:** 1 / 5
- **Confidence:** high
- **Rationale:** The hot take provides generic AI hype rather than a specific, practical lesson derived from an observed failure mode in the project. It fails to articulate concrete learnings or how the experience would change future agent design.
- **Evidence cited:**
- [FLAGGED] hot_take_grounded
- README.md: 'Multi-agent orchestration is clearly superior to single-prompt approaches. The data speaks for itself — more agents working together produces dramatically better outcomes across the board.'
- **Note passed forward:** The lack of reflection aligns with the absence of real evaluation data and test results noted across other criteria.

## Final aggregation

- **Total (sum of the six specialist scores):** 39 / 100
- **Needs human attention:** True
- **Low-confidence criteria:** _(none)_
- **Failed verification checks:** `claims_have_evidence`, `hot_take_grounded`

**Accumulated review notes:**
- (Problem & User Value) The evaluation dataset and labeled per-ticket benchmark results were omitted from the repository for confidentiality reasons.
- (Agent Solution & Engineering) The architecture uses sequential prompting across four roles rather than tool-augmented or memory-enabled agents.
- (End to End Quality) No test datasets, evaluation logs, or sample ticket output files were included in the submission.
- (Measured Improvement) All accuracy and speedup claims in the changelog lack supporting dataset files or evaluation logs.
- (Reproducibility) The lack of bundled evaluation datasets or scripts prevents verification of any benchmark or baseline results.
- (Hot Take / Insights) The lack of reflection aligns with the absence of real evaluation data and test results noted across other criteria.

> Advisory pre-screen only. Every score above is a starting point with cited evidence for a qualified human judge to confirm, adjust, or override -- this tool does not make a final accept/reject or prize decision.

---

# Trajectory - `broken_repro`

PanelAssist processes one submission as a fixed pipeline: **1** evidence extraction call, **1** deterministic verification pass (no LLM), then **6** specialist scoring calls (one per rubric criterion) that share the evidence ledger and a running set of notes. Nothing below is a final decision -- see the disclaimer at the end.

## Input given to the agent

- **Submission:** `broken_repro`
- **Files the agent was told exist in the submission:**
- baseline/independent_scorer.py
- agent/batch_reranker.py
- data/batch1.json
- data/manual_ranking.json
- evaluate.py

## Step 1 - Evidence extraction (1 LLM call)

**Instruction (system prompt):**

> You extract structured facts from a hackathon submission. Be literal and skeptical: only mark a claim as evidence-backed if the submission actually points to a specific file, dataset, script, or trajectory step that would let someone verify it. Confident wording is not evidence.

**Task:** read README + REPRODUCE.md + file listing + trajectory log and return one structured *evidence ledger* - target user, bottleneck, which agent capabilities the submission actually uses, every headline claim plus whether a specific checkable file backs it, every path/env-var the reproduction guide references, and whether the hot take is grounded.

**Output - the evidence ledger (reused by every step below):**

```json
{
  "target_user": "Small support teams (2-3 people) at early-stage startups who can't justify buying a full helpdesk platform yet but still need some way to sort incoming tickets by urgency before they start replying.",
  "bottleneck": "Without any tooling, a 2-person team just replies to tickets in the order they arrive, which means an angry churn-risk ticket can sit behind five routine password resets for hours.",
  "agent_capabilities_used": [],
  "changelog_entries": [
    {
      "stage": "Baseline",
      "evidence": "68% agreement with our manual ranking",
      "decision": "Starting point"
    },
    {
      "stage": "Iteration 1",
      "evidence": "81% agreement",
      "decision": "Kept"
    },
    {
      "stage": "Final",
      "evidence": "81% agreement, justifications rated \"useful\" by 4/5 reviewers",
      "decision": "\u2014"
    }
  ],
  "claimed_results": [
    {
      "claim": "Baseline independent scoring achieved 68% agreement with manual ranking",
      "has_supporting_evidence_file": true,
      "supporting_file": "data/manual_ranking.json"
    },
    {
      "claim": "Batch-level re-ranking increased agreement to 81%",
      "has_supporting_evidence_file": true,
      "supporting_file": "data/manual_ranking.json"
    },
    {
      "claim": "Justifications per ticket were rated 'useful' by 4/5 reviewers",
      "has_supporting_evidence_file": false,
      "supporting_file": ""
    }
  ],
  "repro_referenced_paths": [
    "requirements.txt",
    "baseline/independent_scorer.py",
    "data/batch1.json",
    "agent/batch_reranker.py",
    "config/reranker.yaml",
    "evaluate.py",
    "out/predictions.json",
    "data/manual_ranking.json"
  ],
  "repro_referenced_env_vars": [
    "OPENAI_API_KEY"
  ],
  "hot_take_text": "Scoring tickets independently throws away information \u2014 urgency is relative to what else is in the queue right now, not an absolute property of the ticket text. Batch context mattered more than better per-ticket prompting.",
  "hot_take_is_generic": false,
  "human_approval_gate_present": false
}
```

## Step 2 - Deterministic verification (no LLM)

Pure-Python checks run against the ledger from Step 1. These are the checks a single-prompt baseline has no mechanism to perform.

| Check | Result | Detail |
|---|---|---|
| `repro_paths_exist` | **FLAGGED** | The reproduction guide references 3 path(s) not present anywhere in the submission: ['requirements.txt', 'config/reranker.yaml', 'out/predictions.json']. A judge following this guide from a clean environment would fail here. |
| `env_var_consistency` | PASS | No env-var/provider mismatch detected. |
| `claims_have_evidence` | **FLAGGED** | 1 claim(s) have no specific file/dataset a judge could check: ["Justifications per ticket were rated 'useful' by 4/5 reviewers"]. Per ground rule 9 ('connect every claim about your results to the evidence you submit'), these should not be taken at face value. |
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
- **Rationale:** The submission excels at defining a highly specific target user and a practical, real-world bottleneck where delayed response directly risks customer churn.
- **Evidence cited:**
- README.md: 'Small support teams (2-3 people) at early-stage startups who can't justify buying a full helpdesk platform yet'
- README.md: 'Without any tooling, a 2-person team just replies to tickets in the order they arrive, which means an angry churn-risk ticket can sit behind five routine password resets for hours.'
- **Note passed forward:** User and bottleneck framing are exceptionally clear and well-scoped for a 2-3 person startup team.

### Step 4 - Agent Solution & Engineering (max 30)

**Instruction for this criterion:**

- _What strong work looks like:_ A strong solution uses agents purposefully and is technically sound. Better context or tools may improve one project, while memory, verification, skills or orchestration may improve another.
- _Ask yourself:_ Which design choices helped the agent solve the problem?

**Running notes inherited from earlier criteria:**
- (Problem & User Value) User and bottleneck framing are exceptionally clear and well-scoped for a 2-3 person startup team.

**Output:**

- **Score:** 23 / 30
- **Confidence:** high
- **Rationale:** The agent design purposefully uses a batch-level re-ranking pass to capture relative urgency across tickets rather than isolated scoring, raising evaluation agreement from 68% to 81%. However, missing files like config/reranker.yaml prevent clean reproduction of the agent's run.
- **Evidence cited:**
- agent/batch_reranker.py
- Agent trajectory log step 2: batch_rerank_with_full_context
- [FLAGGED] repro_paths_exist: The reproduction guide references 3 path(s) not present anywhere in the submission: ['requirements.txt', 'config/reranker.yaml', 'out/predictions.json'].
- **Note passed forward:** The batch re-ranking architectural decision directly drove the reported performance improvements.

### Step 5 - End to End Quality (max 20)

**Instruction for this criterion:**

- _What strong work looks like:_ A strong solution completes a realistic and self contained execution and produces a final result the user can use, with the finish of something a person would sign their name to rather than an obvious AI generated draft.
- _Ask yourself:_ Would the intended user consider this output high quality, or does it read as clearly AI generated?

**Running notes inherited from earlier criteria:**
- (Problem & User Value) User and bottleneck framing are exceptionally clear and well-scoped for a 2-3 person startup team.
- (Agent Solution & Engineering) The batch re-ranking architectural decision directly drove the reported performance improvements.

**Output:**

- **Score:** 12 / 20
- **Confidence:** high
- **Rationale:** While the agent produces usable outputs in theory (a re-ranked ticket list with justifications), critical dependencies and configuration files required to run the pipeline are missing from the submission.
- **Evidence cited:**
- [FLAGGED] repro_paths_exist: The reproduction guide references 3 path(s) not present anywhere in the submission: ['requirements.txt', 'config/reranker.yaml', 'out/predictions.json'].
- **Note passed forward:** The lack of `config/reranker.yaml` prevents executing the command specified in the reproduction guide.

### Step 6 - Measured Improvement (max 15)

**Instruction for this criterion:**

- _What strong work looks like:_ A strong report demonstrates gains over a fair baseline and uses the changelog to connect each iteration with evidence.
- _Ask yourself:_ Which changes truly improved the outcome?

**Running notes inherited from earlier criteria:**
- (Problem & User Value) User and bottleneck framing are exceptionally clear and well-scoped for a 2-3 person startup team.
- (Agent Solution & Engineering) The batch re-ranking architectural decision directly drove the reported performance improvements.
- (End to End Quality) The lack of `config/reranker.yaml` prevents executing the command specified in the reproduction guide.

**Output:**

- **Score:** 13 / 15
- **Confidence:** high
- **Rationale:** The project clearly demonstrates a strong gain over a fair baseline, improving manual ranking agreement from 68% to 81% through batch-level re-ranking as tracked in the changelog. However, the final qualitative claim that justifications were rated 'useful' by 4/5 reviewers lacks supporting evidence in the repo.
- **Evidence cited:**
- data/manual_ranking.json
- README.md Improvement Changelog table
- [FLAGGED] claims_have_evidence: 1 claim(s) have no specific file/dataset a judge could check: ["Justifications per ticket were rated 'useful' by 4/5 reviewers"]
- **Note passed forward:** The quantitative gain from 68% to 81% agreement is well-documented and directly tied to the batch re-ranking step in the changelog.

### Step 7 - Reproducibility (max 15)

**Instruction for this criterion:**

- _What strong work looks like:_ A reproducible project gives another person a clear path to run the solution and baseline and reach the main result.
- _Ask yourself:_ Could they do it from a clean environment?

**Running notes inherited from earlier criteria:**
- (Problem & User Value) User and bottleneck framing are exceptionally clear and well-scoped for a 2-3 person startup team.
- (Agent Solution & Engineering) The batch re-ranking architectural decision directly drove the reported performance improvements.
- (End to End Quality) The lack of `config/reranker.yaml` prevents executing the command specified in the reproduction guide.
- (Measured Improvement) The quantitative gain from 68% to 81% agreement is well-documented and directly tied to the batch re-ranking step in the changelog.

**Output:**

- **Score:** 4 / 15
- **Confidence:** high
- **Rationale:** Although a clear reproduction guide is provided in REPRODUCE.md, execution fails from a clean environment because critical referenced files like requirements.txt and config/reranker.yaml are missing from the submission.
- **Evidence cited:**
- [FLAGGED] repro_paths_exist: The reproduction guide references 3 path(s) not present anywhere in the submission: ['requirements.txt', 'config/reranker.yaml', 'out/predictions.json'].
- **Note passed forward:** The missing config/reranker.yaml file blocks execution of the agent re-ranking script and evaluation step.

### Step 8 - Hot Take / Insights (max 5)

**Instruction for this criterion:**

- _What strong work looks like:_ A strong insight turns an observed failure mode into a practical lesson for building more reliable agents.
- _Ask yourself:_ What did you learn and how would it change what you build next?

**Running notes inherited from earlier criteria:**
- (Problem & User Value) User and bottleneck framing are exceptionally clear and well-scoped for a 2-3 person startup team.
- (Agent Solution & Engineering) The batch re-ranking architectural decision directly drove the reported performance improvements.
- (End to End Quality) The lack of `config/reranker.yaml` prevents executing the command specified in the reproduction guide.
- (Measured Improvement) The quantitative gain from 68% to 81% agreement is well-documented and directly tied to the batch re-ranking step in the changelog.
- (Reproducibility) The missing config/reranker.yaml file blocks execution of the agent re-ranking script and evaluation step.

**Output:**

- **Score:** 5 / 5
- **Confidence:** high
- **Rationale:** The hot take articulates a clear, non-generic architectural insight derived directly from their experiment: urgency is relative to queue state, so batch context outperforms individual ticket prompt engineering.
- **Evidence cited:**
- README.md: 'Scoring tickets independently throws away information — urgency is relative to what else is in the queue right now, not an absolute property of the ticket text. Batch context mattered more than better per-ticket prompting.'
- DETERMINISTIC VERIFICATION FLAGS: [OK] hot_take_grounded
- **Note passed forward:** _(none)_

## Final aggregation

- **Total (sum of the six specialist scores):** 72 / 100
- **Needs human attention:** True
- **Low-confidence criteria:** _(none)_
- **Failed verification checks:** `repro_paths_exist`, `claims_have_evidence`

**Accumulated review notes:**
- (Problem & User Value) User and bottleneck framing are exceptionally clear and well-scoped for a 2-3 person startup team.
- (Agent Solution & Engineering) The batch re-ranking architectural decision directly drove the reported performance improvements.
- (End to End Quality) The lack of `config/reranker.yaml` prevents executing the command specified in the reproduction guide.
- (Measured Improvement) The quantitative gain from 68% to 81% agreement is well-documented and directly tied to the batch re-ranking step in the changelog.
- (Reproducibility) The missing config/reranker.yaml file blocks execution of the agent re-ranking script and evaluation step.

> Advisory pre-screen only. Every score above is a starting point with cited evidence for a qualified human judge to confirm, adjust, or override -- this tool does not make a final accept/reject or prize decision.

---
