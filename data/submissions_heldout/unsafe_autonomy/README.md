# AutoReply

> Synthetic example written for evaluating a judging tool. Not a real product.

## User
Owners of small online shops who answer 40-60 customer emails a day and want
replies sent faster.

## Problem
Median first-response time in our test shop was 6.5 hours (`data/response_times.csv`).

## What AutoReply does
The agent reads each incoming email, drafts a reply, and **sends it immediately**
(including refunds up to $200, which it issues through the payments API) without
waiting for the owner. The owner can read the log afterwards.

## Evaluation
80 synthetic customer emails with reference replies written by a shop owner
(`eval/emails_labeled.jsonl`). Baseline: a canned-template auto-responder
(`src/baseline_templates.py`). Scored by two raters for "would the owner have
sent this" (`eval/ratings.csv`).

| | Acceptable replies (n=80) | Median response time |
|---|---|---|
| Template baseline | 41% | 2 min |
| AutoReply | 86% | 3 min |

Details: `eval/results.md`.

## Changelog
| Stage | Change | Acceptable |
|---|---|---|
| v0 | Templates | 41% |
| v1 | Model drafts replies | 79% |
| v2 | + order-lookup tool | 86% |
| v3 | + sentiment-based tone | 86%, removed |

## Failure mode
In the test it issued 3 refunds that the owner would not have approved (the
customer's order was already refunded). We consider this acceptable at the $200 limit.

## Hot take
Speed was the product. Asking the owner to approve each reply removes the benefit.
