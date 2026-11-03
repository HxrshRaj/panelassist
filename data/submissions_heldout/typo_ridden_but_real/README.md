# leaseflag

> Synthetic example written for evaluating a judging tool. Not a real product.

this tool help tenant volunteers read rental leases. volunteers at a tenants union
review about 15 leases a month, each 20+ pages, and they miss clauses (auto-renew,
fees that stack, entry without notice) when tired.

## what it do
agent read lease, list unusual clauses with page and the exact sentence, volunteer
decide what to tell tenant. it never give legal advice, volunteer and union lawyer
review everything. (human in loop - rule 5)

## test
60 synthetic leases we wrote (no real people), 214 planted unusual clauses, list in
`eval/planted_clauses.csv`. compare to volunteer checklist baseline (`src/checklist_baseline.py`,
keyword list the union already uses).

| | clauses found (of 214) | false flags |
|---|---|---|
| checklist | 121 (57%) | 38 |
| leaseflag | 188 (88%) | 21 |

see `eval/results.md`.

## what i try
| try | found | note |
|---|---|---|
| checklist only | 57% | start |
| model reads whole lease | 74% | misses clauses on long leases |
| split lease by section then read each | 85% | kept |
| + must quote the exact sentence, check quote exists in lease | 88% | kept, also cut false flags 33 -> 21 |
| ask model to rate legal risk 1-10 | no gain | removed, rating was not consistent between runs |

## failure
scanned leases with bad ocr - clause text garbled, quote check fails, we drop the flag. lose ~1 in 8.

## hot take
splitting the doc was worth more than a better model. long leases failed because
of length not because of reasoning.
