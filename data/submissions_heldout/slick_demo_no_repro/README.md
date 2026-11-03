# TripBrief

> Synthetic example written for evaluating a judging tool. Not a real product.

## Who it helps
Executive assistants who turn a traveller's mess of confirmation emails into a
one-page itinerary. About 20 trips a month per assistant.

## Bottleneck
Each trip has 6-10 emails in different formats; assembling and cross-checking
them takes 25 minutes, and conflicts (a hotel check-in after the last flight)
are easy to miss.

## Approach
An agent extracts every booking, normalises times to the traveller's zones and
runs a conflict check. The assistant reviews the brief before it is sent.

## Results (30 synthetic trips, `eval/trips_labeled.json`)
| Metric | Single prompt | TripBrief |
|---|---|---|
| Bookings extracted correctly | 83% | 96% |
| Conflicts caught | 5 of 12 | 11 of 12 |

Full table: `eval/results.md`. Scoring code: `eval/score.py`.

## Changelog
| Stage | Change | Conflicts caught |
|---|---|---|
| Baseline | Single prompt | 5 of 12 |
| +1 | Time-zone normalisation tool | 8 of 12 |
| +2 | Deterministic conflict check | 11 of 12 |

## Hot take
Time arithmetic belongs in code, not in the model: the conflict check never
improved until it stopped being a prompt.
