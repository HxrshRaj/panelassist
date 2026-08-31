# TicketTriage — an agent that sorts support tickets the way a senior agent would

## Who has this problem
Mara runs a 4-person support team at a mid-size SaaS company. Roughly 140
tickets land in the shared inbox each day. New hires take 10-15 seconds per
ticket just deciding *what kind of problem this is* and *how urgent it
really is* before they can even start helping the customer — and they get
it wrong often enough (missing a billing-outage ticket buried under twenty
"how do I reset my password" tickets) that Mara still spot-checks the queue
herself every morning.

## The bottleneck
Triage isn't hard per ticket — it's hard at volume, consistently, without a
senior person doing it. A junior agent under-flags urgency because they
don't yet know which phrases correlate with churn risk ("considering
canceling", "this is the third time"). The cost of getting it wrong is
concrete: the median time-to-first-response on tickets that were
initially mis-triaged is 3.1x longer than tickets triaged correctly on
the first pass (measured from our own support tool's ticket history,
`data/historical_triage_delay.csv`).

## What TicketTriage does
Given a raw ticket, the agent:
1. Classifies category (billing / bug / how-to / churn-risk / spam) and
   urgency (P0-P3).
2. Extracts the specific claim the customer is making (e.g. "charged
   twice on Aug 14") so a human doesn't have to re-read the ticket to find it.
3. Checks its own urgency call against a short rubric of red-flag phrases
   before finalizing (`src/verify_urgency.py`) — this is the piece that
   most improved precision on P0 tickets, see changelog.
4. Drafts a first-response, which a human agent reviews and sends — the
   agent never sends a message on its own.

## Improvement Changelog

| Stage | What we tried and why | Evidence | Decision |
|---|---|---|---|
| Baseline | Single prompt: "read this ticket, give category + urgency" | 61% urgency accuracy vs. our 40-ticket labeled set (`eval/labels.csv`) | Established starting point |
| Iteration 1 | Added category-specific few-shot examples pulled from our own resolved tickets | 74% urgency accuracy | Kept — biggest single jump |
| Iteration 2 | Added the red-flag-phrase verification pass (re-check before committing to a P2 or lower when churn language is present) | 89% urgency accuracy; P0/P1 recall went from 71% to 96% | Kept — this is the change that mattered most for the metric Mara actually cares about (missed urgent tickets) |
| Iteration 3 (removed) | Tried a second LLM call to also predict *sentiment score 1-10* as an extra signal | No measurable change to urgency accuracy (88% vs 89%), added ~40% more cost per ticket | Removed — sentiment score didn't correlate with our actual urgency labels, it just felt like it should help |
| Final | Category few-shot + urgency verification pass, sentiment removed | 89% urgency accuracy, 96% P0/P1 recall, $0.006/ticket, ~2.1s/ticket | — |

## Main failure mode & hot take
The agent still misses tickets where urgency is implied by *what's missing*
rather than what's said — e.g. a customer who used to email daily and has
gone silent for a week after a billing dispute. Nothing in the ticket text
itself is urgent-sounding. Our hot take: verification passes built to catch
*wrong tone* won't catch *wrong silence* — if the real signal lives outside
the artifact you're reviewing (ticket history, not ticket text), no amount
of re-reading the same ticket harder will find it. The next version needs a
tool call out to ticket history, not a better prompt.

See `eval/results.md` for the full baseline-vs-agent comparison table.
