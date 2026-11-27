"""Session State (Lab 6): everything Groundwork remembers across turns, in one place.
docs/state-contract.md is the human-readable version of this table; the two must agree.

  kind     scope           lifetime   written when                      deleted by
  turn     one session     24 hours   every chat turn (both sides)      expiry, or DELETE /me/memory
  focus    one founder     30 days    only when the founder asks        expiry, or DELETE /me/memory
                                      (the remember_focus tool)

Rules that hold everywhere in this file:
  * the key holds a hash (tools.caller_key), never the founder or session id itself
  * every read filters by key AND by expiry; there is no "all rows" read
  * forget() is one call and it is total: rows are deleted, not flagged
  * a visitor with no founder and no session leaves nothing behind

Storage: SQLite through the standard library, $GROUNDWORK_STATE_DIR/memory.db (git-ignored).
"""
from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .tools import caller_key

TURN_LIFETIME = timedelta(hours=24)       # a working session, then it is gone
FOCUS_LIFETIME = timedelta(days=30)       # about one round of interviews; refreshed when repeated
MAX_TURNS = 6                             # context budget for history: three exchanges
MAX_TURN_CHARS = 2000


def _db_path() -> Path:
    return Path(os.environ.get("GROUNDWORK_STATE_DIR", "state")) / "memory.db"


def now() -> datetime:
    """UTC now. GROUNDWORK_NOW pins it for the expiry tests."""
    pinned = os.environ.get("GROUNDWORK_NOW")
    return datetime.fromisoformat(pinned) if pinned else datetime.now(timezone.utc)


@contextmanager
def _conn():
    path = _db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    try:
        conn.execute("""CREATE TABLE IF NOT EXISTS memory (
            id INTEGER PRIMARY KEY, key TEXT NOT NULL, kind TEXT NOT NULL, role TEXT,
            value TEXT NOT NULL, created_at TEXT NOT NULL, expires_at TEXT NOT NULL)""")
        conn.execute("CREATE INDEX IF NOT EXISTS memory_key ON memory(key, kind, expires_at)")
        yield conn
        conn.commit()
    finally:
        conn.close()


def _session_key(session: str) -> str:
    return f"session:{caller_key(session)}"


def _founder_key(founder: str) -> str:
    return f"founder:{caller_key(founder)}"


def _put(key: str, kind: str, value: str, lifetime: timedelta, role: str | None = None) -> None:
    t = now()
    with _conn() as c:
        c.execute("INSERT INTO memory (key, kind, role, value, created_at, expires_at) VALUES (?,?,?,?,?,?)",
                  (key, kind, role, value, t.isoformat(), (t + lifetime).isoformat()))


def _get(key: str, kind: str, limit: int) -> list[sqlite3.Row]:
    with _conn() as c:
        c.row_factory = sqlite3.Row
        return c.execute("SELECT role, value FROM memory WHERE key=? AND kind=? AND expires_at>? "
                         "ORDER BY id DESC LIMIT ?", (key, kind, now().isoformat(), limit)).fetchall()


# ---------------------------------------------------------------- turns (scope: one session)

def add_turn(session: str, role: str, text: str) -> None:
    _put(_session_key(session), "turn", text[:MAX_TURN_CHARS], TURN_LIFETIME, role=role)


def recent_turns(session: str, limit: int = MAX_TURNS) -> list[dict]:
    """The last few turns of THIS session, oldest first, ready for a messages list."""
    rows = _get(_session_key(session), "turn", limit)
    return [{"role": r["role"], "content": r["value"]} for r in reversed(rows)]


# ---------------------------------------------------------------- focus (scope: one founder)

def remember_focus(founder: str, segment: str) -> str:
    """Store the founder's focus segment. One per founder: a new one replaces the old and restarts the clock."""
    key = _founder_key(founder)
    with _conn() as c:
        c.execute("DELETE FROM memory WHERE key=? AND kind='focus'", (key,))
    _put(key, "focus", segment.strip(), FOCUS_LIFETIME)
    return segment.strip()


def focus(founder: str) -> str | None:
    rows = _get(_founder_key(founder), "focus", 1)
    return rows[0]["value"] if rows else None


# ---------------------------------------------------------------- deletion and expiry

def forget(founder: str | None, session: str | None) -> dict:
    """Everything for this founder and this session, now. Called by DELETE /me/memory; no model involved."""
    counts = {"focus": 0, "turns": 0}
    with _conn() as c:
        if founder:
            counts["focus"] = c.execute("DELETE FROM memory WHERE key=? AND kind='focus'",
                                        (_founder_key(founder),)).rowcount
        if session:
            counts["turns"] = c.execute("DELETE FROM memory WHERE key=? AND kind='turn'",
                                        (_session_key(session),)).rowcount
    return counts


def expire() -> int:
    """Delete every row past its lifetime. Runs at app startup; reads already ignore expired rows."""
    with _conn() as c:
        return c.execute("DELETE FROM memory WHERE expires_at<=?", (now().isoformat(),)).rowcount


def rows_for_tests() -> list[tuple]:
    """Every row, raw. Only tests call this, to prove deletion is real."""
    with _conn() as c:
        return c.execute("SELECT key, kind, role, value FROM memory").fetchall()
