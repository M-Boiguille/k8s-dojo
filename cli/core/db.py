"""SQLite database layer for K8s Dojo."""
import json
import os
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_HOME = PROJECT_ROOT


def get_data_dir() -> Path:
    """Resolve data directory (project root, or K8S_DOJO_HOME override)."""
    if os.getenv("K8S_DOJO_HOME"):
        return Path(os.getenv("K8S_DOJO_HOME")).expanduser().resolve()
    return PROJECT_ROOT


def db_path() -> Path:
    return get_data_dir() / "private" / "dojo.db"


def ensure_dirs() -> None:
    data = get_data_dir()
    (data / "private" / "drafts").mkdir(parents=True, exist_ok=True)
    (data / "public" / "journal").mkdir(parents=True, exist_ok=True)
    (data / "workspace").mkdir(parents=True, exist_ok=True)


def get_db() -> sqlite3.Connection:
    ensure_dirs()
    conn = sqlite3.connect(db_path())
    conn.row_factory = sqlite3.Row
    init_db(conn)
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS profile (
            id TEXT PRIMARY KEY,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            total_katas INTEGER DEFAULT 0,
            boss_defeated INTEGER DEFAULT 0,
            total_hints_used INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kata_id TEXT NOT NULL,
            started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            ended_at DATETIME,
            duration_seconds INTEGER,
            hint_level_reached INTEGER DEFAULT 0,
            ia_score INTEGER,
            success BOOLEAN,
            raw_log TEXT,
            published_at DATETIME
        );

        CREATE TABLE IF NOT EXISTS competence_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATETIME DEFAULT CURRENT_TIMESTAMP,
            pods INTEGER DEFAULT 0,
            services INTEGER DEFAULT 0,
            storage INTEGER DEFAULT 0,
            networking INTEGER DEFAULT 0,
            rbac INTEGER DEFAULT 0,
            git INTEGER DEFAULT 0,
            architecture INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS skill_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATETIME DEFAULT CURRENT_TIMESTAMP,
            tool TEXT NOT NULL,
            scores TEXT NOT NULL
        );
        """
    )
    conn.commit()
    _migrate_competence_to_skills(conn)


def create_profile(conn: sqlite3.Connection) -> str:
    profile_id = str(uuid.uuid4())
    conn.execute(
        "INSERT INTO profile (id, created_at) VALUES (?, ?)",
        (profile_id, datetime.now()),
    )
    conn.commit()
    return profile_id


def get_profile(conn: sqlite3.Connection) -> sqlite3.Row | None:
    row = conn.execute("SELECT * FROM profile LIMIT 1").fetchone()
    return row


def ensure_profile(conn: sqlite3.Connection) -> sqlite3.Row:
    row = get_profile(conn)
    if not row:
        create_profile(conn)
        row = get_profile(conn)
    return row


def bump_total_katas(conn: sqlite3.Connection) -> None:
    conn.execute("UPDATE profile SET total_katas = total_katas + 1")
    conn.commit()


def bump_total_hints(conn: sqlite3.Connection) -> None:
    conn.execute("UPDATE profile SET total_hints_used = total_hints_used + 1")
    conn.commit()


def create_session(conn: sqlite3.Connection, kata_id: str) -> int:
    cursor = conn.execute(
        "INSERT INTO sessions (kata_id, started_at) VALUES (?, ?)",
        (kata_id, datetime.now()),
    )
    conn.commit()
    return cursor.lastrowid


def get_active_session(conn: sqlite3.Connection) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT * FROM sessions WHERE ended_at IS NULL ORDER BY started_at DESC LIMIT 1"
    ).fetchone()


def get_last_session(conn: sqlite3.Connection) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT * FROM sessions ORDER BY started_at DESC LIMIT 1"
    ).fetchone()


def get_last_finished_session(conn: sqlite3.Connection) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT * FROM sessions WHERE ended_at IS NOT NULL ORDER BY ended_at DESC LIMIT 1"
    ).fetchone()


def update_session_end(
    conn: sqlite3.Connection,
    session_id: int,
    duration: int,
    hint_level: int,
    success: bool,
    raw_log: str,
    ia_score: int | None,
) -> None:
    conn.execute(
        """
        UPDATE sessions
        SET ended_at = ?, duration_seconds = ?, hint_level_reached = ?,
            success = ?, raw_log = ?, ia_score = ?
        WHERE id = ?
        """,
        (datetime.now(), duration, hint_level, success, raw_log, ia_score, session_id),
    )
    conn.commit()


def update_hint_level(conn: sqlite3.Connection, session_id: int, level: int) -> None:
    conn.execute(
        "UPDATE sessions SET hint_level_reached = ? WHERE id = ?",
        (level, session_id),
    )
    conn.commit()


def mark_session_published(conn: sqlite3.Connection, session_id: int) -> None:
    conn.execute(
        "UPDATE sessions SET published_at = ? WHERE id = ?",
        (datetime.now(), session_id),
    )
    conn.commit()


def add_competence_snapshot(conn: sqlite3.Connection, category: str, delta: int = 5) -> None:
    latest = conn.execute(
        "SELECT * FROM competence_snapshots ORDER BY date DESC LIMIT 1"
    ).fetchone()
    defaults = {
        "pods": 0,
        "services": 0,
        "storage": 0,
        "networking": 0,
        "rbac": 0,
        "git": 0,
        "architecture": 0,
    }
    if latest:
        for key in defaults:
            defaults[key] = latest[key]
    current = defaults.get(category, 0)
    defaults[category] = min(100, current + delta)
    conn.execute(
        """
        INSERT INTO competence_snapshots
        (date, pods, services, storage, networking, rbac, git, architecture)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            datetime.now(),
            defaults["pods"],
            defaults["services"],
            defaults["storage"],
            defaults["networking"],
            defaults["rbac"],
            defaults["git"],
            defaults["architecture"],
        ),
    )
    conn.commit()


