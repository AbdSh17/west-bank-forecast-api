"""Connection handling. No weather SQL lives here."""

import time
from collections.abc import Iterator
from contextlib import contextmanager

import mysql.connector
from mysql.connector.pooling import MySQLConnectionPool, PooledMySQLConnection

# MySQLConnectionPool: The pool manager that holds the connections
# PooledMySQLConnection: One borrowed connection

from api_to_sqlite import config

import threading

Connection = PooledMySQLConnection

MAX_POOL_SIZE = 32
POOL_NAME = "weather_pool"
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
    """Hands out connections from a fixed-size MySQL connection pool."""

    _instance: "ConnectionManager | None" = None
    _instance_lock = threading.Lock()

    # __new__ creates the object
    # __init__ fills it in
    def __new__(cls) -> "ConnectionManager":
        """Return the one shared manager, creating it on the first call."""
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    instance = super().__new__(cls)
                    instance._initialize()
                    cls._instance = instance
        return cls._instance

    def _initialize(self) -> None:
        """Read the MySQL settings from config and check them.

        Attributes:

            port: MySQL port, converted to int.
            pool_size: Connection pool size, between 1 and MAX_POOL_SIZE.
            host: MySQL host.
            user: MySQL user.
            password: MySQL password.
            database: Database name.
            _pool: MySQLConnectionPool or None. Not created yet.

        """

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

        try:
            self.pool_size = int(config.MYSQL_POOL_SIZE)
        except ValueError as error:
            raise ConfigError(
                f"MYSQL_POOL_SIZE must be a number, got {config.MYSQL_POOL_SIZE!r}"
            ) from error
        if not 1 <= self.pool_size <= MAX_POOL_SIZE:
            raise ConfigError(
                f"MYSQL_POOL_SIZE must be between 1 and {MAX_POOL_SIZE}, "
                f"got {self.pool_size}"
            )

        self.host = config.MYSQL_HOST
        self.user = config.MYSQL_USER
        self.password = config.MYSQL_PASSWORD
        self.database = config.MYSQL_DATABASE
        self._pool_lock = threading.Lock()
        self._pool: MySQLConnectionPool | None = None

    def _create_pool(self) -> MySQLConnectionPool:
        """Create the pool, retrying with backoff while the server is unreachable."""
        attempt = 1
        while True:
            try:
                return MySQLConnectionPool(
                    pool_name=POOL_NAME,
                    pool_size=self.pool_size,
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
    def connection(self) -> Iterator[Connection]:
        """Borrow a connection from the pool and always give it back afterwards."""
        if self._pool is None:
            with self._pool_lock:
                if self._pool is None:
                    self._pool = self._create_pool()
        try:
            conn = self._pool.get_connection()
        except mysql.connector.PoolError as error:
            raise DatabaseConnectionError(
                f"No free connection in the pool: {error}"
            ) from error
        try:
            yield conn
        finally:
            try:
                conn.rollback()
            finally:
                conn.close()

    @classmethod
    def reset(cls) -> None:
        """Forget the shared manager. Only for tests."""
        with cls._instance_lock:
            cls._instance = None
