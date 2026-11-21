"""Repositories over the SQLite schema in database.py."""
from __future__ import annotations
import sqlite3
from app.core.models import ErrorRecord, Task, TaskItem


class TaskRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def save_task(self, t: Task):
        self.conn.execute(
            "INSERT OR REPLACE INTO tasks VALUES (?,?,?,?,?,?,?)",
            (t.id, t.kind, t.target_version, t.status, t.created_at,
             t.started_at, t.ended_at))
        for it in t.items:
            self.conn.execute(
                "INSERT OR REPLACE INTO task_items VALUES (?,?,?,?,?,?,?,?)",
                (t.id, it.profile_id, it.profile_name, it.status, it.reason,
                 it.attempts, it.previous_version, it.resulting_version))
        self.conn.commit()

    def update_status(self, task_id: str, status: str, ended_at=None):
        self.conn.execute("UPDATE tasks SET status=?, ended_at=? WHERE id=?",
                          (status, ended_at, task_id))
        self.conn.commit()

    def list_tasks(self, limit=200):
        cur = self.conn.execute(
            "SELECT id, kind, target_version, status, created_at, started_at, ended_at "
            "FROM tasks ORDER BY created_at DESC LIMIT ?", (limit,))
        return [Task(id=r[0], kind=r[1], target_version=r[2], status=r[3],
                     created_at=r[4] or "", started_at=r[5], ended_at=r[6])
                for r in cur.fetchall()]

    def interrupted_tasks(self):
        """Tasks left running/paused when the app last exited."""
        cur = self.conn.execute(
            "SELECT id, kind, target_version, status, created_at FROM tasks "
            "WHERE status IN ('running','paused','pending')")
        return [Task(id=r[0], kind=r[1], target_version=r[2], status=r[3],
                     created_at=r[4] or "") for r in cur.fetchall()]


class ErrorRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def add(self, e: ErrorRecord):
        self.conn.execute(
            "INSERT INTO errors(task_id, profile_id, profile_name, operation,"
            " timestamp, message, attempts, screenshot_path, resolution)"
            " VALUES (?,?,?,?,?,?,?,?,?)",
            (e.task_id, e.profile_id, e.profile_name, e.operation,
             e.timestamp, e.message, e.attempts, e.screenshot_path, e.resolution))
        self.conn.commit()

    def list_open(self, limit=500):
        cur = self.conn.execute(
            "SELECT task_id, profile_id, profile_name, operation, timestamp,"
            " message, attempts, screenshot_path, resolution FROM errors"
            " ORDER BY timestamp DESC LIMIT ?", (limit,))
        return [ErrorRecord(task_id=r[0], profile_id=r[1], profile_name=r[2],
                            operation=r[3], timestamp=r[4], message=r[5],
                            attempts=r[6], screenshot_path=r[7], resolution=r[8])
                for r in cur.fetchall()]
