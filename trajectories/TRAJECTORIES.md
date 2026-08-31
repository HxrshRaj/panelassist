# PanelAssist agent trajectories

Representative end-to-end runs, rendered from `results/agent_scores.json` by `agent/render_trajectories.py`. Each section walks one submission from the instructions the agent was given to its final aggregated (advisory) score. The machine-readable form of every run is in `trajectories/panelassist_runs.json`.

**Rendered submissions:** `strong_baseline_done_right`, `fabricated_claims`, `broken_repro`, `overengineered_but_honest`

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
  "target_user": "Mara runs a 4-person support team at a mid-size SaaS company.",
  "bottleneck": "Triage is difficult at volume consistently without senior staff; junior agents under-flag urgency because they don't know phrases correlating with churn risk, resulting in mis-triaged tickets taking 3.1x longer time-to-first-response.",
  "agent_capabilities_used": [
    "tool_use",
    "verification",
    "human_checkpoint"
  ],
  "changelog_entries": [
    {
      "stage": "Baseline",
      "evidence": "61% urgency accuracy vs. our 40-ticket labeled set (eval/labels.csv)",
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
      "claim": "89% urgency accuracy (up from 61% baseline)",
      "has_supporting_evidence_file": true,
      "supporting_file": "eval/results.md"
    },
    {
      "claim": "P0/P1 recall increased from 71% to 96%",
      "has_supporting_evidence_file": true,
      "supporting_file": "eval/results.md"
    },
    {
      "claim": "Mis-triaged tickets have a 3.1x longer median time-to-first-response",
      "has_supporting_evidence_file": true,
      "supporting_file": "data/historical_triage_delay.csv"
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
  "hot_take_text": "The agent still misses tickets where urgency is implied by what's missing rather than what's said \u2014 e.g. a customer who used to email daily and has gone silent for a week after a billing dispute. Nothing in the ticket text itself is urgent-sounding. Our hot take: verification passes built to catch wrong tone won't catch wrong silence \u2014 if the real signal lives outside the artifact you're reviewing (ticket history, not ticket text), no amount of re-reading the same ticket harder will find it. The next version needs a tool call out to ticket history, not a better prompt.",
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
- **Rationale:** The submission identifies a highly specific target user (Mara, a support team lead at a mid-size SaaS company) and articulates a clear, quantified bottleneck (junior agents under-flagging urgency leading to a 3.1x response delay on mis-triaged tickets) with no identifiable weaknesses in problem definition or user value.
- **Evidence cited:**
- README.md: 'Mara runs a 4-person support team at a mid-size SaaS company.'
- README.md: 'the median time-to-first-response on tickets that were initially mis-triaged is 3.1x longer than tickets triaged correctly'
- data/historical_triage_delay.csv
- **Note passed forward:** The problem setup is grounded in a 40-ticket synthetic dataset, which judges evaluating evaluation rigor or dataset scale may wish to note.

### Step 4 - Agent Solution & Engineering (max 30)

**Instruction for this criterion:**

- _What strong work looks like:_ A strong solution uses agents purposefully and is technically sound. Better context or tools may improve one project, while memory, verification, skills or orchestration may improve another.
- _Ask yourself:_ Which design choices helped the agent solve the problem?

**Running notes inherited from earlier criteria:**
- (Problem & User Value) The problem setup is grounded in a 40-ticket synthetic dataset, which judges evaluating evaluation rigor or dataset scale may wish to note.

**Output:**

- **Score:** 25 / 30
- **Confidence:** high
- **Rationale:** The solution incorporates effective verification, low latency/cost, and human-in-the-loop safeguards, but deducts slightly because the agent flow is implemented as a rigid sequential script rather than dynamic tool invocation.
- **Evidence cited:**
- src/agent_triage.py
- src/verify_urgency.py
- Agent trajectory log steps 1-5
- **Note passed forward:** _(none)_

### Step 5 - End to End Quality (max 20)

**Instruction for this criterion:**

- _What strong work looks like:_ A strong solution completes a realistic and self contained execution and produces a final result the user can use, with the finish of something a person would sign their name to rather than an obvious AI generated draft.
- _Ask yourself:_ Would the intended user consider this output high quality, or does it read as clearly AI generated?

**Running notes inherited from earlier criteria:**
- (Problem & User Value) The problem setup is grounded in a 40-ticket synthetic dataset, which judges evaluating evaluation rigor or dataset scale may wish to note.

**Output:**

- **Score:** 17 / 20
- **Confidence:** high
- **Rationale:** The solution completes a fully functional, self-contained execution loop—incorporating automated classification, deterministic red-flag phrase verification (src/verify_urgency.py), response drafting, and a human approval gate. A single minor deduction is made because the execution quality is demonstrated only against a modest 40-ticket synthetic sample written by the creators.
- **Evidence cited:**
- REPRODUCE.md: 'data/tickets.jsonl — 40 synthetic support tickets we wrote ourselves'
- src/agent_triage.py
- Agent trajectory log steps 1-5
- **Note passed forward:** The integration of a human approval gate in step 5 directly addresses customer safety concerns before sending drafted responses.

### Step 6 - Measured Improvement (max 15)

**Instruction for this criterion:**

- _What strong work looks like:_ A strong report demonstrates gains over a fair baseline and uses the changelog to connect each iteration with evidence.
- _Ask yourself:_ Which changes truly improved the outcome?

**Running notes inherited from earlier criteria:**
- (Problem & User Value) The problem setup is grounded in a 40-ticket synthetic dataset, which judges evaluating evaluation rigor or dataset scale may wish to note.
- (End to End Quality) The integration of a human approval gate in step 5 directly addresses customer safety concerns before sending drafted responses.

**Output:**

- **Score:** 13 / 15
- **Confidence:** high
- **Rationale:** The submission excels at connecting iteration steps directly to quantitative metric changes, including explicitly removing an iteration that added cost without improvement (Iteration 3). A minor point deduction is applied because the gains are evaluated entirely on a small 40-ticket synthetic set, slightly weakening the statistical robustness of the claimed improvements.
- **Evidence cited:**
- README.md Improvement Changelog
- eval/labels.csv
- eval/results.md
- **Note passed forward:** The iteration log provides an exemplary model for showing rejected changes alongside successful ones.

### Step 7 - Reproducibility (max 15)

**Instruction for this criterion:**

- _What strong work looks like:_ A reproducible project gives another person a clear path to run the solution and baseline and reach the main result.
- _Ask yourself:_ Could they do it from a clean environment?

**Running notes inherited from earlier criteria:**
- (Problem & User Value) The problem setup is grounded in a 40-ticket synthetic dataset, which judges evaluating evaluation rigor or dataset scale may wish to note.
- (End to End Quality) The integration of a human approval gate in step 5 directly addresses customer safety concerns before sending drafted responses.
- (Measured Improvement) The iteration log provides an exemplary model for showing rejected changes alongside successful ones.

**Output:**

- **Score:** 15 / 15
- **Confidence:** high
- **Rationale:** The project provides exemplary reproduction documentation in REPRODUCE.md, including precise commands for setup, baseline, agent execution, and evaluation, along with cost/time estimates and all required files present in the repository.
- **Evidence cited:**
- REPRODUCE.md
- [OK] repro_paths_exist
- **Note passed forward:** _(none)_

### Step 8 - Hot Take / Insights (max 5)

**Instruction for this criterion:**

- _What strong work looks like:_ A strong insight turns an observed failure mode into a practical lesson for building more reliable agents.
- _Ask yourself:_ What did you learn and how would it change what you build next?

**Running notes inherited from earlier criteria:**
- (Problem & User Value) The problem setup is grounded in a 40-ticket synthetic dataset, which judges evaluating evaluation rigor or dataset scale may wish to note.
- (End to End Quality) The integration of a human approval gate in step 5 directly addresses customer safety concerns before sending drafted responses.
- (Measured Improvement) The iteration log provides an exemplary model for showing rejected changes alongside successful ones.

**Output:**

- **Score:** 5 / 5
- **Confidence:** high
- **Rationale:** The hot take is exemplary: it clearly identifies a subtle failure mode (signals of urgency missing from single-ticket text), derives a practical generalizable lesson ('re-reading the same ticket harder won't find signal outside the artifact'), and outlines a concrete architectural pivot for future versions.
- **Evidence cited:**
- README.md: 'Our hot take: verification passes built to catch wrong tone won't catch wrong silence — if the real signal lives outside the artifact you're reviewing (ticket history, not ticket text), no amount of re-reading the same ticket harder will find it.'
- Verification flag: [OK] hot_take_grounded
- **Note passed forward:** _(none)_

## Final aggregation

- **Total (sum of the six specialist scores):** 90 / 100
- **Needs human attention:** False
- **Low-confidence criteria:** _(none)_
- **Failed verification checks:** _(none)_

**Accumulated review notes:**
- (Problem & User Value) The problem setup is grounded in a 40-ticket synthetic dataset, which judges evaluating evaluation rigor or dataset scale may wish to note.
- (End to End Quality) The integration of a human approval gate in step 5 directly addresses customer safety concerns before sending drafted responses.
- (Measured Improvement) The iteration log provides an exemplary model for showing rejected changes alongside successful ones.

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
      "claim": "94.7% classification accuracy (+33% increase over 71% baseline)",
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
| `claims_have_evidence` | **FLAGGED** | 1 claim(s) have no specific file/dataset a judge could check: ['94.7% classification accuracy (+33% increase over 71% baseline)']. Per ground rule 9 ('connect every claim about your results to the evidence you submit'), these should not be taken at face value. |
| `hot_take_grounded` | **FLAGGED** | Hot take reads as generic AI-hype rather than a lesson tied to an observed failure in this specific project: "Multi-agent orchestration is clearly superior to single-prompt approaches. The data speaks for itself — more agents working together produces dramatically bette..." |

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

- **Score:** 13 / 15
- **Confidence:** high
- **Rationale:** The submission clearly defines a specific target user (Support operations leads at B2B companies processing >500 tickets/day) and a clear operational bottleneck (slow, inconsistent manual ticket triage). However, the stated financial magnitude ($2.3M lost annually) is asserted without supporting domain citations or user research.
- **Evidence cited:**
- README.md: 'Support operations leads at high-growth B2B companies lose an estimated $2.3M annually to mis-routed tickets and delayed escalations. Any team processing more than 500 tickets/day faces this exact bottleneck.'
- **Note passed forward:** The evaluation dataset and test results were intentionally omitted for confidentiality, which directly impacts evidence-backed accuracy claims.

### Step 4 - Agent Solution & Engineering (max 30)

**Instruction for this criterion:**

- _What strong work looks like:_ A strong solution uses agents purposefully and is technically sound. Better context or tools may improve one project, while memory, verification, skills or orchestration may improve another.
- _Ask yourself:_ Which design choices helped the agent solve the problem?

**Running notes inherited from earlier criteria:**
- (Problem & User Value) The evaluation dataset and test results were intentionally omitted for confidentiality, which directly impacts evidence-backed accuracy claims.

**Output:**

- **Score:** 17 / 30
- **Confidence:** high
- **Rationale:** Although the submission organizes agent roles into dedicated modules, the technical engineering is shallow. The pipeline relies on four static sequential prompts without tool integration or dynamic planning, and the QA verification step lacks rigorous checks.
- **Evidence cited:**
- Agent trajectory log step 2: 'Single LLM call per role; 'multi-agent' here means four sequential prompts, not four independently useful capabilities.'
- Agent trajectory log step 3: 'The QA step does not verify anything against ground truth or re-derived evidence -- it just re-asks the model if it's confident.'
- **Note passed forward:** The minimal verification layer and static sequential prompts support concerns regarding unverified accuracy gains.

### Step 5 - End to End Quality (max 20)

**Instruction for this criterion:**

- _What strong work looks like:_ A strong solution completes a realistic and self contained execution and produces a final result the user can use, with the finish of something a person would sign their name to rather than an obvious AI generated draft.
- _Ask yourself:_ Would the intended user consider this output high quality, or does it read as clearly AI generated?

**Running notes inherited from earlier criteria:**
- (Problem & User Value) The evaluation dataset and test results were intentionally omitted for confidentiality, which directly impacts evidence-backed accuracy claims.
- (Agent Solution & Engineering) The minimal verification layer and static sequential prompts support concerns regarding unverified accuracy gains.

**Output:**

- **Score:** 6 / 20
- **Confidence:** high
- **Rationale:** The submission fails to demonstrate end-to-end quality because evaluation outputs and sample ticket runs were omitted entirely, and the project documentation retains visible encoding glitches and generic AI claims.
- **Evidence cited:**
- REPRODUCE.md: 'the labeled evaluation set and per-ticket results are not included in this submission for confidentiality reasons'
- README.md: 'TriageX â€” enterprise-grade agentic support triage'
- [FLAGGED] claims_have_evidence: 1 claim(s) have no specific file/dataset a judge could check: ['94.7% classification accuracy (+33% increase over 71% baseline)']
- [FLAGGED] hot_take_grounded: Hot take reads as generic AI-hype rather than a lesson tied to an observed failure in this specific project
- **Note passed forward:** The missing evaluation dataset directly compromises end-to-end quality as there are no verifiable end-user outputs to review.

### Step 6 - Measured Improvement (max 15)

**Instruction for this criterion:**

- _What strong work looks like:_ A strong report demonstrates gains over a fair baseline and uses the changelog to connect each iteration with evidence.
- _Ask yourself:_ Which changes truly improved the outcome?

**Running notes inherited from earlier criteria:**
- (Problem & User Value) The evaluation dataset and test results were intentionally omitted for confidentiality, which directly impacts evidence-backed accuracy claims.
- (Agent Solution & Engineering) The minimal verification layer and static sequential prompts support concerns regarding unverified accuracy gains.
- (End to End Quality) The missing evaluation dataset directly compromises end-to-end quality as there are no verifiable end-user outputs to review.

**Output:**

- **Score:** 3 / 15
- **Confidence:** high
- **Rationale:** Although the submission lists an iteration changelog, all accuracy gains are purely claimed text with no evaluation scripts or test datasets submitted in the repo to verify them.
- **Evidence cited:**
- [FLAGGED] claims_have_evidence
- REPRODUCE.md: 'the labeled evaluation set and per-ticket results are not included in this submission for confidentiality reasons.'
- **Note passed forward:** The lack of evaluation dataset and test results directly undermines all reported quantitative accuracy improvements.

### Step 7 - Reproducibility (max 15)

**Instruction for this criterion:**

- _What strong work looks like:_ A reproducible project gives another person a clear path to run the solution and baseline and reach the main result.
- _Ask yourself:_ Could they do it from a clean environment?

**Running notes inherited from earlier criteria:**
- (Problem & User Value) The evaluation dataset and test results were intentionally omitted for confidentiality, which directly impacts evidence-backed accuracy claims.
- (Agent Solution & Engineering) The minimal verification layer and static sequential prompts support concerns regarding unverified accuracy gains.
- (End to End Quality) The missing evaluation dataset directly compromises end-to-end quality as there are no verifiable end-user outputs to review.
- (Measured Improvement) The lack of evaluation dataset and test results directly undermines all reported quantitative accuracy improvements.

**Output:**

- **Score:** 4 / 15
- **Confidence:** high
- **Rationale:** The criterion is largely unmet because a reviewer cannot reproduce the baseline or main accuracy findings from a clean environment. REPRODUCE.md explicitly notes that the evaluation set and test results were omitted for confidentiality reasons, leaving no dataset or test harness to replicate the claimed results.
- **Evidence cited:**
- REPRODUCE.md: 'Note: the 94.7% accuracy figure and the 500-ticket benchmark referenced in the README were measured internally; the labeled evaluation set and per-ticket results are not included in this submission for confidentiality reasons.'
- FLAGGED: claims_have_evidence (1 claim(s) have no specific file/dataset a judge could check: ['94.7% classification accuracy (+33% increase over 71% baseline)'])
- **Note passed forward:** The evaluation dataset and baseline execution scripts are completely absent from the repository.

### Step 8 - Hot Take / Insights (max 5)

**Instruction for this criterion:**

- _What strong work looks like:_ A strong insight turns an observed failure mode into a practical lesson for building more reliable agents.
- _Ask yourself:_ What did you learn and how would it change what you build next?

**Running notes inherited from earlier criteria:**
- (Problem & User Value) The evaluation dataset and test results were intentionally omitted for confidentiality, which directly impacts evidence-backed accuracy claims.
- (Agent Solution & Engineering) The minimal verification layer and static sequential prompts support concerns regarding unverified accuracy gains.
- (End to End Quality) The missing evaluation dataset directly compromises end-to-end quality as there are no verifiable end-user outputs to review.
- (Measured Improvement) The lack of evaluation dataset and test results directly undermines all reported quantitative accuracy improvements.
- (Reproducibility) The evaluation dataset and baseline execution scripts are completely absent from the repository.

**Output:**

- **Score:** 1 / 5
- **Confidence:** high
- **Rationale:** The hot take lacks any practical learning from failure modes, offering only generic AI hype that multi-agent systems are superior. This directly violates the criterion guidelines and triggers the deterministic verification flag for ungrounded hot takes.
- **Evidence cited:**
- [FLAGGED] hot_take_grounded
- README.md: 'Multi-agent orchestration is clearly superior to single-prompt approaches. The data speaks for itself — more agents working together produces dramatically better outcomes across the board.'
- **Note passed forward:** The submission offers no specific failure analysis or empirical insights from building the system.

## Final aggregation

- **Total (sum of the six specialist scores):** 44 / 100
- **Needs human attention:** True
- **Low-confidence criteria:** _(none)_
- **Failed verification checks:** `claims_have_evidence`, `hot_take_grounded`

**Accumulated review notes:**
- (Problem & User Value) The evaluation dataset and test results were intentionally omitted for confidentiality, which directly impacts evidence-backed accuracy claims.
- (Agent Solution & Engineering) The minimal verification layer and static sequential prompts support concerns regarding unverified accuracy gains.
- (End to End Quality) The missing evaluation dataset directly compromises end-to-end quality as there are no verifiable end-user outputs to review.
- (Measured Improvement) The lack of evaluation dataset and test results directly undermines all reported quantitative accuracy improvements.
- (Reproducibility) The evaluation dataset and baseline execution scripts are completely absent from the repository.
- (Hot Take / Insights) The submission offers no specific failure analysis or empirical insights from building the system.

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
  "target_user": "Small support teams (2-3 people) at early-stage startups who can't justify buying a full helpdesk platform yet",
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
      "claim": "Batch-level re-ranking achieved 81% agreement with manual ranking",
      "has_supporting_evidence_file": true,
      "supporting_file": "data/manual_ranking.json"
    },
    {
      "claim": "Justifications rated 'useful' by 4/5 reviewers",
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
| `claims_have_evidence` | **FLAGGED** | 1 claim(s) have no specific file/dataset a judge could check: ["Justifications rated 'useful' by 4/5 reviewers"]. Per ground rule 9 ('connect every claim about your results to the evidence you submit'), these should not be taken at face value. |
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
- **Rationale:** The submission clearly defines a specific target user (2-3 person support teams at early-stage startups) and a concrete, impactful bottleneck (FIFO ticket ordering causing urgent churn-risk tickets to sit behind routine requests). No weaknesses were identified for this criterion.
- **Evidence cited:**
- README.md: 'Small support teams (2-3 people) at early-stage startups who can't justify buying a full helpdesk platform yet'
- README.md: 'Without any tooling, a 2-person team just replies to tickets in the order they arrive, which means an angry churn-risk ticket can sit behind five routine password resets for hours.'
- **Note passed forward:** _(none)_

### Step 4 - Agent Solution & Engineering (max 30)

**Instruction for this criterion:**

- _What strong work looks like:_ A strong solution uses agents purposefully and is technically sound. Better context or tools may improve one project, while memory, verification, skills or orchestration may improve another.
- _Ask yourself:_ Which design choices helped the agent solve the problem?

**Running notes inherited from earlier criteria:**
_(none)_

**Output:**

- **Score:** 21 / 30
- **Confidence:** high
- **Rationale:** The design choice to use batch context rather than per-ticket isolated scoring is purposeful and well-motivated for relative ticket urgency. However, points were deducted because the required 'config/reranker.yaml' file is missing from the submission repo, and the agent framework remains minimal with no verification or dynamic tools.
- **Evidence cited:**
- FLAGGED repro_paths_exist: The reproduction guide references 3 path(s) not present anywhere in the submission: ['requirements.txt', 'config/reranker.yaml', 'out/predictions.json']
- REPRODUCE.md: python agent/batch_reranker.py --input data/batch1.json --config config/reranker.yaml
- Agent trajectory log: step 1 (score_each_ticket_independently) -> step 2 (batch_rerank_with_full_context)
- **Note passed forward:** The missing configuration file config/reranker.yaml prevents executing the agent script per REPRODUCE.md instructions.

### Step 5 - End to End Quality (max 20)

**Instruction for this criterion:**

- _What strong work looks like:_ A strong solution completes a realistic and self contained execution and produces a final result the user can use, with the finish of something a person would sign their name to rather than an obvious AI generated draft.
- _Ask yourself:_ Would the intended user consider this output high quality, or does it read as clearly AI generated?

**Running notes inherited from earlier criteria:**
- (Agent Solution & Engineering) The missing configuration file config/reranker.yaml prevents executing the agent script per REPRODUCE.md instructions.

**Output:**

- **Score:** 6 / 20
- **Confidence:** high
- **Rationale:** End to End Quality is largely unmet because key execution dependencies like 'config/reranker.yaml' are missing from the repository listing, making it impossible to complete a clean execution of the agent script. Furthermore, no sample output predictions or saved justifications are provided to evaluate if the end result is something a user could directly consume.
- **Evidence cited:**
- [FLAGGED] repro_paths_exist: The reproduction guide references 3 path(s) not present anywhere in the submission: ['requirements.txt', 'config/reranker.yaml', 'out/predictions.json'].
- **Note passed forward:** The missing configuration file config/reranker.yaml prevents running the agent script as documented in REPRODUCE.md.

### Step 6 - Measured Improvement (max 15)

**Instruction for this criterion:**

- _What strong work looks like:_ A strong report demonstrates gains over a fair baseline and uses the changelog to connect each iteration with evidence.
- _Ask yourself:_ Which changes truly improved the outcome?

**Running notes inherited from earlier criteria:**
- (Agent Solution & Engineering) The missing configuration file config/reranker.yaml prevents executing the agent script per REPRODUCE.md instructions.
- (End to End Quality) The missing configuration file config/reranker.yaml prevents running the agent script as documented in REPRODUCE.md.

**Output:**

- **Score:** 9 / 15
- **Confidence:** high
- **Rationale:** While the project presents a clear baseline and iterative improvement from 68% to 81% agreement using batch re-ranking, the qualitative human evaluation claim is unsupported by files and the evaluation code cannot be run to verify results.
- **Evidence cited:**
- FLAGGED claims_have_evidence: 1 claim(s) have no specific file/dataset a judge could check: ["Justifications rated 'useful' by 4/5 reviewers"]
- FLAGGED repro_paths_exist: The reproduction guide references 3 path(s) not present anywhere in the submission: ['requirements.txt', 'config/reranker.yaml', 'out/predictions.json']
- === README.md === Improvement Changelog
- **Note passed forward:** _(none)_

### Step 7 - Reproducibility (max 15)

**Instruction for this criterion:**

- _What strong work looks like:_ A reproducible project gives another person a clear path to run the solution and baseline and reach the main result.
- _Ask yourself:_ Could they do it from a clean environment?

**Running notes inherited from earlier criteria:**
- (Agent Solution & Engineering) The missing configuration file config/reranker.yaml prevents executing the agent script per REPRODUCE.md instructions.
- (End to End Quality) The missing configuration file config/reranker.yaml prevents running the agent script as documented in REPRODUCE.md.

**Output:**

- **Score:** 4 / 15
- **Confidence:** high
- **Rationale:** A judge attempting to reproduce the submission from a clean environment cannot install dependencies or run the agent script due to missing referenced files (`requirements.txt` and `config/reranker.yaml`). Per rubric rules, severe failure in runnable paths triggers the <35% score band.
- **Evidence cited:**
- [FLAGGED] repro_paths_exist: The reproduction guide references 3 path(s) not present anywhere in the submission: ['requirements.txt', 'config/reranker.yaml', 'out/predictions.json'].
- REPRODUCE.md: pip install -r requirements.txt
- REPRODUCE.md: python agent/batch_reranker.py --input data/batch1.json --config config/reranker.yaml
- **Note passed forward:** Reproducibility fails immediately at setup due to missing requirements.txt and config/reranker.yaml.

### Step 8 - Hot Take / Insights (max 5)

**Instruction for this criterion:**

- _What strong work looks like:_ A strong insight turns an observed failure mode into a practical lesson for building more reliable agents.
- _Ask yourself:_ What did you learn and how would it change what you build next?

**Running notes inherited from earlier criteria:**
- (Agent Solution & Engineering) The missing configuration file config/reranker.yaml prevents executing the agent script per REPRODUCE.md instructions.
- (End to End Quality) The missing configuration file config/reranker.yaml prevents running the agent script as documented in REPRODUCE.md.
- (Reproducibility) Reproducibility fails immediately at setup due to missing requirements.txt and config/reranker.yaml.

**Output:**

- **Score:** 5 / 5
- **Confidence:** high
- **Rationale:** The hot take offers a sharp, practical lesson directly tied to the experiment's findings, highlighting that ticket urgency is relative to queue context rather than an absolute property of individual ticket text.
- **Evidence cited:**
- README.md: 'Scoring tickets independently throws away information — urgency is relative to what else is in the queue right now, not an absolute property of the ticket text. Batch context mattered more than better per-ticket prompting.'
- **Note passed forward:** _(none)_

## Final aggregation

- **Total (sum of the six specialist scores):** 60 / 100
- **Needs human attention:** True
- **Low-confidence criteria:** _(none)_
- **Failed verification checks:** `repro_paths_exist`, `claims_have_evidence`

**Accumulated review notes:**
- (Agent Solution & Engineering) The missing configuration file config/reranker.yaml prevents executing the agent script per REPRODUCE.md instructions.
- (End to End Quality) The missing configuration file config/reranker.yaml prevents running the agent script as documented in REPRODUCE.md.
- (Reproducibility) Reproducibility fails immediately at setup due to missing requirements.txt and config/reranker.yaml.

> Advisory pre-screen only. Every score above is a starting point with cited evidence for a qualified human judge to confirm, adjust, or override -- this tool does not make a final accept/reject or prize decision.

---

# Trajectory - `overengineered_but_honest`

PanelAssist processes one submission as a fixed pipeline: **1** evidence extraction call, **1** deterministic verification pass (no LLM), then **6** specialist scoring calls (one per rubric criterion) that share the evidence ledger and a running set of notes. Nothing below is a final decision -- see the disclaimer at the end.

## Input given to the agent

- **Submission:** `overengineered_but_honest`
- **Files the agent was told exist in the submission:**
- requirements.txt
- baseline/one_shot_rank.py
- src/grantmatch.py
- src/call_parser.py
- src/faculty_researcher.py
- src/matcher.py
- src/checker.py
- data/calls/
- data/calls/SOURCES.md
- data/faculty.json
- eval/officer_rankings.json
- eval/score.py
- eval/results.md
- results/baseline.json
- results/agent.json
- results/agent_trace/

## Step 1 - Evidence extraction (1 LLM call)

**Instruction (system prompt):**

> You extract structured facts from a hackathon submission. Be literal and skeptical: only mark a claim as evidence-backed if the submission actually points to a specific file, dataset, script, or trajectory step that would let someone verify it. Confident wording is not evidence.

**Task:** read README + REPRODUCE.md + file listing + trajectory log and return one structured *evidence ledger* - target user, bottleneck, which agent capabilities the submission actually uses, every headline claim plus whether a specific checkable file backs it, every path/env-var the reproduction guide references, and whether the hot take is grounded.

**Output - the evidence ledger (reused by every step below):**

```json
{
  "target_user": "Research-development officers at small university departments",
  "bottleneck": "A funding call is 3-8 pages of eligibility rules, scope language, and priorities. Matching it to a faculty member means holding the call's constraints in your head while reading someone's publication list and deciding whether the fit is real or superficial. It's a comparison task across two long, messy documents, done 60 times per call, and the officer's attention degrades after the first fifteen.",
  "agent_capabilities_used": [
    "verification",
    "orchestration",
    "human_checkpoint"
  ],
  "changelog_entries": [
    {
      "stage": "Baseline",
      "evidence": "0.58 nDCG@10 vs. the officer's own ranking on 8 past calls (`eval/officer_rankings.json`)",
      "decision": "Starting point"
    },
    {
      "stage": "Iteration 1",
      "evidence": "0.64 nDCG@10; hard-constraint violations in the top 10 went 1.4 -> 0.5 per call",
      "decision": "Kept"
    },
    {
      "stage": "Iteration 2",
      "evidence": "0.71 nDCG@10",
      "decision": "Kept"
    },
    {
      "stage": "Iteration 3",
      "evidence": "0.76 nDCG@10; \"unsupported reason\" rate in top 10 fell from 22% to 6%",
      "decision": "Kept"
    },
    {
      "stage": "Iteration 4 (removed)",
      "evidence": "No nDCG change (0.76 -> 0.76), +35% cost, and it mostly re-surfaced candidates the checker then re-demoted",
      "decision": "Removed - it added a loop, not information"
    },
    {
      "stage": "Final",
      "evidence": "0.76 nDCG@10, 0.5 hard-constraint violations/call, ~$0.14 per call, ~3 min",
      "decision": "-"
    }
  ],
  "claimed_results": [
    {
      "claim": "nDCG@10 vs. officer ranking improved from 0.58 (baseline) to 0.76 (GrantMatch) across 8 calls",
      "has_supporting_evidence_file": true,
      "supporting_file": "eval/officer_rankings.json"
    },
    {
      "claim": "Hard-constraint violations in top 10 reduced from 1.4 to 0.5 per call",
      "has_supporting_evidence_file": true,
      "supporting_file": "eval/score.py"
    },
    {
      "claim": "Unsupported fit reasons in top 10 reduced from 22% to 6%",
      "has_supporting_evidence_file": true,
      "supporting_file": "eval/score.py"
    }
  ],
  "repro_referenced_paths": [
    "requirements.txt",
    "baseline/one_shot_rank.py",
    "data/calls/",
    "data/faculty.json",
    "results/baseline.json",
    "src/grantmatch.py",
    "results/agent.json",
    "eval/score.py",
    "eval/officer_rankings.json",
    "eval/results.md",
    "data/calls/SOURCES.md"
  ],
  "repro_referenced_env_vars": [
    "ANTHROPIC_API_KEY"
  ],
  "hot_take_text": "The remaining errors are near-misses on interdisciplinary faculty: someone whose work genuinely spans two areas gets a middling score in both instead of a high score for the combination, because each step evaluates fit one dimension at a time. The checker doesn't help here - the reason is supported, it's just underweight. Hot take: every agent in this pipeline had to earn its place in the metric, not the diagram. Three of the four steps moved nDCG or the constraint-violation count; the fourth (the removed advocate) moved neither and we cut it even though it made the architecture diagram look more thorough. The lesson we're taking forward: add the step, measure, and be willing to delete it the same day if the number doesn't move - 'it seems like it should help' is how you end up paying 35% more for a loop.",
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

- **Score:** 14 / 15
- **Confidence:** high
- **Rationale:** calculated deduction for using synthetic faculty profiles instead of live department data. Otherwise, the project defines an extremely clear, real-world user persona and concrete bottleneck with high impact.
- **Evidence cited:**
- README.md: 'Research-development officers at small university departments.'
- README.md: 'The officer we worked with spends about 90 minutes per call cross-referencing the call text against faculty pages and past awards.'
- REPRODUCE.md: 'data/faculty.json - 60 synthetic faculty profiles we generated'
- **Note passed forward:** The submission highlights high human-in-the-loop control with an explicitly defined officer review step in the workflow trace.

### Step 4 - Agent Solution & Engineering (max 30)

**Instruction for this criterion:**

- _What strong work looks like:_ A strong solution uses agents purposefully and is technically sound. Better context or tools may improve one project, while memory, verification, skills or orchestration may improve another.
- _Ask yourself:_ Which design choices helped the agent solve the problem?

**Running notes inherited from earlier criteria:**
- (Problem & User Value) The submission highlights high human-in-the-loop control with an explicitly defined officer review step in the workflow trace.

**Output:**

- **Score:** 26 / 30
- **Confidence:** high
- **Rationale:** GrantMatch demonstrates strong engineering with a purposeful four-agent pipeline (parser, researcher, matcher, checker) featuring verification and explicit human-in-the-loop checkpoints. A minor weakness is the reliance on a fixed sequential workflow that evaluates candidates independently along isolated dimensions, limiting its ability to resolve complex interdisciplinary fits.
- **Evidence cited:**
- README.md: 'The remaining errors are near-misses on interdisciplinary faculty... because each step evaluates fit one dimension at a time.'
- Agent trajectory log: steps 1-5 detail a static pipeline (call_parser -> faculty_researcher -> matcher -> checker).
- **Note passed forward:** The iteration log shows exemplary engineering discipline by pruning an ineffective 5th agent (advocate) after empirical testing.

### Step 5 - End to End Quality (max 20)

**Instruction for this criterion:**

- _What strong work looks like:_ A strong solution completes a realistic and self contained execution and produces a final result the user can use, with the finish of something a person would sign their name to rather than an obvious AI generated draft.
- _Ask yourself:_ Would the intended user consider this output high quality, or does it read as clearly AI generated?

**Running notes inherited from earlier criteria:**
- (Problem & User Value) The submission highlights high human-in-the-loop control with an explicitly defined officer review step in the workflow trace.
- (Agent Solution & Engineering) The iteration log shows exemplary engineering discipline by pruning an ineffective 5th agent (advocate) after empirical testing.

**Output:**

- **Score:** 17 / 20
- **Confidence:** high
- **Rationale:** The pipeline delivers a complete, highly practical, and self-contained workflow that generates clean, actionable shortlists (`shortlist.md`) with explicit verification checks and reasonings tailored directly for research-development officers. A minor deduction is made because the output degrades on interdisciplinary candidates, who receive suboptimal rankings due to single-dimension scoring logic.
- **Evidence cited:**
- README.md: 'The remaining errors are near-misses on interdisciplinary faculty: someone whose work genuinely spans two areas gets a middling score in both instead of a high score for the combination, because each step evaluates fit one dimension at a time.'
- **Note passed forward:** _(none)_

### Step 6 - Measured Improvement (max 15)

**Instruction for this criterion:**

- _What strong work looks like:_ A strong report demonstrates gains over a fair baseline and uses the changelog to connect each iteration with evidence.
- _Ask yourself:_ Which changes truly improved the outcome?

**Running notes inherited from earlier criteria:**
- (Problem & User Value) The submission highlights high human-in-the-loop control with an explicitly defined officer review step in the workflow trace.
- (Agent Solution & Engineering) The iteration log shows exemplary engineering discipline by pruning an ineffective 5th agent (advocate) after empirical testing.

**Output:**

- **Score:** 15 / 15
- **Confidence:** high
- **Rationale:** The submission provides an exemplary evaluation with a fair baseline, granular iteration tracking across multiple quantitative metrics (nDCG@10, hard-constraint violations, unsupported reason rate), full trade-off reporting (cost and latency), and empirical justification for removing an unproductive agent step.
- **Evidence cited:**
- eval/officer_rankings.json
- eval/score.py
- README.md (Improvement Changelog)
- **Note passed forward:** _(none)_

### Step 7 - Reproducibility (max 15)

**Instruction for this criterion:**

- _What strong work looks like:_ A reproducible project gives another person a clear path to run the solution and baseline and reach the main result.
- _Ask yourself:_ Could they do it from a clean environment?

**Running notes inherited from earlier criteria:**
- (Problem & User Value) The submission highlights high human-in-the-loop control with an explicitly defined officer review step in the workflow trace.
- (Agent Solution & Engineering) The iteration log shows exemplary engineering discipline by pruning an ineffective 5th agent (advocate) after empirical testing.

**Output:**

- **Score:** 15 / 15
- **Confidence:** high
- **Rationale:** The submission provides an exemplary, complete reproduction guide in REPRODUCE.md, including exact environment dependencies, cost/runtime expectations, clean step-by-step commands for running the baseline, agent, and evaluation script, and all referenced files and paths exist.
- **Evidence cited:**
- REPRODUCE.md
- [OK] repro_paths_exist
- [OK] env_var_consistency
- [OK] claims_have_evidence
- **Note passed forward:** _(none)_

### Step 8 - Hot Take / Insights (max 5)

**Instruction for this criterion:**

- _What strong work looks like:_ A strong insight turns an observed failure mode into a practical lesson for building more reliable agents.
- _Ask yourself:_ What did you learn and how would it change what you build next?

**Running notes inherited from earlier criteria:**
- (Problem & User Value) The submission highlights high human-in-the-loop control with an explicitly defined officer review step in the workflow trace.
- (Agent Solution & Engineering) The iteration log shows exemplary engineering discipline by pruning an ineffective 5th agent (advocate) after empirical testing.

**Output:**

- **Score:** 5 / 5
- **Confidence:** high
- **Rationale:** The submission articulates an exemplary insight grounded in empirical observation: analyzing why interdisciplinary faculty are mis-scored and deriving a concrete architectural rule that every agent step must empirically move metrics rather than just populate architecture diagrams.
- **Evidence cited:**
- README.md: 'Hot take: every agent in this pipeline had to earn its place in the metric, not the diagram.'
- README.md: 'The remaining errors are near-misses on interdisciplinary faculty... because each step evaluates fit one dimension at a time.'
- DETERMINISTIC VERIFICATION FLAGS: [OK] hot_take_grounded
- **Note passed forward:** The pruning of the 5th 'advocate' agent (Iteration 4) serves as both an iteration win and the basis for a strong hot take.

## Final aggregation

- **Total (sum of the six specialist scores):** 92 / 100
- **Needs human attention:** False
- **Low-confidence criteria:** _(none)_
- **Failed verification checks:** _(none)_

**Accumulated review notes:**
- (Problem & User Value) The submission highlights high human-in-the-loop control with an explicitly defined officer review step in the workflow trace.
- (Agent Solution & Engineering) The iteration log shows exemplary engineering discipline by pruning an ineffective 5th agent (advocate) after empirical testing.
- (Hot Take / Insights) The pruning of the 5th 'advocate' agent (Iteration 4) serves as both an iteration win and the basis for a strong hot take.

> Advisory pre-screen only. Every score above is a starting point with cited evidence for a qualified human judge to confirm, adjust, or override -- this tool does not make a final accept/reject or prize decision.

---
