"""Connection handling. No weather SQL lives here."""

import time
from collections.abc import Iterator
from contextlib import contextmanager

import mysql.connector
from mysql.connector.abstracts import MySQLConnectionAbstract

from api_to_sqlite import config

CONNECT_ATTEMPTS = 3
RETRY_DELAY_SECONDS = 1
CONNECT_TIMEOUT_SECONDS = 5
# MySQL client error numbers for "server not reachable". Only 2003 was seen here.
TRANSIENT_ERRNOS = {2002, 2003, 2013}


class ConfigError(Exception):
    """Raised when the MySQL settings are missing or invalid."""


class DatabaseConnectionError(Exception):
    """Raised when the MySQL server cannot be reached or refuses the login."""


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

    def _connect(self) -> MySQLConnectionAbstract:
        """Open a connection, retrying with backoff while the server is unreachable."""
        attempt = 1
        while True:
            try:
                return mysql.connector.connect(
                    host=self.host,
                    port=self.port,
                    user=self.user,
                    password=self.password,
                    database=self.database,
                    connection_timeout=CONNECT_TIMEOUT_SECONDS,
                )
            except mysql.connector.Error as error:
                if error.errno not in TRANSIENT_ERRNOS:
                    raise DatabaseConnectionError(
                        f"MySQL refused the connection: {error}"
                    ) from error
                if attempt == CONNECT_ATTEMPTS:
                    raise DatabaseConnectionError(
                        f"Could not reach MySQL after {CONNECT_ATTEMPTS} attempts: "
                        f"{error}"
                    ) from error
                time.sleep(RETRY_DELAY_SECONDS * 2 ** (attempt - 1))
                attempt += 1

    @contextmanager
    def connection(self) -> Iterator[MySQLConnectionAbstract]:
        """Yield an open connection and always close it afterwards."""
        conn = self._connect()
        try:
            yield conn
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
