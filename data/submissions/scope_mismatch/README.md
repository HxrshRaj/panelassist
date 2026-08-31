# TidyDrop

## Who has this problem

Me. My Downloads folder has 3,400 files in it. Probably other people too.
It's annoying to find things.

## The bottleneck

Sorting a downloads folder by hand is boring and I never do it, so it just
grows. Rule-based sorters (by extension) put every PDF in one pile whether
it's a bank statement, a boarding pass, or a paper.

## What TidyDrop does

Given a folder, the agent:

1. Reads each file's name, type, size, and - for PDFs, text, and images -
   a short content sample.
2. Proposes a destination folder from a small taxonomy (documents/finance,
   documents/travel, documents/reading, media/images, media/video,
   installers, archives, code, misc) with a one-line reason.
3. Shows the full plan as a dry run. Nothing moves until you approve.
4. On approval, moves the files and writes an undo log; `tidydrop --undo`
   puts everything back exactly where it was.

Read-only until you approve. Every move is reversible from the log.

## Improvement Changelog

| Stage | What we tried and why | Evidence | Decision |
|---|---|---|---|
| Baseline | Extension-only rules (`.pdf` -> documents, `.jpg` -> images, ...) | 0.44 agreement with my hand-sort of 200 files | Starting point |
| Iteration 1 | LLM classifies from filename only | 0.63 agreement; still bad on generic names like `scan_0421.pdf` | Kept |
| Iteration 2 | Added a content sample (first 500 chars / image caption) for ambiguous types | 0.86 agreement; the finance/travel/reading split on PDFs went from near-random to 0.9 | Kept - the change that mattered |
| Iteration 3 | Added the dry-run + undo log after I lost track of where 40 files went in an early test | Agreement unchanged; recovered a bad run in one command | Kept - safety, not accuracy |
| Final | Content-aware classification + dry run + undo | 0.86 agreement with hand-sort, ~$0.05 per 200 files, ~90s | - |

## Results

| Metric | Baseline (extension rules) | TidyDrop | Change |
|---|---|---|---|
| Agreement with my hand-sort (n=200) | 0.44 | 0.86 | +0.42 |
| PDF sub-type accuracy (finance/travel/reading, n=70) | 0.19 | 0.90 | +0.71 |
| Files needing manual fix after the run | 112 | 28 | -84 |
| Cost per 200 files | $0 | ~$0.05 | +$0.05 |
| Wall-clock per 200 files | <1 s | ~90 s | +~90 s |

Per-file labels and both runs are in `eval/handsort.csv` and `eval/results.md`.

## Main failure mode and hot take

It's bad at files that are only meaningful to me - a PDF named
`final_FINAL_v3.pdf` that's actually my apartment lease goes to
"documents/reading" because nothing in the first 500 characters says
"lease". A per-user memory of past corrections would fix most of these; I
didn't build it.

Hot take: the dry-run step changed how I felt about the tool more than the
accuracy did. At 86% agreement, one run still misplaces ~28 of 200 files -
that's only acceptable because I see the whole plan first and can fix it in
the preview, and because undo is one command. An agent that moves your
files is a different trust proposition than one that suggests where to move
them, and the preview is what bridges it.
