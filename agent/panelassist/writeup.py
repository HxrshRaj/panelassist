"""
Deterministic write-up quality check (no LLM).

It looks for README prose that reads as padded boilerplate and targets the
End to End Quality criterion ("would a person sign their name to this
write-up?"). Every signal is something a judge can verify by eye in seconds.

It is a heuristic about *style*, not about whether the project is any good, and
it can be wrong - for example a genuinely well-written README that happens to
use a stock phrase or two. That is why it raises a flag for a human and is never
a verdict, and why one signal alone is not enough to flag.

Signals (a write-up is flagged when at least WRITEUP_SIGNALS_TO_FLAG fire):
  filler_phrases           >= 3 distinct stock phrases from a fixed list
  stacked_transitions      >= 3 sentences opening with Firstly / Furthermore / ...
  results_without_numbers  a Results/Evaluation section with prose but no digit

Design note: the phrase list and thresholds were written after reading the one
dev-set case this targets (good_project_bad_writeup), so that case is not
evidence the check generalises. The held-out set in data/submissions_heldout/
was written after this file was frozen, and eval/WRITEUP_CHECK.md reports both.
"""
import re

FILLER_PHRASES = (
    "in today's", "fast-paced", "ever-evolving", "rapidly evolving", "rapidly changing",
    "leverage the power", "leverages the power", "leveraging the power", "harness the power",
    "harnesses the power", "cutting-edge", "state-of-the-art", "game-changer", "game changing",
    "revolutioniz", "transformative", "seamless", "unlock the", "it is important to note",
    "it's important to note", "it is worth noting", "plays a crucial role", "in conclusion",
    "delve into", "testament to", "navigate the complexities", "comprehensive solution",
    "robust and scalable", "paradigm shift", "in harmony", "the future of",
)

TRANSITION_RE = re.compile(
    r"(?:^|[.!?]\s+|\*\*)(firstly|secondly|thirdly|furthermore|moreover|additionally|lastly)\b",
    re.IGNORECASE | re.MULTILINE,
)
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$", re.MULTILINE)
FENCE_RE = re.compile(r"```.*?```", re.DOTALL)
RESULTS_TITLE_RE = re.compile(r"result|evaluation|improvement", re.IGNORECASE)

WRITEUP_SIGNALS_TO_FLAG = 2
FILLER_DISTINCT_MIN = 3
TRANSITION_MIN = 3
RESULTS_MIN_WORDS = 15


def _prose(text: str) -> str:
    """README text without code fences or table rows (numbers in a table are
    real evidence, and code is not prose)."""
    text = FENCE_RE.sub(" ", text)
    return "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("|"))


def _results_section_without_numbers(raw: str):
    """(heading, word_count) for a Results/Evaluation/Improvement section that
    has prose but no digit anywhere in it, else None."""
    text = FENCE_RE.sub(" ", raw)
    heads = [(m.start(), m.end(), len(m.group(1)), m.group(2)) for m in HEADING_RE.finditer(text)]
    for i, (_, end, level, title) in enumerate(heads):
        if not RESULTS_TITLE_RE.search(title):
            continue
        stop = len(text)
        for nxt in heads[i + 1:]:
            if nxt[2] <= level:
                stop = nxt[0]
                break
        body = text[end:stop]
        words = len(body.split())
        if words >= RESULTS_MIN_WORDS and not re.search(r"\d", body):
            return title.strip(), words
    return None


def check_writeup_quality(readme_text) -> dict:
    if not readme_text or not readme_text.strip():
        return {"check": "writeup_quality", "passed": True, "signals": [],
                "detail": "No README text to assess."}
    prose = _prose(readme_text)
    low = prose.lower()
    signals = []

    hits = sorted({p for p in FILLER_PHRASES if p in low})
    if len(hits) >= FILLER_DISTINCT_MIN:
        signals.append({
            "name": "filler_phrases", "count": len(hits), "evidence": hits[:6],
            "explanation": f"{len(hits)} stock filler phrases appear (e.g. "
                           + ", ".join(repr(h) for h in hits[:3]) + ").",
        })

    trans = [m.group(1).lower() for m in TRANSITION_RE.finditer(prose)]
    if len(trans) >= TRANSITION_MIN:
        signals.append({
            "name": "stacked_transitions", "count": len(trans), "evidence": sorted(set(trans)),
            "explanation": f"{len(trans)} sentences open with a stock transition ("
                           + ", ".join(sorted(set(trans))) + ").",
        })

    nonum = _results_section_without_numbers(readme_text)
    if nonum:
        signals.append({
            "name": "results_without_numbers", "count": 1, "evidence": [nonum[0]],
            "explanation": f"The section '{nonum[0]}' ({nonum[1]} words) describes results but "
                           "contains no number.",
        })

    flagged = len(signals) >= WRITEUP_SIGNALS_TO_FLAG
    if flagged:
        detail = ("README prose reads as padded boilerplate: "
                  + " ".join(s["explanation"] for s in signals)
                  + " This bears on End to End Quality (would a person sign their name to this write-up?).")
    elif signals:
        detail = (f"One write-up signal fired, below the flag threshold of {WRITEUP_SIGNALS_TO_FLAG}: "
                  + signals[0]["explanation"])
    else:
        detail = "No filler-phrase, stacked-transition or numberless-results signals found in the README."
    return {"check": "writeup_quality", "passed": not flagged, "signals": signals, "detail": detail}
