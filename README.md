# api-to-sqlite

A command-line tool that fetches 7-day weather forecasts from the Open-Meteo API for five West Bank cities, stores them in SQLite and prints three reports.

Cities: Ramallah, Nablus, Hebron, Jenin and Jericho. No API key is needed.

## Setup

Requires Python 3.10 or newer.

```bash
git clone git@github.com:AbdSh17/api-to-sqlite.git
cd api-to-sqlite
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

`pip install -r requirements.txt` installs the pinned `requests` and its dependencies. `pip install -e .` makes the `api_to_sqlite` package importable, because the code lives in `src/`.

## Usage

Run both commands from the project folder, with the virtual environment active.

```bash
python -m api_to_sqlite fetch
python -m api_to_sqlite report
```

**`fetch`** requests one forecast per city and stores it in `data/weather.db`. The folder and the database are created on first run. If a city fails, the tool prints the reason to stderr, skips that city, stores the others and exits with code 1. Running `fetch` again updates existing rows and adds new days. It never creates duplicates.

**`report`** reads the stored data and prints three tables. If the database has no data, it prints a message to stderr and exits with code 1.

| Exit code | Meaning |
|---|---|
| 0 | Success |
| 1 | A city failed to fetch, or `report` found no data |
| 2 | Invalid command-line usage |

## Table design

```text
cities                          daily_weather
------                          -------------
id        INTEGER PRIMARY KEY   city_id        INTEGER REFERENCES cities(id)
name      TEXT UNIQUE           date           TEXT (ISO 8601, YYYY-MM-DD)
latitude  REAL                   temp_max       REAL
longitude REAL                   temp_min       REAL
                                precipitation  REAL
                                PRIMARY KEY (city_id, date)
```

- `daily_weather` has one row per city per day. The primary key `(city_id, date)` makes that pair unique.
- `city_id` is a foreign key to `cities(id)`. Foreign keys are enforced by turning on `PRAGMA foreign_keys` for every connection.
- Dates are stored as ISO text, which sorts correctly. SQLite has no date type.
- The three weather columns allow `NULL`, in case the API sends no value for a day.
- The stored coordinates are the ones set in `src/api_to_sqlite/config.py`. The API returns the centre of its own grid cell, which can differ by a few kilometres.
- Rows are written with an upsert (`INSERT ... ON CONFLICT DO UPDATE`) and parameterized `?` placeholders. The forecast window moves forward by one day, so most dates repeat between runs. The upsert overwrites the overlapping days with the newer forecast and inserts the new day. `INSERT OR REPLACE` is not used, because it deletes and re-inserts the row, which can break foreign keys.
- The database file is in `.gitignore`, because it is generated data that anyone can recreate with `fetch`.

## Sample report output

Output of `python -m api_to_sqlite report` for the forecast of 12 to 18 October 2026:

```text
1. Average maximum temperature per city
City      Avg max
--------  -------
Jericho   32.3 C
Jenin     28.7 C
Nablus    26.0 C
Ramallah  23.5 C
Hebron    23.0 C

2. Hottest day per city
City      Date        Max temp
--------  ----------  --------
Jericho   2026-10-12  36.2 C
Jenin     2026-10-14  30.8 C
Nablus    2026-10-14  28.4 C
Ramallah  2026-10-14  25.4 C
Hebron    2026-10-14  25.1 C

3. Days with rain per city
City      Rainy days
--------  ----------
Jenin     1
Jericho   1
Nablus    1
Hebron    0
Ramallah  0
```

Report 2 shows every day that ties for a city's maximum. Report 3 lists cities with no rainy days as 0. Rain means `precipitation` above 0, which includes rain, showers and snowfall.

## Data source

[Open-Meteo Forecast API](https://open-meteo.com/en/docs). The free tier is for non-commercial use, with fewer than 10,000 calls per day. The tool makes 5 calls per `fetch`.
