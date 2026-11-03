# ShiftSwap

> Synthetic example written for evaluating a judging tool. Not a real product.

## The user
Nurse managers on a 30-bed ward who arbitrate shift-swap requests between staff.
Each week there are roughly 25 swap requests, and each must respect rest-hour
rules, skill mix and fairness history.

## The bottleneck
Checking a swap against three rule sets by hand takes about 6 minutes, and
managers say the fairness history is the part they most often get wrong.

## What it does
For each request the agent checks rest-hour rules, skill mix and swap history,
then proposes approve / reject with the specific rule it relied on. The manager
makes the final call on every request.

## Evaluation
40 historical swap requests with the manager's actual decision, in
`eval/swaps_labeled.csv`. We compare the agent to the status quo.

| Method | Agreement with manager (n=40) |
|---|---|
| Status quo (random approve/reject, as a stand-in for "no tool") | 34% |
| ShiftSwap agent | 91% |

Per-request results: `results/agent.csv`, `results/random.csv`.
Scoring script: `eval/score.py`.

## Changelog
| Stage | What changed | Agreement |
|---|---|---|
| v0 | Rule 1 only (rest hours) | 62% (`results/v0.csv`) |
| v1 | Added skill-mix rule | 79% (`results/v1.csv`) |
| v2 | Added fairness history | 91% (`results/agent.csv`) |

## Hot take
The fairness rule mattered most, and it is the one managers get wrong by hand,
so the gain concentrates exactly where the human is weakest.
