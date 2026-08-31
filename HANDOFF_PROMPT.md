# Prompt for Claude Code — paste this whole thing as your first message

I'm competing in the **micro1 Agentic Workflows Hackathon** (aka the Frontier
Engineering Challenge). It started Aug 28 and **ends Aug 31, 2026 at 18:00
UTC — that's 23:30 IST today**, so treat this as time-critical. Registration
requires an individual, solo submission; no team.

## What this project is

The hackathon's brief is open-ended: "pick a specific and meaningful problem
you understand, use agents to solve it, prove the improvement over a fair
baseline." I chose to solve **micro1's own judging bottleneck**: they have
8,300+ registrations to score against a published 100-point rubric (6
criteria: Problem & User Value 15pts, Agent Solution & Engineering 30pts,
End to End Quality 20pts, Measured Improvement 15pts, Reproducibility 15pts,
Hot Take/Insights 5pts — see `rubric.py`, transcribed verbatim from their
challenge PDF).

**PanelAssist** is an evidence-grounded pre-screener for that job: given a
submission's README, reproduction guide, and trajectory log, it (1) extracts
a structured "evidence ledger" once (target user, bottleneck, changelog
entries, every headline claim + whether it's backed by a specific checkable
file, every reproduction-guide reference, whether the hot take is genuine or
generic filler), (2) runs **deterministic verification** against that ledger
(do the reproduction guide's referenced files actually exist? does every
claim point to something checkable? is the hot take grounded?), (3) scores
each of the 6 rubric criteria with its **own specialist LLM call**, sharing
the evidence ledger and running memory notes from criteria already scored
in the same review, and (4) outputs an advisory report — cited evidence per
score, confidence flags — that a **human judge still has to confirm**. It
never issues a final accept/reject (this is deliberate, per the hackathon's
own ground rule 5: "make a qualified human reviewer part of any solution
that could significantly affect someone").

Baseline for comparison: one direct prompt, whole submission + rubric text,
single call, no tools (`baseline/baseline_scorer.py`) — exactly what a
time-pressed judge does pasting a submission into a chat window.

Evaluation: 6 fully synthetic mock hackathon submissions I wrote myself
(`data/submissions/`), deliberately spanning strong / weak / confidently
fabricated-but-unsupported-claims / broken-reproduction-guide /
generic-hot-take / cosmetic-multi-agent-with-no-real-gain. I hand-scored all
6 against the real rubric as ground truth (`data/human_scores.json`). Both
baseline and PanelAssist run against the same 6 cases; `eval/run_eval.py`
compares total-score MAE, ranking correlation, and — critically — whether
PanelAssist's verification layer actually catches the seeded issues that a
single prompt structurally cannot (the baseline has no mechanism to notice a
confidently-worded but evidence-free claim; that's the whole point being
measured).

## Where we're stuck

The Python/Gemini integration in `common/llm.py` is unreliable. History:

1. Originally called `gemini-2.0-flash` → 404, model retired. Google's error
   pointed us at `gemini-3.6-flash`.
2. Switched to `gemini-3.6-flash` → calls started failing with "No JSON
   object found in response" — the response looked truncated mid-JSON. My
   hypothesis: `gemini-3.6-flash` may be a "thinking" model that spends part
   of `maxOutputTokens` on hidden reasoning before the visible answer, so a
   token budget that's fine for a non-thinking model cuts off the JSON.
3. I patched `call_json()` to retry once with a much larger token budget
   (3x, min 4000) if the first parse fails, and bumped the default
   `max_tokens` across `baseline_scorer.py`, `extract.py`, and `score.py`.
   The user reports it's **still not fixed** — I don't have the exact
   current error/traceback, the conversation moved to handing off to you
   before I could see it.

**Your first job: get a clean, full traceback by running
`python baseline\baseline_scorer.py` yourself, read it carefully, and fix
the root cause** — don't just keep raising token limits blindly. Things
worth checking:
- Is the raw response actually JSON-shaped at all, or is `gemini-3.6-flash`
  returning something structurally different (e.g. a `thought` part
  alongside an `answer` part, where `common/llm.py`'s
  `"".join(p.get("text","") for p in parts)` is concatenating reasoning
  text together with the answer)? Print/log the *raw, full* response body
  once to see its actual shape before assuming it's a token-budget issue.
- **Strongly consider switching to Gemini's native structured-output mode**
  instead of prompt-asking for JSON and regex-stripping fences: set
  `generationConfig.responseMimeType: "application/json"` (optionally with
  a `responseSchema`) in the request body in `_call_gemini()`. That
  eliminates the whole fragile "hope the model wraps it in ```json" parsing
  approach in `_extract_json_object()` and is the more correct fix, not a
  workaround.
- Consider whether the official `google-genai` Python SDK
  (`pip install google-genai`) would be more robust than hand-rolled
  `urllib` REST calls — worth switching to if it saves debugging time,
  since the interface (`call()` / `call_json()`) that the rest of the
  codebase depends on is already abstracted in `common/llm.py`, so a
  provider swap there doesn't touch anything else.
- The API key the user has (`GEMINI_API_KEY` in `.env`, format
  `AQ.Ab8...`) is unusual for a Gemini key (standard ones start
  `AIzaSy...`). If errors turn out to be auth-related rather than
  parsing-related, flag that to the user — they may need to generate a
  fresh key at https://aistudio.google.com/apikey.
- `ANTHROPIC_API_KEY` is also supported as a fallback provider (see
  `_provider()` in `common/llm.py` — set `LLM_PROVIDER=anthropic` and
  `ANTHROPIC_API_KEY` in `.env` instead) if Gemini keeps being unreliable
  and the user can get a Claude API key faster.

## What's already built (don't redo this)

```
panelassist/
  rubric.py                        # exact rubric, verbatim from the challenge PDF
  common/llm.py                    # provider-agnostic LLM wrapper (Gemini + Anthropic)
  common/loader.py                 # loads a submission folder into a dict
  common/stats.py                  # dependency-free MAE + Spearman correlation
  data/submissions/*/               # 6 synthetic mock hackathon submissions (README, REPRODUCE.md, trajectory.json, manifest.json each)
  data/human_scores.json           # human-panel ground truth scores for those 6
  baseline/baseline_scorer.py      # single-prompt baseline
  agent/panelassist/extract.py     # evidence-ledger extraction (1 call)
  agent/panelassist/verify.py      # deterministic verification checks (no LLM)
  agent/panelassist/score.py       # per-criterion specialist scoring (6 calls)
  agent/panelassist/memory.py      # running notes carried across criteria in one review
  agent/panelassist/orchestrate.py # ties extract -> verify -> score together
  agent/panelassist/ablations.py   # isolates what each design choice contributes
  agent/run_agent.py               # CLI entrypoint for the full agent
  eval/run_eval.py                 # baseline vs agent vs human-ground-truth comparison
  eval/run_ablation.py             # produces the real measured changelog (not just baseline-vs-final)
  README.md                        # hackathon deliverable doc -- has a placeholder where real results go
  REPRODUCE.md                     # reproduction guide -- already accurate, just needs real numbers plugged into README
  HANDOFF_PROMPT.md                # this file
```

## The hackathon's actual requirements (check all of these before calling it done)

**Every valid entry needs a baseline AND an advanced solution** with a
*meaningful* improvement (not cosmetic) — we have this, but it needs real
numbers to prove it.

**Ground rules (all 10, from the challenge PDF) — audit against each:**
1. Fine to build with known tools (Python, LLM APIs) — already true.
2. Make clear what existed before the hackathon vs. what was added — README
   has a section for this, verify it's accurate.
3. Use every tool/component per its license and service terms — using
   official Gemini/Anthropic APIs, fine.
4. Consequential actions sandboxed/simulated with human approval before
   they happen — PanelAssist takes no actions, only produces a report; make
   sure nothing added later violates this.
5. A qualified human reviewer must be part of any solution that could
   significantly affect someone — PanelAssist is explicitly advisory-only
   (`orchestrate.py`'s `disclaimer` field); don't let a later change turn it
   into an auto-decision system.
6. Legal, ethical use case, responsible with data — all 6 eval cases are
   synthetic, verify none of it looks like it's using real people's data.
7. Public or synthetic data — same, already true, keep it that way.
8. **Keep credentials out of the submission** — `.env` is gitignored,
   double check it never gets committed or zipped into the final package.
9. Connect every claim about results to evidence you submit — this is the
   whole point of the project; make sure the README's own claims about
   *itself* follow this rule too (no numbers without a script that produces
   them).
10. Give judges enough access to run the project and reproduce the main
    result — test `REPRODUCE.md` yourself from a clean environment/venv
    before calling this done.

**Final deliverables (4 required):**
1. **Complete solution code + Improvement Changelog** — code exists;
   changelog table in `README.md` currently has real prose but needs the
   evidence numbers filled in from a real run. Close the README with the
   main failure mode + a genuine hot take (a draft is already there — keep
   it if it still rings true after real numbers, revise if not).
2. **Reproduction guide** — `REPRODUCE.md` exists and should be accurate;
   verify every command in it actually works from a clean environment,
   fix anything that doesn't.
3. **Solution video, up to 5 minutes** — not yet made. Once real numbers
   exist, write a tight script: problem + baseline → one full realistic
   execution end-to-end → final comparison table → changelog highlights →
   the single change that contributed most → one experiment that was tried
   and removed. **We don't yet have a genuine "removed experiment" for
   PanelAssist itself** (the mock submissions have one each, but that's not
   the same thing) — if time allows, actually try one cheap real ablation
   (e.g., LLM-based verification instead of the current deterministic
   checks) and see if it's actually worse/less auditable, then honestly
   report that as removed. If time is too short for a real experiment,
   report a real minor one instead (e.g., we initially considered scipy for
   the stats and removed the dependency in favor of a small hand-rolled
   implementation) rather than inventing a bigger one that didn't happen.
   The user needs to actually record this video themselves — you can only
   write the script.
4. **Agent trajectories for every agent used** — `trajectories/
   panelassist_runs.json` gets written by `agent/run_agent.py`, but it's
   raw JSON. Make it "easy to follow from agent instructions to final
   result" per the requirement — consider rendering 2-3 representative
   submissions' full trajectories (evidence extraction → verification flags
   → each per-criterion call with its citations → final aggregated score)
   into a readable markdown doc, not just a JSON dump.

## How to finish, in order

1. Fix `common/llm.py` (get a real, unmangled traceback first — don't guess).
2. Run `python baseline\baseline_scorer.py`, `python agent\run_agent.py`,
   `python eval\run_eval.py`, `python eval\run_ablation.py` — confirm all 4
   succeed and produce sane-looking numbers (sanity check: the strong
   submission should score highest, the weak one lowest, per
   `data/human_scores.json`).
3. Plug the real tables from `eval/RESULTS.md` and `eval/ABLATIONS.md` into
   `README.md`'s placeholder section and changelog table. Don't round up or
   soften a bad number — if PanelAssist doesn't actually beat baseline on
   something, say so honestly; the hot take can talk about it.
4. Render the trajectories deliverable as described above.
5. Test `REPRODUCE.md` from a genuinely clean environment (new venv or
   equivalent) — fix anything that doesn't work as written.
6. **Nice-to-have but genuinely valuable**: run PanelAssist on its own
   submission package before submitting (dogfooding) — structure this
   project's own README/REPRODUCE.md/trajectories as a `manifest.json`-style
   submission and see what PanelAssist itself flags. If it catches a real
   gap, fix it. This is also a great beat for the video.
7. Write the video script, then tell the user exactly what to record and
   where the take should start/stop for each of the 5 required beats. They
   record it themselves.
8. Final pass: re-read all 10 ground rules and the 4 deliverables above and
   confirm each is actually satisfied, not just plausible. Check no `.env`
   or API key ends up in whatever gets zipped/submitted.
9. Confirm the actual submission mechanism/deadline (check the HackerEarth
   challenge page or ask the user) and package everything needed to
   submit — the deadline is **18:00 UTC / 23:30 IST today, Aug 31, 2026.**

Work fast but don't fabricate a single number — the whole point of this
project is catching submissions that do that, so ours can't.
