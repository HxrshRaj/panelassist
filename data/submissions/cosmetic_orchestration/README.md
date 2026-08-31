# Hydra Support Swarm

## Who has this problem
Support teams triaging incoming tickets.

## The bottleneck
Doing it manually takes time.

## Our solution
A swarm of 6 specialized agents — Intake Agent, Sentiment Agent, Category
Agent, Priority Agent, Consensus Agent, and Output Formatter Agent — all
orchestrated via a central controller to classify each ticket with maximum
sophistication.

## Improvement Changelog

| Stage | What we tried | Evidence | Decision |
|---|---|---|---|
| Baseline | One prompt classifies category + urgency | 82% accuracy vs. our 20-ticket labeled set | Starting point |
| Iteration 1 | Split into 6 specialized agents or one per sub-task, orchestrated by a controller | 83% accuracy | Kept — more agents, more sophisticated |
| Iteration 2 | Added a Consensus Agent that combines the other 5 agents' outputs via majority vote | 82% accuracy | Kept for architectural completeness |
| Final | Full 6-agent swarm with consensus voting | 83% accuracy, 5.8x more tokens per ticket than baseline, 4.1x higher latency | — |

## Hot take
More specialized agents working together is inherently more powerful and
represents best practice in agentic system design.
