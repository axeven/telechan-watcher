import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "telechan.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS channels (
    id INTEGER PRIMARY KEY,
    username TEXT,
    title TEXT NOT NULL,
    label TEXT NOT NULL,
    paused INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_id INTEGER NOT NULL REFERENCES channels(id),
    sender TEXT,
    text TEXT NOT NULL,
    sent_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_messages_channel_time ON messages(channel_id, sent_at);
"""


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    conn.executescript(SCHEMA)
    columns = {row["name"] for row in conn.execute("PRAGMA table_info(channels)")}
    if "paused" not in columns:
        conn.execute("ALTER TABLE channels ADD COLUMN paused INTEGER NOT NULL DEFAULT 0")
    conn.commit()
    conn.close()


def upsert_channel(conn, channel_id, username, title):
    conn.execute(
        """
        INSERT INTO channels (id, username, title, label)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET username = excluded.username, title = excluded.title
        """,
        (channel_id, username, title, title),
    )
    conn.commit()


def is_paused(conn, channel_id):
    row = conn.execute("SELECT paused FROM channels WHERE id = ?", (channel_id,)).fetchone()
    return bool(row and row["paused"])


def set_paused(conn, channel_id, paused):
    conn.execute("UPDATE channels SET paused = ? WHERE id = ?", (1 if paused else 0, channel_id))
    conn.commit()


def insert_message(conn, channel_id, sender, text, sent_at):
    conn.execute(
        "INSERT INTO messages (channel_id, sender, text, sent_at) VALUES (?, ?, ?, ?)",
        (channel_id, sender, text, sent_at),
    )
    conn.commit()


def list_channels(conn):
    return conn.execute(
        """
        SELECT c.id, c.username, c.title, c.label, c.paused,
               COUNT(m.id) AS message_count,
               MAX(m.sent_at) AS latest_at
        FROM channels c
        LEFT JOIN messages m ON m.channel_id = c.id
        GROUP BY c.id
        ORDER BY latest_at DESC
        """
    ).fetchall()


def get_channel(conn, channel_id):
    return conn.execute("SELECT * FROM channels WHERE id = ?", (channel_id,)).fetchone()


def list_messages(conn, channel_id):
    return conn.execute(
        "SELECT * FROM messages WHERE channel_id = ? ORDER BY sent_at DESC",
        (channel_id,),
    ).fetchall()


def update_label(conn, channel_id, label):
    conn.execute("UPDATE channels SET label = ? WHERE id = ?", (label, channel_id))
    conn.commit()
