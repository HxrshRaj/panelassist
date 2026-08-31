# PanelAssist - solution video script (<= 5 minutes)

Target **4:15-4:40**. You (Harsh) narrate over a screen recording. Every
number below is from `eval/RESULTS.md` / `eval/ABLATIONS.md` /
`eval/REMOVED_EXPERIMENT.md`. Do not round them in PanelAssist's favour -
the honesty is the point of the project.

**Setup:** terminal + editor side by side, repo at
`C:\Users\hraj1\Desktop\panelassist`, `.env` already configured, font big
enough to read at 1080p. Pre-record and cut any multi-minute wait.

---

## Beat 1 - Problem + baseline  (0:00 - 0:50)

**Show:** `rubric.py`, then `baseline/baseline_scorer.py`.

**Say:**
> micro1's Agentic Workflows Hackathon drew over eight thousand three
> hundred registrations, all scored by a human panel against this
> hundred-point rubric. The failure I care about isn't a judge being wrong,
> it's a judge being rushed on their fortieth submission and not *checking*:
> giving points for a confident claim without verifying anything backs it,
> or scoring a submission "strong overall" without docking the one
> criterion it actually fails.
>
> My baseline is what a rushed judge does: paste the whole submission plus
> the rubric into one prompt, get six sub-scores and a paragraph back. One
> LLM call, no tools. `baseline_scorer.py`. It's a fair baseline, not a
> strawman - and it's a strong one.

**Take:** rubric -> baseline file. ~50s.

---

## Beat 2 - One full execution, end to end  (0:50 - 2:20)

**Show:** run `python agent/run_agent.py` (cut the wait), then open
`trajectories/TRAJECTORIES.md`, scroll the `fabricated_claims` section:
evidence ledger -> verification table -> the six specialist calls -> final
aggregation.

**Say:**
> PanelAssist runs one submission as a fixed pipeline. One extraction call
> builds an evidence ledger - target user, bottleneck, and for every
> headline result claim, is there a specific file that would let someone
> check it.
>
> Then a deterministic pass, no LLM. On `fabricated_claims` it flags that
> the headline numbers - 94.7% accuracy, a 12.4x speedup - name no file at
> all, and that the reproduction guide openly says the eval set is
> withheld. A single prompt has nowhere to run that check or leave a record
> of it.
>
> Then six specialist calls, one per rubric criterion. Each one is told:
> judge only your criterion, start from full marks, deduct for a weakness
> you can name, and treat any verification flag as a real subtraction. Each
> comes back with a score, the weaknesses it deducted for, and a citation.
>
> Then it aggregates - and it stops. No accept, no reject, no ranking. It
> hands the judge a report with `needs_human_attention` set and a
> disclaimer. That's ground rule five, by construction.

**Take:** hit enter on `run_agent.py`; cut; resume on `TRAJECTORIES.md`;
end on the disclaimer line. ~1:30.

---

## Beat 3 - The comparison  (2:20 - 3:20)

**Show:** `eval/RESULTS.md` - the metrics table and the seeded-issue
section.

**Say:**
> Both scorers run on the same ten synthetic submissions, against scores I
> set by hand as the reviewer. The result: PanelAssist agrees with the
> panel better. Total-score mean absolute error 7.8, versus the baseline's
> 11.2. Rank correlation slightly better too.
>
> The gap is almost entirely six mid-band submissions - each one strong
> except for a single localized flaw. `good_project_bad_writeup` is solid
> engineering wrapped in an obviously AI-generated write-up; the panel gave
> it 78, the baseline gave it 98, because a holistic pass reads
> "strong overall" and can't dock one criterion without being told to look
> at that criterion alone. PanelAssist's per-criterion specialists got it
> to 94 - still high, but not top-of-class.
>
> And the seeded defects: three of three caught by the deterministic layer,
> zero false alarms on the five honest submissions. The baseline catches
> zero - no mechanism. One more thing worth saying: the baseline isn't just
> less accurate here, it's *unstable* - 8.6 on one run of these ten, 11.2
> on the next, same inputs. The verification layer doesn't move at all.
>
> Cost of all this: seven calls per submission instead of one, about six
> cents for all ten versus half a cent.

**Take:** one scroll through `RESULTS.md`. ~1:00.

---

## Beat 4 - Changelog: what each change actually did  (3:20 - 4:05)

**Show:** `eval/ABLATIONS.md` - the stage table.

**Say:**
> I built this in stages and re-scored each against the same panel.
> Baseline, one prompt: MAE 11.2. Add the evidence ledger: MAE goes
> slightly *worse*, 12.2 - the compressed ledger trades calibration for
> ranking. Add the six specialist calls with the strict deduct-from-full
> prompt: back to 11.2 - no better than one prompt. Then feed the
> deterministic verification flags into those calls as forced deductions:
> 7.8.
>
> So the honest changelog: the six scoring calls were not the improvement.
> The thing that moved the number, and the only thing that catches the
> planted defects, was the cheap Python check - once its output was wired
> in as a subtraction the scorer couldn't ignore.

**Take:** hold on the ablation table. ~45s.

---

## Beat 5 - One experiment, tried and removed  (4:05 - 4:30)

**Show:** `eval/REMOVED_EXPERIMENT.md`, then `agent/panelassist/verify_llm.py`.

**Say:**
> One thing I tried and cut: doing the verification step with an LLM
> instead of plain Python - ask a model "does this claim have evidence"
> rather than checking `path in file_list`. Across all ten submissions,
> three runs each, it caught the same three of three defects with the same
> zero false alarms. It didn't fail. I cut it anyway - thirty extra LLM
> calls, and "the same across three runs" isn't "reproducible" for a
> sampled model. A flag a judge acts on has to be one they can re-derive by
> hand. The code's still in the repo, off the pipeline. That's the whole
> idea - the cheap deterministic check was just as good, and I only know
> that because I measured instead of assuming the LLM was the upgrade.

**Take:** `REMOVED_EXPERIMENT.md` -> `verify_llm.py` docstring. ~25s.

---

## Optional closer (if under time)  (4:30 - 4:40)

> I also ran PanelAssist on its own submission package - `dogfood/`. It
> flagged two real gaps where the reproduction guide named files the
> package manifest didn't list. Both fixed. What it can't tell me is
> whether the six scoring calls were worth building - the ablation already
> answered that: no.

---

_All numbers verified against `eval/RESULTS.md`, `eval/ABLATIONS.md`,
`eval/REMOVED_EXPERIMENT.md` from the canonical 10-case run. Nothing here is
rounded in PanelAssist's favour; where it loses (cost, and it still runs
high on `good_project_bad_writeup`) the script says so._
