# GrantMatch

## Who has this problem

Research-development officers at small university departments. When a
funding call comes out, they read it and then decide which of their ~60
faculty to email about it. Getting it wrong both ways is costly: email
everyone and they stop reading your emails; miss the one person whose work
fits and the department loses a proposal it would have won. The officer we
worked with spends about 90 minutes per call cross-referencing the call
text against faculty pages and past awards.

## The bottleneck

A funding call is 3-8 pages of eligibility rules, scope language, and
priorities. Matching it to a faculty member means holding the call's
constraints in your head while reading someone's publication list and
deciding whether the fit is real or superficial. It's a comparison task
across two long, messy documents, done 60 times per call, and the officer's
attention degrades after the first fifteen.

## Our solution

A four-agent pipeline behind one command:

1. **Call parser** - extracts hard constraints (eligibility, deadline,
   award ceiling, required institution type) and soft signals (topic
   priorities, named example areas) into a structured brief.
2. **Faculty researcher** - for each faculty member, pulls their listed
   research statement + last 5 publication titles from the provided
   dataset and summarizes their active areas.
3. **Matcher** - scores each faculty member against the brief, separating
   "fails a hard constraint" from "soft-fit score", with a one-line reason.
4. **Checker** - re-reads the top 10 matches against the call text and
   flags any where the stated reason isn't supported by the faculty
   summary. Demotes those.

The officer gets a ranked shortlist with reasons and hard-constraint flags,
and decides who to actually contact.

## Improvement Changelog

| Stage | What we tried and why | Evidence | Decision |
|---|---|---|---|
| Baseline | One prompt: call text + all 60 faculty blurbs -> "rank the top 10" | 0.58 nDCG@10 vs. the officer's own ranking on 8 past calls (`eval/officer_rankings.json`) | Starting point |
| Iteration 1 | Split call parsing into its own step so constraints were explicit, not buried in the prompt | 0.64 nDCG@10; hard-constraint violations in the top 10 went 1.4 -> 0.5 per call | Kept |
| Iteration 2 | Added the per-faculty researcher step (summarize before matching) instead of matching against raw blurbs | 0.71 nDCG@10 | Kept |
| Iteration 3 | Added the checker step after seeing the matcher invent plausible-sounding fit reasons | 0.76 nDCG@10; "unsupported reason" rate in top 10 fell from 22% to 6% | Kept |
| Iteration 4 (removed) | Added a fifth "advocate" agent that argued for borderline candidates to reduce false negatives | No nDCG change (0.76 -> 0.76), +35% cost, and it mostly re-surfaced candidates the checker then re-demoted | Removed - it added a loop, not information |
| Final | parse -> research -> match -> check, four agents | 0.76 nDCG@10, 0.5 hard-constraint violations/call, ~$0.14 per call, ~3 min | - |

## Results

| Metric | Simple baseline | GrantMatch | Change |
|---|---|---|---|
| nDCG@10 vs. officer ranking (n=8 calls) | 0.58 | 0.76 | +0.18 |
| Hard-constraint violations in top 10 (mean/call) | 1.4 | 0.5 | -0.9 |
| Unsupported fit reasons in top 10 | 22% | 6% | -16 pts |
| Officer time per call | ~90 min | ~25 min (review the shortlist) | -65 min |
| Cost per call | ~$0.03 | ~$0.14 | +$0.11 |
| Wall-clock per call | ~35 s | ~3 min | +~2.5 min |

## Main failure mode and hot take

The remaining errors are near-misses on interdisciplinary faculty: someone
whose work genuinely spans two areas gets a middling score in both instead
of a high score for the combination, because each step evaluates fit one
dimension at a time. The checker doesn't help here - the reason *is*
supported, it's just underweight.

Hot take: every agent in this pipeline had to earn its place in the metric,
not the diagram. Three of the four steps moved nDCG or the constraint-
violation count; the fourth (the removed advocate) moved neither and we
cut it even though it made the architecture diagram look more thorough. The
lesson we're taking forward: add the step, measure, and be willing to
delete it the same day if the number doesn't move - "it seems like it
should help" is how you end up paying 35% more for a loop.
