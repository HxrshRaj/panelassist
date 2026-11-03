# logtriage

> Synthetic example written for evaluating a judging tool. Not a real product.

quick notes, sorry for the mess. wrote this over the weekend.

## who
on-call engineers at a small saas shop. pager goes off, they get ~200 lines of
logs and have to decide: page the db team, the api team, or ignore.

## problem
wrong first guess costs about 12 min (we measured it, `data/oncall_timings.csv`).
2 of the last 9 incidents were routed wrong.

## what it does
1. regex pass pulls error signatures
2. model labels the incident (db / api / network / noise) and quotes the log line it used
3. if the quote isnt actually in the log, the label is thrown out (deterministic check, `src/verify_quote.py`)
4. a human confirms before anyone is paged

## numbers
60 labelled incidents in `eval/incidents_labeled.jsonl`. results in `eval/results.md`.

| method | routed correctly (n=60) |
|---|---|
| grep rules | 58% |
| single prompt | 71% |
| logtriage | 87% |

## changelog (what i tried)
| # | change | correct | kept? |
|---|---|---|---|
| 0 | grep rules | 58% | baseline 1 |
| 1 | single prompt | 71% | baseline 2 |
| 2 | + quote must appear in log | 83% | yes, biggest jump |
| 3 | + second model pass to double check label | 83% | **removed**, no gain, 2x cost |
| 4 | + regex signatures in the prompt | 87% | yes |

## failure mode
noise incidents (flapping health checks) get labelled network ~1 in 4 times.

## hot take
making the model quote its evidence and then checking the quote in plain code
fixed more than any prompt wording did.
