"""Tests for parsing the Open-Meteo daily response. No network is used."""

import json
from pathlib import Path

import pytest

from api_to_sqlite.openmeteo.parse import parse_daily

SAMPLE_PATH = Path(__file__).parent.parent / "data" / "sample_response.json"


@pytest.fixture
def sample() -> dict:
    """Load a fresh copy of the saved Ramallah response for each test."""
    return json.loads(SAMPLE_PATH.read_text())


def test_one_record_per_day(sample):
    assert len(parse_daily(sample)) == 7


def test_records_have_the_expected_keys(sample):
    for record in parse_daily(sample):
        assert set(record) == {"date", "temp_max", "temp_min", "precipitation"}


def test_first_record_matches_by_position(sample):
    assert parse_daily(sample)[0] == {
        "date": "2026-10-12",
        "temp_max": 24.3,
        "temp_min": 17.3,
        "precipitation": 0.3,
    }


def test_last_record_matches_by_position(sample):
    assert parse_daily(sample)[-1] == {
        "date": "2026-10-18",
        "temp_max": 22.2,
        "temp_min": 13.9,
        "precipitation": 0.0,
    }


def test_none_value_passes_through(sample):
    sample["daily"]["temperature_2m_max"][0] = None
    assert parse_daily(sample)[0]["temp_max"] is None


def test_empty_lists_give_no_records():
    data = {
        "daily": {
            "time": [],
            "temperature_2m_max": [],
            "temperature_2m_min": [],
            "precipitation_sum": [],
        }
    }
    assert parse_daily(data) == []


def test_missing_daily_key_raises_key_error():
    with pytest.raises(KeyError):
        parse_daily({})
