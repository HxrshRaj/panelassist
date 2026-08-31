# DocSync AI - Revolutionizing Documentation Consistency with Agentic Workflows

## Introduction

In today's fast-paced software development landscape, maintaining
consistency between code and documentation has become an increasingly
critical challenge for engineering teams of all sizes. As codebases grow
and evolve at an unprecedented rate, the gap between what the code actually
does and what the documentation claims it does continues to widen,
resulting in confusion, wasted time, and a suboptimal developer experience.

DocSync AI leverages the power of cutting-edge agentic workflows to
seamlessly bridge this gap and deliver a truly transformative solution to
this pervasive problem.

## Who Has This Problem

The target user for DocSync AI is a technical writer or developer advocate
who is responsible for keeping a library's public API documentation in sync
with the actual codebase. On the team we studied, this person spends
roughly 6 hours per release manually diffing the changelog against the docs
site and hunting for function signatures that changed. Releases happen
weekly. When they miss something, the first signal is a GitHub issue from a
confused user, which then costs a support round-trip to resolve.

## What DocSync AI Does

DocSync AI utilizes a sophisticated multi-step agentic approach to
comprehensively address the documentation consistency challenge:

- **Firstly**, the agent ingests the git diff for a release and extracts
  every changed, added, or removed public symbol (functions, classes,
  constants) using the language's AST, not regex.
- **Secondly**, it retrieves the documentation pages that reference each
  changed symbol from the docs repository.
- **Thirdly**, it checks each doc snippet against the new signature and
  flags three categories: stale signature, removed symbol still documented,
  new symbol undocumented.
- **Furthermore**, before emitting a flag, a verification step re-parses
  the cited doc line and confirms the mismatch is real, which cut false
  positives substantially (see changelog).
- **Moreover**, it produces a patch file for the docs repo that a human
  reviews and merges. It never pushes on its own.

It is important to note that the human technical writer remains firmly in
the loop at all times and retains full control over what actually gets
merged.

## Improvement Changelog

| Stage | What we tried and why | Evidence | Decision |
|---|---|---|---|
| Baseline | One prompt: "here's a git diff and the docs folder, list the doc mismatches" | 0.52 F1 vs. our 30-item labeled set (`eval/labeled_mismatches.json`) | Starting point |
| Iteration 1 | Replaced regex symbol extraction with real AST parsing after seeing decorator-wrapped functions missed | 0.68 F1 | Kept |
| Iteration 2 | Added the re-parse verification step after noticing most false positives were the model misreading a doc line | 0.81 F1; precision 0.74 -> 0.91 | Kept - biggest single gain |
| Iteration 3 (removed) | Added a second model pass to also rewrite prose descriptions, not just signatures | No F1 change on the signature task, doubled cost, and the rewrites drifted in tone | Removed - out of scope for the metric that matters here |
| Final | AST extraction + retrieval + re-parse verification, prose rewriting removed | 0.81 F1, precision 0.91, recall 0.73, ~$0.02 per release, ~40s | - |

## Results

| Metric | Baseline | DocSync AI | Change |
|---|---|---|---|
| F1 on labeled mismatch set (n=30) | 0.52 | 0.81 | +0.29 |
| Precision | 0.61 | 0.91 | +0.30 |
| Recall | 0.45 | 0.73 | +0.28 |
| Cost per release | $0.01 | $0.02 | +$0.01 |
| Writer time per release (1 writer, timed over 4 releases, `eval/writer_time_log.csv`) | ~6 hr | ~1.5 hr | -4.5 hr |

## Main Failure Mode and Hot Take

The main failure mode is recall on symbols that are documented only in prose
("the timeout defaults to thirty seconds") rather than in a code block. The
AST gives us the symbol; the retrieval step finds the page; but matching a
number written as an English word against a changed default is still weak.
Four of the eight misses in the final eval were this pattern.

Hot take: retrieval quality set the ceiling here, not the model. Once the
right doc page was in context the model was reliable; when retrieval missed
the page, no amount of prompting recovered it. The verification step was
worth more than any prompt change because it let us be aggressive on recall
and clean up precision afterward, instead of trading one for the other in a
single pass.

See `eval/results.md` for the full per-item breakdown.
