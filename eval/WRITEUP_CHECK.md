# Write-up quality check - summary across sets

The check is `agent/panelassist/writeup.py`. It was frozen before the held-out set was written and has not been changed since. The labels are subjective drafts by one person, not independently reviewed; counts are tiny.

| Set | Cases | Labelled filler | Caught | Missed | Honest cases | False alarms |
|---|---|---|---|---|---|---|
| dev | 10 | 3 | 1 | 2 | 7 | 0 |
| held-out | 12 | 1 | 1 | 0 | 11 | 0 |
| **all** | 22 | 4 | 2 | 2 | 18 | 0 |

Overall: caught 2 of 4 filler write-ups; 0 false alarms on 18 honest write-ups.

What this does and does not show:
- It is conservative: it needs two independent signals, so it rarely fires on a good README. The cost is that it misses hype that uses wording outside its list.
- The dev-set catch (`good_project_bad_writeup`) was the case the check was written against, so it is not independent evidence.
- The held-out filler case (`buzzword_pipeline`) mixes phrases that are on the list with ones that are not, so one catch there is weak evidence too. There is exactly one labelled-filler case in the held-out set.
- Whether flagging a write-up improves the *score* needs a live run; see the README's status table.
