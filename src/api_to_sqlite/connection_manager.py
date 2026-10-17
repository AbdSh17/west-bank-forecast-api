"""Connection handling. No weather SQL lives here."""

from collections.abc import Iterator
from contextlib import contextmanager

import mysql.connector
from mysql.connector.abstracts import MySQLConnectionAbstract

from api_to_sqlite import config


class ConfigError(Exception):
    """Raised when the MySQL settings are missing or invalid."""


class ConnectionManager:
    """Opens and closes connections to the MySQL database."""

    def __init__(self) -> None:
        """Read the MySQL settings from config and check them."""
        missing = [
            name
            for name, value in (
                ("MYSQL_USER", config.MYSQL_USER),
                ("MYSQL_PASSWORD", config.MYSQL_PASSWORD),
            )
            if not value
        ]
        if missing:
            raise ConfigError(
                f"Missing settings: {', '.join(missing)}. "
                "Copy .env.example to .env and fill them in."
            )
        try:
            self.port = int(config.MYSQL_PORT)
        except ValueError as error:
            raise ConfigError(
                f"MYSQL_PORT must be a number, got {config.MYSQL_PORT!r}"
            ) from error
        self.host = config.MYSQL_HOST
        self.user = config.MYSQL_USER
        self.password = config.MYSQL_PASSWORD
        self.database = config.MYSQL_DATABASE

    @contextmanager
    def connection(self) -> Iterator[MySQLConnectionAbstract]:
        """Yield an open connection and always close it afterwards."""
        conn = mysql.connector.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            database=self.database,
        )
        try:
            yield conn
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
