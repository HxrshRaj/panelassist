# PanelAssist agent trajectories

Representative end-to-end runs, rendered from `results/agent_scores.json` by `agent/render_trajectories.py`. Each section walks one submission from the instructions the agent was given to its final aggregated (advisory) score. The machine-readable form of every run is in `trajectories/panelassist_runs.json`.

**Rendered submissions:** `panelassist_self`

---

# Trajectory - `panelassist_self`

PanelAssist processes one submission as a fixed pipeline: **1** evidence extraction call, **1** deterministic verification pass (no LLM), then **6** specialist scoring calls (one per rubric criterion) that share the evidence ledger and a running set of notes. Nothing below is a final decision -- see the disclaimer at the end.

## Input given to the agent

- **Submission:** `panelassist_self`
- **Files the agent was told exist in the submission:**
- .gitignore
- HANDOFF_PROMPT.md
- README.md
- REPRODUCE.md
- VIDEO_SCRIPT.md
- agent/panelassist/ablations.py
- agent/panelassist/extract.py
- agent/panelassist/memory.py
- agent/panelassist/orchestrate.py
- agent/panelassist/score.py
- agent/panelassist/verify.py
- agent/panelassist/verify_llm.py
- agent/render_trajectories.py
- agent/run_agent.py
- baseline/baseline_scorer.py
- common/llm.py
- common/loader.py
- common/stats.py
- data/human_scores.json
- data/submissions/broken_repro/README.md
- data/submissions/broken_repro/REPRODUCE.md
- data/submissions/broken_repro/manifest.json
- data/submissions/broken_repro/trajectory.json
- data/submissions/cosmetic_orchestration/README.md
- data/submissions/cosmetic_orchestration/REPRODUCE.md
- data/submissions/cosmetic_orchestration/manifest.json
- data/submissions/cosmetic_orchestration/trajectory.json
- data/submissions/fabricated_claims/README.md
- data/submissions/fabricated_claims/REPRODUCE.md
- data/submissions/fabricated_claims/manifest.json
- data/submissions/fabricated_claims/trajectory.json
- data/submissions/good_project_bad_writeup/README.md
- data/submissions/good_project_bad_writeup/REPRODUCE.md
- data/submissions/good_project_bad_writeup/manifest.json
- data/submissions/good_project_bad_writeup/trajectory.json
- data/submissions/overengineered_but_honest/README.md
- data/submissions/overengineered_but_honest/REPRODUCE.md
- data/submissions/overengineered_but_honest/manifest.json
- data/submissions/overengineered_but_honest/trajectory.json
- data/submissions/real_gains_no_changelog/README.md
- data/submissions/real_gains_no_changelog/REPRODUCE.md
- data/submissions/real_gains_no_changelog/manifest.json
- data/submissions/real_gains_no_changelog/trajectory.json
- data/submissions/scope_mismatch/README.md
- data/submissions/scope_mismatch/REPRODUCE.md
- data/submissions/scope_mismatch/manifest.json
- data/submissions/scope_mismatch/trajectory.json
- data/submissions/strong_baseline_done_right/README.md
- data/submissions/strong_baseline_done_right/REPRODUCE.md
- data/submissions/strong_baseline_done_right/manifest.json
- data/submissions/strong_baseline_done_right/trajectory.json
- data/submissions/thin_hot_take/README.md
- data/submissions/thin_hot_take/REPRODUCE.md
- data/submissions/thin_hot_take/manifest.json
- data/submissions/thin_hot_take/trajectory.json
- data/submissions/weak_single_prompt/README.md
- data/submissions/weak_single_prompt/REPRODUCE.md
- data/submissions/weak_single_prompt/manifest.json
- data/submissions/weak_single_prompt/trajectory.json
- dogfood/panelassist_self/manifest.json
- dogfood/panelassist_self/trajectory.json
- eval/ABLATIONS.md
- eval/REMOVED_EXPERIMENT.md
- eval/RESULTS.md
- eval/results.json
- eval/run_ablation.py
- eval/run_eval.py
- eval/run_removed_experiment.py
- requirements.txt
- results/agent_scores.json
- results/baseline_scores.json
- results/dogfood_scores.json
- rubric.py
- trajectories/DOGFOOD_TRAJECTORY.md
- trajectories/TRAJECTORIES.md
- trajectories/dogfood_runs.json
- trajectories/panelassist_runs.json

