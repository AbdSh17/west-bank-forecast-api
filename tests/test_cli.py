"""Tests for the fetch and report commands against the real weather_test database."""

from datetime import date, timedelta

import pytest

from api_to_sqlite import cli
from api_to_sqlite.forecasts import service
from api_to_sqlite.openmeteo.exceptions import FetchError

JENIN_LATITUDE = 32.46


def fake_forecast(latitude: float, longitude: float) -> dict:
    """Return 7 days starting today. Only the second day has rain."""
    days = [date.today() + timedelta(days=i) for i in range(7)]
    return {
        "daily": {
            "time": [day.isoformat() for day in days],
            "temperature_2m_max": [30.0 - i for i in range(7)],
            "temperature_2m_min": [20.0 - i for i in range(7)],
            "precipitation_sum": [0.0, 1.5, 0.0, 0.0, 0.0, 0.0, 0.0],
        }
    }


def failing_for_jenin(latitude: float, longitude: float) -> dict:
    """Behave like fake_forecast, but fail for Jenin."""
    if latitude == JENIN_LATITUDE:
        raise FetchError("The service is overloaded")
    return fake_forecast(latitude, longitude)


@pytest.fixture
def fake_api(monkeypatch):
    """Replace the real Open-Meteo call inside the service with the fake."""
    monkeypatch.setattr(service, "fetch_forecast", fake_forecast)


def count_rows(db, table: str) -> int:
    """Return the number of rows in a table of the test database."""
    with db.connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        cursor.close()
    return count


def test_fetch_stores_five_cities_and_35_rows(db, fake_api):
    assert cli.main(["fetch"]) == 0
    assert count_rows(db, "cities") == 5
    assert count_rows(db, "daily_weather") == 35


def test_second_fetch_does_not_duplicate_rows(db, fake_api):
    cli.main(["fetch"])
    assert cli.main(["fetch"]) == 0
    assert count_rows(db, "cities") == 5
    assert count_rows(db, "daily_weather") == 35


def test_fetch_stores_the_other_cities_when_one_fails(db, monkeypatch, capsys):
    monkeypatch.setattr(service, "fetch_forecast", failing_for_jenin)
    assert cli.main(["fetch"]) == 1
    assert count_rows(db, "cities") == 5
    assert count_rows(db, "daily_weather") == 28
    assert "Jenin" in capsys.readouterr().err


def test_report_on_an_empty_database_exits_with_1(db, capsys):
    assert cli.main(["report"]) == 1
    assert "No data found" in capsys.readouterr().err


def test_report_prints_the_three_tables(db, fake_api, capsys):
    cli.main(["fetch"])
    capsys.readouterr()
    assert cli.main(["report"]) == 0
    out = capsys.readouterr().out
    assert "1. Average maximum temperature per city" in out
    assert "2. Hottest day per city" in out
    assert "3. Days with rain per city" in out


def test_report_city_filter_ignores_letter_case(db, fake_api, capsys):
    cli.main(["fetch"])
    capsys.readouterr()
    assert cli.main(["report", "--city", "ramallah"]) == 0
    out = capsys.readouterr().out
    assert "Ramallah" in out
    assert "Hebron" not in out


def test_report_unknown_city_exits_with_1(db, fake_api, capsys):
    cli.main(["fetch"])
    capsys.readouterr()
    assert cli.main(["report", "--city", "nowhere"]) == 1
    assert "Unknown city: nowhere" in capsys.readouterr().err


def test_report_writes_the_three_csv_files(db, fake_api, tmp_path):
    cli.main(["fetch"])
    assert cli.main(["report", "--csv-dir", str(tmp_path)]) == 0
    for name in ("average_max.csv", "hottest_day.csv", "rainy_days.csv"):
        assert (tmp_path / name).exists()
