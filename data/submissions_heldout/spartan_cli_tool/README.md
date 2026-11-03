# pr-risk

> Synthetic example written for evaluating a judging tool. Not a real product.

A command-line tool that scores how risky a pull request is to review.

**User:** reviewers on a 12-person team who each get ~10 PRs a week and review
them in the order they arrive. **Problem:** a risky PR can wait behind five
trivial ones for a day; in a month of our history 7 of 41 incident-causing PRs
sat unreviewed for over 24h (`data/pr_history.csv`).

**Method:** extract features from the diff (files touched, test changes, config
changes), ask a model for a risk label with a one-line reason, show the label to
the reviewer. It orders nothing automatically; the reviewer chooses.

**Eval:** 90 historical PRs labelled risky/not by the team lead
(`eval/labels.csv`). Baseline is lines-changed thresholding
(`src/baseline_loc.py`). Results: `eval/results.md`.

| | catches risky PRs (of 24) | wrongly flagged (of 66) |
|---|---|---|
| lines-changed threshold | 11 | 9 |
| pr-risk | 19 | 8 |

**Changes tried:** diff text only (14 of 24) -> + file-type features (17) -> +
test-change feature (19). Adding commit-message sentiment: no change, removed.

**Hot take:** whether a PR touched tests told the model more than the diff text.
