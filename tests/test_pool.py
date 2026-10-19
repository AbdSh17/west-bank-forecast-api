"""Tests for the wait rule when the connection pool is empty."""

import threading
import time

import pytest

from api_to_sqlite import database
from api_to_sqlite.database import DatabaseConnectionError
from api_to_sqlite.settings import get_settings


@pytest.fixture
def small_pool(monkeypatch):
    """Make the manager use a pool of one connection. Request it before db."""
    monkeypatch.setenv("MYSQL_POOL_SIZE", "1")
    get_settings.cache_clear()


def test_a_waiting_borrow_gets_the_connection_when_it_is_freed(small_pool, db):
    assert db.pool_size == 1

    def hold() -> None:
        with db.connection():
            time.sleep(0.3)

    thread = threading.Thread(target=hold)
    thread.start()
    time.sleep(0.05)
    start = time.monotonic()
    with db.connection():
        waited = time.monotonic() - start
    thread.join()
    assert waited >= 0.1


def test_borrow_fails_after_the_wait_when_the_pool_stays_empty(
    small_pool, db, monkeypatch
):
    monkeypatch.setattr(database, "POOL_WAIT_SECONDS", 0.2)
    with db.connection():
        start = time.monotonic()
        with pytest.raises(DatabaseConnectionError):
            with db.connection():
                pass
        assert time.monotonic() - start >= 0.15


def test_a_failed_wait_does_not_leak_a_slot(small_pool, db, monkeypatch):
    monkeypatch.setattr(database, "POOL_WAIT_SECONDS", 0.1)
    with db.connection():
        with pytest.raises(DatabaseConnectionError):
            with db.connection():
                pass
    with db.connection() as conn:
        assert conn is not None
