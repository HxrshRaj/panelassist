"""
SQLite storage for judge feedback. It stores scores, notes and ratings - never
the submission text, only a SHA-256 of it so a repeat review can be recognised.

Everything the stats page shows is computed from these tables, so with no rows
every metric is None and the page shows an empty state. Nothing is seeded.
"""
import hashlib
import json
import os
import sqlite3
import statistics
import threading
from datetime import datetime, timezone

SCHEMA = """
CREATE TABLE IF NOT EXISTS reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    source TEXT NOT NULL,              -- live | offline_demo | deterministic_only
    title TEXT,
    text_sha256 TEXT,
    advisory_total INTEGER,
    advisory_json TEXT,                -- {criterion_id: advisory score}
    flags_json TEXT,
    completed_at TEXT,
    seconds_to_review REAL,
    judge_total INTEGER
);
CREATE TABLE IF NOT EXISTS flag_feedback (
    review_id INTEGER NOT NULL,
    check_name TEXT NOT NULL,
    useful INTEGER NOT NULL,           -- 1 useful, 0 not useful
    created_at TEXT NOT NULL,
    PRIMARY KEY (review_id, check_name)
);
CREATE TABLE IF NOT EXISTS criterion_reviews (
    review_id INTEGER NOT NULL,
    criterion_id TEXT NOT NULL,
    max_points INTEGER NOT NULL,
    advisory_score INTEGER,
    judge_score INTEGER NOT NULL,
    note TEXT,
    PRIMARY KEY (review_id, criterion_id)
);
"""


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sha256_text(*parts: str) -> str:
    h = hashlib.sha256()
    for p in parts:
        h.update((p or "").encode("utf-8", errors="replace"))
        h.update(b"\x00")
    return h.hexdigest()


class Store:
    def __init__(self, path: str):
        self.path = path
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        self._lock = threading.Lock()
        with self._conn() as c:
            c.executescript(SCHEMA)

    def _conn(self):
        conn = sqlite3.connect(self.path, timeout=10)
        conn.row_factory = sqlite3.Row
        return conn

    # -- writes -----------------------------------------------------------
    def create_review(self, source, title, text_sha256, advisory_total, flags, advisory=None) -> int:
        with self._lock, self._conn() as c:
            cur = c.execute(
                "INSERT INTO reviews (created_at, source, title, text_sha256, advisory_total, advisory_json, flags_json) "
                "VALUES (?,?,?,?,?,?,?)",
                (now(), source, (title or "")[:120], text_sha256, advisory_total,
                 json.dumps(advisory or {}), json.dumps(flags)))
            return cur.lastrowid

    def review_exists(self, review_id: int) -> bool:
        with self._conn() as c:
            return c.execute("SELECT 1 FROM reviews WHERE id=?", (review_id,)).fetchone() is not None

    def get_advisory(self, review_id: int) -> dict:
        with self._conn() as c:
            row = c.execute("SELECT advisory_json FROM reviews WHERE id=?", (review_id,)).fetchone()
        return json.loads(row[0]) if row and row[0] else {}

    def rate_flag(self, review_id: int, check_name: str, useful: bool) -> None:
        with self._lock, self._conn() as c:
            c.execute("INSERT OR REPLACE INTO flag_feedback (review_id, check_name, useful, created_at) "
                      "VALUES (?,?,?,?)", (review_id, check_name[:60], int(bool(useful)), now()))

    def save_judge_review(self, review_id: int, judged: list, seconds: float | None) -> int:
        """judged: [{criterion_id, max_points, advisory_score, judge_score, note}]. Returns judge total."""
        total = sum(j["judge_score"] for j in judged)
        with self._lock, self._conn() as c:
            c.execute("DELETE FROM criterion_reviews WHERE review_id=?", (review_id,))
            c.executemany(
                "INSERT INTO criterion_reviews (review_id, criterion_id, max_points, advisory_score, judge_score, note) "
                "VALUES (?,?,?,?,?,?)",
                [(review_id, j["criterion_id"], j["max_points"], j.get("advisory_score"), j["judge_score"],
                  (j.get("note") or "")[:2000]) for j in judged])
            c.execute("UPDATE reviews SET completed_at=?, seconds_to_review=?, judge_total=? WHERE id=?",
                      (now(), seconds, total, review_id))
        return total

    # -- reads ------------------------------------------------------------
    def count_live_today(self) -> int:
        today = datetime.now(timezone.utc).date().isoformat()
        with self._conn() as c:
            return c.execute("SELECT COUNT(*) FROM reviews WHERE source='live' AND created_at LIKE ?",
                             (today + "%",)).fetchone()[0]

    def stats(self) -> dict:
        with self._conn() as c:
            total = c.execute("SELECT COUNT(*) FROM reviews").fetchone()[0]
            by_source = {r["source"]: r["n"] for r in c.execute(
                "SELECT source, COUNT(*) AS n FROM reviews GROUP BY source")}
            completed = c.execute("SELECT COUNT(*) FROM reviews WHERE completed_at IS NOT NULL").fetchone()[0]
            secs = [r[0] for r in c.execute(
                "SELECT seconds_to_review FROM reviews WHERE completed_at IS NOT NULL AND seconds_to_review IS NOT NULL")]
            rated = c.execute("SELECT COUNT(*) FROM flag_feedback").fetchone()[0]
            useful = c.execute("SELECT COUNT(*) FROM flag_feedback WHERE useful=1").fetchone()[0]
            crit = c.execute("SELECT advisory_score, judge_score FROM criterion_reviews "
                             "WHERE advisory_score IS NOT NULL").fetchall()
        diffs = [abs(r["judge_score"] - r["advisory_score"]) for r in crit]
        overrides = [d for d in diffs if d != 0]
        return {
            "has_data": total > 0,
            "reviews_opened": total,
            "reviews_by_source": by_source,
            "offline_demo_reviews": by_source.get("offline_demo", 0),
            "reviews_completed": completed,
            "completion_rate": round(completed / total, 3) if total else None,
            "median_seconds_to_review": round(statistics.median(secs), 1) if secs else None,
            "flags_rated": rated,
            "flags_marked_useful": useful,
            "helpful_rate": round(useful / rated, 3) if rated else None,
            "criteria_reviewed": len(diffs),
            "criteria_overridden": len(overrides),
            "override_rate": round(len(overrides) / len(diffs), 3) if diffs else None,
            "mean_abs_override_points": round(sum(overrides) / len(overrides), 2) if overrides else None,
        }
