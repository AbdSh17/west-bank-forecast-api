"""Tests for the ConnectionManager singleton. No database is used."""

import pytest

from api_to_sqlite import config
from api_to_sqlite.database import ConfigError, ConnectionManager


@pytest.fixture(autouse=True)
def valid_settings(monkeypatch):
    """Give the manager valid settings and start each test with no shared instance."""
    monkeypatch.setattr(config, "MYSQL_USER", "test_user")
    monkeypatch.setattr(config, "MYSQL_PASSWORD", "test_password")
    ConnectionManager.reset()
    yield
    ConnectionManager.reset()


def test_returns_the_same_object():
    assert ConnectionManager() is ConnectionManager()


def test_reset_gives_a_new_object():
    first = ConnectionManager()
    ConnectionManager.reset()
    assert ConnectionManager() is not first


def test_failed_setup_leaves_no_instance(monkeypatch):
    monkeypatch.setattr(config, "MYSQL_PASSWORD", "")
    with pytest.raises(ConfigError):
        ConnectionManager()
    assert ConnectionManager._instance is None
