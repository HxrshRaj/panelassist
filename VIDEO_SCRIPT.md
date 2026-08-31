# PanelAssist - solution video script (<= 5 minutes)

Target **4:15-4:40**. You (Harsh) narrate over a screen recording. Every
number below is real, from `eval/RESULTS.md`, `eval/ABLATIONS.md`,
`eval/REMOVED_EXPERIMENT.md`. Do not round them "up" - the honesty is the
point of the project.

**Setup:** terminal + editor side by side, repo at
`C:\Users\hraj1\Desktop\panelassist`, `.env` already configured, font big
enough to read at 1080p. Where a command takes minutes, pre-record and
cut the wait.

---

## Beat 1 - Problem + baseline  (0:00 - 0:50)

**Show:** `rubric.py`, then `baseline/baseline_scorer.py`.

**Say:**
> micro1's Agentic Workflows Hackathon drew over eight thousand three
> hundred registrations, all scored by a human panel against this
> hundred-point rubric. The failure I care about isn't a judge being wrong,
> it's a judge being rushed on their fortieth submission and not *checking*:
> giving points for a confident claim without verifying that anything in the
> submission backs it. The rubric literally says "connect every claim to
> evidence" - but nothing forces that check.
>
> My baseline is what a rushed judge actually does: paste the whole
> submission plus the rubric into one prompt, get six sub-scores and a
> paragraph back. One LLM call, no tools. That's `baseline_scorer.py`, and
> it's a fair baseline, not a strawman - as you'll see, it's a strong one.

**Take:** rubric -> baseline file. ~50s.

---

## Beat 2 - One full execution, end to end  (0:50 - 2:25)

**Show:** run `python agent/run_agent.py` (cut the wait), then open
`trajectories/TRAJECTORIES.md`, scroll the `fabricated_claims` section:
evidence ledger -> verification table -> the six specialist calls -> final
aggregation.

**Say:**
> PanelAssist runs one submission as a fixed pipeline. One extraction call
> builds an evidence ledger - target user, bottleneck, and for every
> headline claim, is there a specific file that would let someone check it.
>
> Then a deterministic pass, no LLM. On `fabricated_claims` it flags that
> all three headline numbers - 94.7% accuracy, a 12.4x speedup, 63% cost
> reduction - name no file at all, and that the reproduction guide openly
> says the eval set is withheld. A single prompt has no mechanism to run
> that check or leave a record of it.
>
> Then six specialist calls, one per rubric criterion. Each sees the
> ledger, the flags, and the notes left by criteria already scored - so a
> broken-repro finding reaches the Measured Improvement scorer too. Every
> sub-score comes back with a citation and a confidence level.
>
> Then it aggregates - and it stops. No accept, no reject, no ranking. It
> hands the judge a report with `needs_human_attention` set and a
> disclaimer. A human still decides. That's ground rule five, by
> construction.

**Take:** hit enter on `run_agent.py`; cut; resume on `TRAJECTORIES.md`;
end on the disclaimer line. ~1:35.

---

## Beat 3 - The comparison, honestly  (2:25 - 3:25)

**Show:** `eval/RESULTS.md` - the metrics table and the seeded-issue
section.

**Say:**
> Both scorers run on the same six synthetic submissions, against scores I
> set by hand as the reviewer. Here's the honest result, wins and losses.
>
> On raw agreement with my scores, the baseline is *better*: mean absolute
> error 5.3 versus PanelAssist's 6.3, rank correlation a perfect 1.0 versus
> 0.94. A strong model asked to score holistically is already a good
> holistic judge, and PanelAssist's seven calls came out a little generous.
> I'm not going to pretend otherwise.
>
> Where it separates is the three submissions with a planted,
> rubric-violating defect. PanelAssist's verification layer catches three
> of three, with zero false alarms on the clean control. The baseline
> catches zero of three - it has no mechanism to. And that same layer,
> feeding the Reproducibility scorer, is the one sub-score where PanelAssist
> beats the baseline: 0.67 error versus 1.17.
>
> Cost of the machinery: seven calls per submission instead of one, about
> three cents for all six versus a third of a cent.

**Take:** one scroll through `RESULTS.md`. ~1:00.

---

## Beat 4 - Changelog: what each change actually did  (3:25 - 4:05)

**Show:** `eval/ABLATIONS.md` - the stage table.

**Say:**
> I built this in stages and re-scored each against the same ground truth.
> Baseline to evidence-ledger: it got *worse* - error jumped from 5.3 to
> 10.2, because scoring from a tidy structured summary instead of the raw
> text made the model over-credit submissions that looked complete. The
> specialist split clawed about 1.5 points back. Adding deterministic
> verification clawed another 2.3 back, to 6.3 - the single biggest
> positive change, and the only one that catches the planted defects - but
> still short of the baseline on total error.
>
> So the honest changelog is: the verification pass earned its place. The
> six-call scoring machinery around it did not. If I shipped this, I'd run
> verification as a side-car on the single-prompt score and drop the
> re-scoring.

**Take:** hold on the ablation table. ~40s.

---

## Beat 5 - One experiment, tried and removed  (4:05 - 4:30)

**Show:** `eval/REMOVED_EXPERIMENT.md`, then `agent/panelassist/verify_llm.py`.

**Say:**
> One thing I tried and cut: doing the verification step with an LLM
> instead of plain Python - ask a model "does this claim have evidence"
> rather than checking `path in file_list`. Here's the honest result: it
> caught the same three of three defects, with the same zero false alarms.
> It didn't fail. I cut it anyway - it costs an extra call per submission,
> and its answer is only *probably* the same run to run, because it's a
> sampled model. A flag a judge acts on has to be one they can re-derive by
> hand. The code's still in the repo, off the pipeline. That's the whole
> idea - the cheap deterministic check was just as good, and I only know
> that because I measured it instead of assuming the LLM was the upgrade.

**Take:** `REMOVED_EXPERIMENT.md` -> `verify_llm.py` docstring. ~25s.

---

## Optional closer (if under time)  (4:30 - 4:40)

> I also ran PanelAssist on its own submission package - `dogfood/`. What
> it flagged, I fixed. What it couldn't flag is exactly the hot take: it
> can't tell you whether the seven-call pipeline was worth building. The
> ablation can.

---

_All numbers verified against `eval/RESULTS.md`, `eval/ABLATIONS.md`,
`eval/REMOVED_EXPERIMENT.md` as of the final run. Nothing in this script is
rounded in PanelAssist's favour._
