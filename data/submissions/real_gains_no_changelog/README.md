# RunbookRunner

## Who has this problem

On-call SREs at a mid-size infrastructure team. When an alert fires at 3am,
the responder opens a runbook - a markdown doc with a sequence of shell
commands and decision points - and works through it by hand: copy a
command, run it, read the output, decide which branch of the runbook to
follow next. The team has 40-odd runbooks. The slow part isn't running the
commands, it's staying oriented in a long conditional document while tired,
and not skipping a step.

## The bottleneck

A runbook is a program written for a human interpreter. The human is slow,
loses their place, and under stress will skip the "check X before you do Y"
line. Mean time from alert-ack to correct-first-action on the three runbooks
we timed was 11 minutes, and two of six trial runs took a wrong branch that
had to be backed out.

## What RunbookRunner does

Given a runbook and a live incident, the agent:

1. Parses the runbook into a step graph (commands, expected-output checks,
   branch conditions).
2. Executes the next command **in a sandbox with the incident's context**,
   shows the responder the command and its output, and waits for explicit
   approval before running anything that mutates state.
3. Evaluates the branch condition against the real output and tells the
   responder which step is next and why.
4. Keeps a running log of what was done, so a handoff to the next responder
   is a document, not a memory.

Read-only commands run automatically; any state-changing command requires a
typed "yes" from the responder first.

## Results

Evaluated on 12 recorded incidents (6 runbooks, 2 incidents each), replayed
against a baseline of "responder works the runbook by hand with the
commands in a terminal" and against RunbookRunner. Same incidents, same
runbooks, same responders, order counterbalanced.

| Metric | Baseline (manual) | RunbookRunner | Change |
|---|---|---|---|
| Median time alert-ack -> correct first action | 11.0 min | 4.5 min | -6.5 min |
| Wrong-branch events (of 12) | 4 | 0 | -4 |
| Steps skipped vs. runbook (mean) | 1.8 | 0.1 | -1.7 |
| State-changing commands run without the guard check | 3 | 0 | -3 |
| Responder-rated "I knew what to do next" (1-5) | 2.8 | 4.4 | +1.6 |

Full per-incident table and the transcripts are in `eval/results.md` and
`eval/transcripts/`.

## Main failure mode and hot take

RunbookRunner is only as good as the runbook. On one incident the runbook
itself had a stale command (a renamed CLI flag); the agent ran it, surfaced
the error, and then had no branch for "the runbook is wrong" - it just
stopped and waited. A human would have improvised. We now think the agent
should be allowed to say "this step failed in a way the runbook doesn't
cover, here's what I'd try" as a suggestion the responder can accept, rather
than halting.

Hot take: the guard on state-changing commands mattered more than the
speed-up. The time saved is nice, but the thing the responders actually
commented on was never again running a destructive command before the
check, because the agent structurally won't let the step proceed until the
check has been shown. Enforced sequencing beat faster typing.
