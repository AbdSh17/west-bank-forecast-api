"""Connection handling. No weather SQL lives here."""

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from api_to_sqlite.config import DB_PATH


class ConnectionManager:
    """Opens and closes connections to the SQLite database."""

    def __init__(self, db_path: Path = DB_PATH) -> None:
        """Store the path of the database file."""
        self.db_path = db_path

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        """Yield an open connection and always close it afterwards."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
