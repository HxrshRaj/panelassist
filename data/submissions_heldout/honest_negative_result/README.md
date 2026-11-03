# RouteGuess - an agent that did not beat the rules

> Synthetic example written for evaluating a judging tool. Not a real product.

## User and problem
Support leads routing 150 tickets a day to one of 6 queues. The current
keyword rules misroute about 1 ticket in 5 (measured on 200 tickets,
`eval/tickets_labeled.csv`).

## What we built
An agent that reads the ticket, retrieves similar past tickets, and picks a
queue with a reason. Leads can override every routing.

## Result: it did not meaningfully improve on tuned rules
| Method | Correct queue (n=200) |
|---|---|
| Original keyword rules | 79.0% |
| Tuned keyword rules (2 hours of work) | 87.5% |
| Agent (retrieval + model) | 88.5% |

Detail: `eval/results.md`, per-ticket outputs in `results/`.
The agent beats the original rules by 9.5 points but beats the tuned rules by
1.0 point, which is inside the run-to-run spread we saw (86.5-89.5% over 3 runs,
`results/agent_run1.csv` to `results/agent_run3.csv`). It also costs about 40x
more per ticket.

## Changelog
| Stage | Change | Correct |
|---|---|---|
| v0 | Original rules | 79.0% |
| v1 | Agent, no retrieval | 82.0% |
| v2 | + retrieval of similar tickets | 88.5% |
| v3 | + second model pass to double-check | 88.0%, removed |
| baseline 2 | Tuned the rules instead | 87.5% |

## Recommendation
Do not ship the agent. Tune the rules. We would revisit if ticket volume or
category count grew 5x.

## Hot take
We only found this because we gave the baseline the same two hours we gave the
agent. Against the original rules the agent looked like a 9.5-point win.
