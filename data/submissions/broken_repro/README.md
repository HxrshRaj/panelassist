# QuickTriage

## Who has this problem
Small support teams (2-3 people) at early-stage startups who can't
justify buying a full helpdesk platform yet but still need some way to
sort incoming tickets by urgency before they start replying.

## The bottleneck
Without any tooling, a 2-person team just replies to tickets in the order
they arrive, which means an angry churn-risk ticket can sit behind five
routine password resets for hours.

## Our solution
A lightweight agent that reads a batch of tickets and ranks them by
urgency, with a short justification per ticket. It uses a two-step
process: first a rough urgency score, then a re-ranking pass that looks at
the whole batch together so genuinely urgent tickets don't get buried.

## Improvement Changelog

| Stage | What we tried | Evidence | Decision |
|---|---|---|---|
| Baseline | Score each ticket independently, no batch context | 68% agreement with our manual ranking | Starting point |
| Iteration 1 | Added batch-level re-ranking pass | 81% agreement | Kept |
| Final | Batch re-ranking + short justification per ticket | 81% agreement, justifications rated "useful" by 4/5 reviewers | — |

## Hot take
Scoring tickets independently throws away information — urgency is
relative to what else is in the queue right now, not an absolute property
of the ticket text. Batch context mattered more than better per-ticket
prompting.
