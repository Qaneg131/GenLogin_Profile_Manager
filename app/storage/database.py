"""SQLite storage. Tasks, items, errors, history. No secrets stored."""
from __future__ import annotations
import os
import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks(
  id TEXT PRIMARY KEY, kind TEXT, target_version TEXT, status TEXT,
  created_at TEXT, started_at TEXT, ended_at TEXT);
CREATE TABLE IF NOT EXISTS task_items(
  task_id TEXT, profile_id TEXT, profile_name TEXT, status TEXT,
  reason TEXT, attempts INTEGER DEFAULT 0,
  previous_version TEXT, resulting_version TEXT,
  PRIMARY KEY(task_id, profile_id));
CREATE TABLE IF NOT EXISTS errors(
  id INTEGER PRIMARY KEY AUTOINCREMENT, task_id TEXT, profile_id TEXT,
  profile_name TEXT, operation TEXT, timestamp TEXT, message TEXT,
  attempts INTEGER DEFAULT 1, screenshot_path TEXT, resolution TEXT DEFAULT 'open');
"""


def connect(db_path: str) -> sqlite3.Connection:
    os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript(SCHEMA)
    conn.commit()
    return conn