## Step 1 - Evidence extraction (1 LLM call)

**Instruction (system prompt):**

> You extract structured facts from a hackathon submission. Be literal and skeptical: only mark a claim as evidence-backed if the submission actually points to a specific file, dataset, script, or trajectory step that would let someone verify it. Confident wording is not evidence.

**Task:** read README + REPRODUCE.md + file listing + trajectory log and return one structured *evidence ledger* - target user, bottleneck, which agent capabilities the submission actually uses, every headline claim plus whether a specific checkable file backs it, every path/env-var the reproduction guide references, and whether the hot take is grounded.

**Output - the evidence ledger (reused by every step below):**

```json
{
  "target_user": "micro1 hackathon judge",
  "bottleneck": "A tired judge under time pressure, scoring their fortieth submission of the day, easily slips past a confidently-worded but evidence-free submission because nothing forces checking claims against specific files.",
  "agent_capabilities_used": [
    "verification",
    "memory",
    "orchestration",
    "human_checkpoint"
  ],
  "changelog_entries": [
    {
      "stage": "Baseline",
      "evidence": "single prompt, raw submission text",
      "decision": "starting point (MAE 11.2, Spearman 0.857)"
    },
    {
      "stage": "+ Evidence ledger",
      "evidence": "still one combined call, but scoring from the extracted ledger instead of raw text",
      "decision": "mixed - MAE slightly worse (12.2) as ledger compresses nuance, but rank correlation improves (0.893)"
    },
    {
      "stage": "+ Specialist split",
      "evidence": "one call per criterion with a strict 'deduct from full marks for a named weakness' prompt, shared ledger + running memory, verification still off",
      "decision": "returns MAE to baseline (11.2, Spearman 0.894) - splitting job and forcing deductions undoes ledger cost but does not beat single prompt alone"
    },
    {
      "stage": "+ Verification (final)",
      "evidence": "the deterministic flags are passed to the specialist calls, which are told to treat any FLAGGED result as a real deduction",
      "decision": "kept - the change that matters (-3.4 MAE to 7.8, Spearman 0.875) and the only thing that catches the 3 seeded defects"
    }
  ],
  "claimed_results": [
    {
      "claim": "Total-score MAE vs. human improved from 11.2 (baseline) to 7.8 (PanelAssist)",
      "has_supporting_evidence_file": true,
      "supporting_file": "eval/RESULTS.md"
    },
    {
      "claim": "Spearman rank correlation vs. human of 0.875",
      "has_supporting_evidence_file": true,
      "supporting_file": "eval/RESULTS.md"
    },
    {
      "claim": "Seeded-issue recall of 1.00 (3/3) with 1.00 precision (0 false alarms)",
      "has_supporting_evidence_file": true,
      "supporting_file": "eval/RESULTS.md"
    },
    {
      "claim": "Produced 148 structured evidence citations across 10 submissions",
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
  "hot_take_text": "I expected the six specialist scoring calls to be the win. They were not - the ablation shows the bare split scoring no better than one holistic prompt, and the evidence-ledger step actively trading calibration for ranking. What put the pipeline ahead was the least glamorous component: a pure-Python pass that checks whether a claim names a file and whether the repro paths exist, plus a scoring instruction that forces the deduction when a flag fires. An LLM judge - one call or seven - is bad at not looking: it reads a confident submission and scores the confidence. You do not fix that with more judge calls. You fix it with a deterministic check that runs every time, and a rule that the check's output is a subtraction, not a footnote. Add the cheap check before you add the sixth model call.",
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
- **Rationale:** The project identifies a clear, highly specific target user (micro1 hackathon judges) and articulates a precise bottleneck (tired judges slipping past evidence-free submissions under time pressure). No concrete weakness can be named for this criterion.
- **Evidence cited:**
- README.md: 'The user is a micro1 hackathon judge. This challenge alone drew 8,300+ registrations... The bottleneck is not "reading takes time" - it is that a tired judge under time pressure, scoring their fortieth submission of the day, is exactly who a confidently-worded but evidence-free submission slips past.'
- **Note passed forward:** The target user is a hackathon judge, and the system acts as an advisory pre-screener rather than taking autonomous actions.

### Step 4 - Agent Solution & Engineering (max 30)

**Instruction for this criterion:**

- _What strong work looks like:_ A strong solution uses agents purposefully and is technically sound. Better context or tools may improve one project, while memory, verification, skills or orchestration may improve another.
- _Ask yourself:_ Which design choices helped the agent solve the problem?

**Running notes inherited from earlier criteria:**
- (Problem & User Value) The target user is a hackathon judge, and the system acts as an advisory pre-screener rather than taking autonomous actions.

**Output:**

- **Score:** 25 / 30
- **Confidence:** high
- **Rationale:** The solution demonstrates sound engineering with thoughtful memory passing (`agent/panelassist/memory.py`), structured ledger extraction, and seamless integration of deterministic verification into LLM prompts. Points were deducted because the core agent design choice (splitting into 6 sequential specialist calls) adds significant cost and latency while contributing no measurable performance gain over the baseline on its own (Specialist split MAE 11.2 vs Baseline MAE 11.2), with gains driven almost exclusively by the non-LLM Python verification pass.
- **Evidence cited:**
- README.md: 'the ablation shows the bare split scoring no better than one holistic prompt'
- eval/ABLATIONS.md: Stage '+ Specialist split' MAE 11.2 (identical to Baseline 11.2)
- agent/panelassist/orchestrate.py
- **Note passed forward:** The multi-agent specialist split was shown by ablation to add cost/latency without raw LLM scoring improvements prior to adding deterministic flags.

### Step 5 - End to End Quality (max 20)

**Instruction for this criterion:**

- _What strong work looks like:_ A strong solution completes a realistic and self contained execution and produces a final result the user can use, with the finish of something a person would sign their name to rather than an obvious AI generated draft.
- _Ask yourself:_ Would the intended user consider this output high quality, or does it read as clearly AI generated?

**Running notes inherited from earlier criteria:**
- (Problem & User Value) The target user is a hackathon judge, and the system acts as an advisory pre-screener rather than taking autonomous actions.
- (Agent Solution & Engineering) The multi-agent specialist split was shown by ablation to add cost/latency without raw LLM scoring improvements prior to adding deterministic flags.

**Output:**

- **Score:** 19 / 20
- **Confidence:** high
- **Rationale:** The submission executes a complete, highly realistic end-to-end pre-screening workflow and produces clean, usable advisory reports and trajectory outputs. The finish and voice of the documentation and output reports are exemplary and authentic, with only a minor deduction for presenting final outputs as static Markdown/JSON files rather than through a dedicated interactive judge interface.
- **Evidence cited:**
- README.md: 'hands a human judge an advisory report with cited evidence per score.'
- agent/run_agent.py -> results/agent_scores.json
- trajectories/DOGFOOD_TRAJECTORY.md
- eval/RESULTS.md
- **Note passed forward:** The solution outputs well-formatted, complete advisory reports and markdown trajectories that are immediately useful to human judges.

### Step 6 - Measured Improvement (max 15)

**Instruction for this criterion:**

- _What strong work looks like:_ A strong report demonstrates gains over a fair baseline and uses the changelog to connect each iteration with evidence.
- _Ask yourself:_ Which changes truly improved the outcome?

**Running notes inherited from earlier criteria:**
- (Problem & User Value) The target user is a hackathon judge, and the system acts as an advisory pre-screener rather than taking autonomous actions.
- (Agent Solution & Engineering) The multi-agent specialist split was shown by ablation to add cost/latency without raw LLM scoring improvements prior to adding deterministic flags.
- (End to End Quality) The solution outputs well-formatted, complete advisory reports and markdown trajectories that are immediately useful to human judges.

**Output:**

- **Score:** 15 / 15
- **Confidence:** high
- **Rationale:** The submission provides an exemplary, evidence-backed iteration changelog against a fair single-prompt baseline, demonstrating an MAE reduction from 11.2 to 7.8 and candidly identifying which pipeline changes truly drove gains versus those that added cost without benefit.
- **Evidence cited:**
- README.md: 'Improvement Changelog'
- eval/ABLATIONS.md
- eval/RESULTS.md
- **Note passed forward:** Ablation results confirm that deterministic verification flags provided the -3.4 MAE improvement over the baseline, whereas the specialist prompt split alone provided no MAE gain.

### Step 7 - Reproducibility (max 15)

**Instruction for this criterion:**

- _What strong work looks like:_ A reproducible project gives another person a clear path to run the solution and baseline and reach the main result.
- _Ask yourself:_ Could they do it from a clean environment?

**Running notes inherited from earlier criteria:**
- (Problem & User Value) The target user is a hackathon judge, and the system acts as an advisory pre-screener rather than taking autonomous actions.
- (Agent Solution & Engineering) The multi-agent specialist split was shown by ablation to add cost/latency without raw LLM scoring improvements prior to adding deterministic flags.
- (End to End Quality) The solution outputs well-formatted, complete advisory reports and markdown trajectories that are immediately useful to human judges.
- (Measured Improvement) Ablation results confirm that deterministic verification flags provided the -3.4 MAE improvement over the baseline, whereas the specialist prompt split alone provided no MAE gain.

**Output:**

- **Score:** 15 / 15
- **Confidence:** high
- **Rationale:** The submission provides an exemplary reproduction guide with step-by-step instructions from a clean virtual environment, detailed provider/env options, and explicit execution commands for all steps and evaluation scripts.
- **Evidence cited:**
- REPRODUCE.md
- requirements.txt
- DETERMINISTIC VERIFICATION FLAG: repro_paths_exist [OK]
- **Note passed forward:** All reproduction paths and script references were verified as present in the codebase.

### Step 8 - Hot Take / Insights (max 5)

**Instruction for this criterion:**

- _What strong work looks like:_ A strong insight turns an observed failure mode into a practical lesson for building more reliable agents.
- _Ask yourself:_ What did you learn and how would it change what you build next?

**Running notes inherited from earlier criteria:**
- (Problem & User Value) The target user is a hackathon judge, and the system acts as an advisory pre-screener rather than taking autonomous actions.
- (Agent Solution & Engineering) The multi-agent specialist split was shown by ablation to add cost/latency without raw LLM scoring improvements prior to adding deterministic flags.
- (End to End Quality) The solution outputs well-formatted, complete advisory reports and markdown trajectories that are immediately useful to human judges.
- (Measured Improvement) Ablation results confirm that deterministic verification flags provided the -3.4 MAE improvement over the baseline, whereas the specialist prompt split alone provided no MAE gain.
- (Reproducibility) All reproduction paths and script references were verified as present in the codebase.

**Output:**

- **Score:** 5 / 5
- **Confidence:** high
- **Rationale:** The hot take provides an exemplary, evidence-backed insight derived directly from ablation data—showing that deterministic verification checks outperform multi-agent prompt splitting—and clearly articulates how this changes future agent design.
- **Evidence cited:**
- README.md: 'I expected the six specialist scoring calls to be the win. They were not - the ablation shows the bare split scoring no better than one holistic prompt... Add the cheap check before you add the sixth model call.'
- **Note passed forward:** _(none)_

## Final aggregation

- **Total (sum of the six specialist scores):** 94 / 100
- **Needs human attention:** False
- **Low-confidence criteria:** _(none)_
- **Failed verification checks:** _(none)_

**Accumulated review notes:**
- (Problem & User Value) The target user is a hackathon judge, and the system acts as an advisory pre-screener rather than taking autonomous actions.
- (Agent Solution & Engineering) The multi-agent specialist split was shown by ablation to add cost/latency without raw LLM scoring improvements prior to adding deterministic flags.
- (End to End Quality) The solution outputs well-formatted, complete advisory reports and markdown trajectories that are immediately useful to human judges.
- (Measured Improvement) Ablation results confirm that deterministic verification flags provided the -3.4 MAE improvement over the baseline, whereas the specialist prompt split alone provided no MAE gain.
- (Reproducibility) All reproduction paths and script references were verified as present in the codebase.

> Advisory pre-screen only. Every score above is a starting point with cited evidence for a qualified human judge to confirm, adjust, or override -- this tool does not make a final accept/reject or prize decision.

---
