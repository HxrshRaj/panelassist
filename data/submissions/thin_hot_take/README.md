# SortDesk

## Who has this problem
Any 3-6 person support team without a dedicated triage lead — someone has
to eyeball every new ticket before the shift starts, and whoever draws
that job loses 20-30 minutes every morning to it.

## The bottleneck
That 20-30 minutes is dead time nobody wants to own, so it gets skipped on
busy mornings, which is exactly when triage matters most.

## Our solution
An agent that pre-sorts the overnight queue into three buckets (needs
immediate reply, can wait until midday, can be closed/auto-replied) with a
one-line reason for each placement, and a verification step that
double-checks anything placed in "can wait" by re-reading it against a
short list of red-flag terms before committing.

## Improvement Changelog

| Stage | What we tried | Evidence | Decision |
|---|---|---|---|
| Baseline | Single prompt sorts all tickets in one pass | 70% agreement with team lead's manual sort (n=35 tickets) | Starting point |
| Iteration 1 | Split into three separate calls, one per bucket, to reduce cross-bucket confusion | 76% agreement | Kept |
| Iteration 2 | Added red-flag re-check specifically on the "can wait" bucket, since that's where a miss is costliest | 88% agreement, and zero red-flag tickets miscategorized as "can wait" (vs. 3 misses at baseline) | Kept — this is the change that mattered |
| Final | Three-bucket sort + red-flag re-check on the low-urgency bucket | 88% agreement, 0/35 costly misses | — |

## Hot take
AI is transforming how businesses operate and agents represent the future
of workplace automation. We learned that agentic AI has huge potential to
improve efficiency and that this technology will only get better over
time. We're excited to see where this space goes next.
