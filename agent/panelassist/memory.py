"""
Minimal shared memory for one review: as each rubric criterion is scored,
any 'note_for_other_criteria' it produced is carried forward so later
criteria in the same review are consistent with earlier findings (e.g. once
Reproducibility flags a broken setup guide, Agent Solution & Engineering
sees that note too and doesn't independently give full credit for
capabilities the judge can't actually verify were run).

This is deliberately simple -- a list, not a vector store -- because the
problem this project solves (consistency within one review) doesn't need
more than that. Scaling to memory *across* many submissions (calibration
drift over a long judging session) is exactly the kind of follow-up noted
in the README's hot take.
"""


class ReviewMemory:
    def __init__(self):
        self.notes: list[str] = []

    def add(self, criterion_name: str, note: str) -> None:
        if note:
            self.notes.append(f"({criterion_name}) {note}")

    def snapshot(self) -> list:
        return list(self.notes)
