import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

DB_DIR = Path(__file__).resolve().parents[2] / "data"
DB_PATH = DB_DIR / "chat.db"
MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def get_db_connection() -> sqlite3.Connection:
    DB_DIR.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db() -> None:
    with get_db_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version TEXT PRIMARY KEY,
                applied_at TEXT NOT NULL
            )
            """
        )

        for migration_path in sorted(MIGRATIONS_DIR.glob("*.sql")):
            version = migration_path.stem
            if connection.execute(
                "SELECT 1 FROM schema_migrations WHERE version = ?",
                (version,),
            ).fetchone() is not None:
                continue

            migration_sql = migration_path.read_text(encoding="utf-8")
            connection.executescript(
                f"""
                BEGIN;
                {migration_sql}
                INSERT INTO schema_migrations (version, applied_at)
                VALUES ('{version}', strftime('%Y-%m-%dT%H:%M:%SZ', 'now'));
                COMMIT;
                """
            )


def create_conversation(title: str = "New chat") -> dict:
    conversation_id = str(uuid.uuid4())
    now = utc_now()

    with get_db_connection() as connection:
        connection.execute(
            "INSERT INTO conversations (id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (conversation_id, title, now, now),
        )

    return {
        "id": conversation_id,
        "title": title,
        "created_at": now,
        "updated_at": now,
    }


def list_conversations() -> list[dict]:
    with get_db_connection() as connection:
        rows = connection.execute(
            "SELECT id, title, created_at, updated_at FROM conversations ORDER BY updated_at DESC"
        ).fetchall()

    return [
        {
            "id": row["id"],
            "title": row["title"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }
        for row in rows
    ]


def delete_conversation(conversation_id: str) -> bool:
    with get_db_connection() as connection:
        cursor = connection.execute(
            "DELETE FROM conversations WHERE id = ?",
            (conversation_id,),
        )

    return cursor.rowcount > 0


def list_messages(conversation_id: str) -> list[dict]:
    with get_db_connection() as connection:
        conversation = connection.execute(
            "SELECT id FROM conversations WHERE id = ?",
            (conversation_id,),
        ).fetchone()

        if conversation is None:
            raise ValueError("Conversation not found")

        rows = connection.execute(
            """
            SELECT id, conversation_id, role, content, created_at
            FROM messages
            WHERE conversation_id = ?
            ORDER BY rowid ASC
            """,
            (conversation_id,),
        ).fetchall()

    return [
        {
            "id": row["id"],
            "conversation_id": row["conversation_id"],
            "role": row["role"],
            "content": row["content"],
            "created_at": row["created_at"],
        }
        for row in rows
    ]


def create_message(conversation_id: str, role: str, content: str) -> dict:
    with get_db_connection() as connection:
        conversation = connection.execute(
            "SELECT id FROM conversations WHERE id = ?",
            (conversation_id,),
        ).fetchone()

        if conversation is None:
            raise ValueError("Conversation not found")

        now = utc_now()
        message_id = str(uuid.uuid4())

        connection.execute(
            """
            INSERT INTO messages (id, conversation_id, role, content, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (message_id, conversation_id, role, content, now),
        )

        connection.execute(
            "UPDATE conversations SET updated_at = ? WHERE id = ?",
            (now, conversation_id),
        )

    return {
        "id": message_id,
        "conversation_id": conversation_id,
        "role": role,
        "content": content,
        "created_at": now,
    }
