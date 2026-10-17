"""Command-line entry point: the fetch and report commands."""

import argparse
import csv
import sys
from pathlib import Path

from api_to_sqlite.api import FetchError, fetch_forecast, parse_daily
from api_to_sqlite.config import CITIES
from api_to_sqlite.connection_manager import ConnectionManager
from api_to_sqlite.weather_dao import WeatherDAO


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser with the fetch and report commands."""
    parser = argparse.ArgumentParser(
        prog="python -m api_to_sqlite",
        description="Fetch Open-Meteo forecasts into SQLite and report on them.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("fetch", help="fetch forecasts and store them")
    report = subparsers.add_parser("report", help="print reports from the stored data")
    report.add_argument("--city", help="limit the reports to one city")
    report.add_argument(
        "--csv-dir", help="also write each report as a CSV file into this folder"
    )
    return parser


def format_temp(value: float | None) -> str:
    """Format a temperature in Celsius, or n/a when it is missing."""
    return "n/a" if value is None else f"{value:.1f} C"


def print_table(title: str, headers: list[str], rows: list[list[str]]) -> None:
    """Print a titled table with columns padded to their widest value."""
    widths = [max(len(cell) for cell in column) for column in zip(headers, *rows)]
    print(title)
    print("  ".join(h.ljust(w) for h, w in zip(headers, widths)))
    print("  ".join("-" * w for w in widths))
    for row in rows:
        print("  ".join(cell.ljust(w) for cell, w in zip(row, widths)))
    print()


def write_csv(path: Path, headers: list[str], rows: list[tuple]) -> None:
    """Write a report to a CSV file; a missing value becomes an empty cell."""
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(headers)
        for row in rows:
            writer.writerow(["" if cell is None else cell for cell in row])


def cmd_fetch(manager: ConnectionManager, dao: WeatherDAO) -> int:
    """Fetch every city, store the successes and return 1 if any city failed."""
    with manager.connection() as conn:
        dao.create_schema(conn)

    failed: list[str] = []
    for name, latitude, longitude in CITIES:
        try:
            records = parse_daily(fetch_forecast(latitude, longitude))
        except FetchError as error:
            print(f"{name}: failed - {error}", file=sys.stderr)
            failed.append(name)
            continue
        with manager.connection() as conn:
            city_id = dao.upsert_city(conn, name, latitude, longitude)
            dao.upsert_daily_weather(conn, city_id, records)
            conn.commit()
        print(f"{name}: stored {len(records)} days")

    if failed:
        print(
            f"Fetch finished with errors. Failed: {', '.join(failed)}",
            file=sys.stderr,
        )
        return 1
    print(f"Fetched and stored {len(CITIES)} cities.")
    return 0


def cmd_report(
    manager: ConnectionManager,
    dao: WeatherDAO,
    city: str | None = None,
    csv_dir: str | None = None,
) -> int:
    """Print the three reports, optionally export them as CSV, and return the exit code."""
    with manager.connection() as conn:
        dao.create_schema(conn)
        if not dao.has_data(conn):
            print("No data found. Run fetch first.", file=sys.stderr)
            return 1
        if city is not None and not dao.city_exists(conn, city):
            print(f"Unknown city: {city}", file=sys.stderr)
            return 1
        averages = dao.average_max_temp_per_city(conn, city=city)
        hottest = dao.hottest_day_per_city(conn, city=city)
        rainy = dao.rainy_days_per_city(conn, city=city)

    if csv_dir is not None:
        out = Path(csv_dir)
        out.mkdir(parents=True, exist_ok=True)
        write_csv(out / "average_max.csv", ["City", "Avg max (C)"], averages)
        write_csv(out / "hottest_day.csv", ["City", "Date", "Max temp (C)"], hottest)
        write_csv(out / "rainy_days.csv", ["City", "Rainy days"], rainy)
        print(f"CSV files written to {out}")

    print_table(
        "1. Average maximum temperature per city",
        ["City", "Avg max"],
        [[name, format_temp(avg)] for name, avg in averages],
    )
    print_table(
        "2. Hottest day per city",
        ["City", "Date", "Max temp"],
        [[name, str(date), format_temp(temp)] for name, date, temp in hottest],
    )
    print_table(
        "3. Days with rain per city",
        ["City", "Rainy days"],
        [[name, str(days)] for name, days in rainy],
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    """Parse the arguments, run the chosen command and return the exit code."""
    args = build_parser().parse_args(argv)
    manager = ConnectionManager()
    dao = WeatherDAO()
    if args.command == "fetch":
        return cmd_fetch(manager, dao)
    return cmd_report(manager, dao, args.city, args.csv_dir)