def get_all_competence_snapshots(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM competence_snapshots ORDER BY date ASC"
    ).fetchall()


def get_sessions(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM sessions ORDER BY started_at ASC"
    ).fetchall()


K8S_SKILL_KEYS = ["pods", "services", "storage", "networking", "rbac", "git", "architecture"]


def _migrate_competence_to_skills(conn: sqlite3.Connection) -> None:
    """One-shot migration from the legacy competence_snapshots table."""
    existing = conn.execute("SELECT COUNT(*) FROM skill_snapshots").fetchone()[0]
    if existing > 0:
        return
    rows = conn.execute(
        "SELECT * FROM competence_snapshots ORDER BY date ASC"
    ).fetchall()
    for row in rows:
        scores = {k: row[k] for k in K8S_SKILL_KEYS}
        conn.execute(
            "INSERT INTO skill_snapshots (date, tool, scores) VALUES (?, ?, ?)",
            (row["date"], "k8s", json.dumps(scores)),
        )
    conn.commit()


def _default_k8s_scores() -> dict:
    return {k: 0 for k in K8S_SKILL_KEYS}


def add_skill_snapshot(conn: sqlite3.Connection, tool: str, category: str, delta: int = 5) -> None:
    latest = conn.execute(
        "SELECT * FROM skill_snapshots WHERE tool = ? ORDER BY date DESC LIMIT 1",
        (tool,),
    ).fetchone()
    scores = _default_k8s_scores() if tool == "k8s" else {}
    if latest:
        scores = {**json.loads(latest["scores"])}
    if category in scores:
        scores[category] = min(100, scores[category] + delta)
    conn.execute(
        "INSERT INTO skill_snapshots (date, tool, scores) VALUES (?, ?, ?)",
        (datetime.now(), tool, json.dumps(scores)),
    )
    conn.commit()


def get_skill_snapshots(conn: sqlite3.Connection, tool: str = "k8s") -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM skill_snapshots WHERE tool = ? ORDER BY date ASC",
        (tool,),
    ).fetchall()
