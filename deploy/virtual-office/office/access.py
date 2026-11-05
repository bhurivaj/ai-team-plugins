"""Floor access grants and audit log, stored in sqlite. Admins come from env only."""
from __future__ import annotations

import sqlite3
import time


class AccessStore:
    def __init__(self, db_path: str, admins: set[str]):
        self.db_path = db_path
        self.admins = set(admins)
        with self._db() as db:
            db.executescript(
                "CREATE TABLE IF NOT EXISTS users(id TEXT PRIMARY KEY, name TEXT);"
                "CREATE TABLE IF NOT EXISTS grants(user TEXT, area TEXT, PRIMARY KEY(user, area));"
                "CREATE TABLE IF NOT EXISTS audit(ts REAL, actor TEXT, user TEXT, area TEXT, allowed INTEGER, ok INTEGER);"
            )

    def _db(self):
        # A fresh connection per call; `with` commits, closing() releases the file.
        return closing_commit(sqlite3.connect(self.db_path, check_same_thread=False))

    def is_admin(self, user_id) -> bool:
        return user_id in self.admins

    def can_enter(self, user_id, area_id: str | None) -> bool:
        if area_id == "security":
            return self.is_admin(user_id)
        if area_id and area_id.startswith("floor:"):
            if self.is_admin(user_id):
                return True
            with self._db() as db:
                return db.execute("SELECT 1 FROM grants WHERE user=? AND area=?", (user_id, area_id)).fetchone() is not None
        return True  # lobby, None, and rooms inside a floor have no doors

    def remember_user(self, user_id, name) -> None:
        with self._db() as db:
            db.execute("INSERT INTO users(id, name) VALUES(?, ?) ON CONFLICT(id) DO UPDATE SET name=excluded.name", (user_id, name))

    def users(self) -> list[tuple[str, str]]:
        with self._db() as db:
            return [tuple(r) for r in db.execute("SELECT id, name FROM users ORDER BY name, id")]

    def set_grant(self, actor_id, user_id, area_id: str, allowed: bool) -> None:
        err = None
        if not self.is_admin(actor_id):
            err = PermissionError("only an admin may change access")
        elif not area_id.startswith("floor:"):
            err = ValueError("only floor areas can be granted")
        with self._db() as db:
            db.execute("INSERT INTO audit VALUES(?,?,?,?,?,?)", (time.time(), actor_id, user_id, area_id, int(bool(allowed)), int(err is None)))
            if err is None:
                if allowed:
                    db.execute("INSERT OR IGNORE INTO grants VALUES(?, ?)", (user_id, area_id))
                else:
                    db.execute("DELETE FROM grants WHERE user=? AND area=?", (user_id, area_id))
        if err:
            raise err

    def grants(self) -> dict[str, set[str]]:
        out: dict[str, set[str]] = {}
        with self._db() as db:
            for user, area in db.execute("SELECT user, area FROM grants"):
                out.setdefault(user, set()).add(area)
        return out

    def audit(self, limit=100) -> list[dict]:
        with self._db() as db:
            rows = db.execute("SELECT ts, actor, user, area, allowed, ok FROM audit ORDER BY rowid DESC LIMIT ?", (limit,))
            return [{"ts": ts, "actor": a, "user": u, "area": ar, "allowed": bool(al), "ok": bool(ok)} for ts, a, u, ar, al, ok in rows]


class closing_commit:
    """Context manager: commit on success, roll back on error, always close."""

    def __init__(self, conn):
        self.conn = conn

    def __enter__(self):
        return self.conn.__enter__()

    def __exit__(self, *exc):
        try:
            return self.conn.__exit__(*exc)
        finally:
            self.conn.close()
