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

Run the commands from the project folder, with the virtual environment active.

```bash
python -m api_to_sqlite fetch
python -m api_to_sqlite report
python -m api_to_sqlite report --city ramallah
python -m api_to_sqlite report --csv-dir reports
```

**`fetch`** requests one forecast per city and stores it in `data/weather.db`. The folder and the database are created on first run. If a city fails, the tool prints the reason to stderr, skips that city, stores the others and exits with code 1. Running `fetch` again updates existing rows and adds new days. It never creates duplicates.

**`report`** reads the stored data and prints three tables. The reports cover today and later days only. Older days stay in the database but are ignored. If the database has no data, it prints a message to stderr and exits with code 1.

| Option          | Effect                                                                                                                                                                              |
| --------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `--city NAME`   | Limits all three reports to one city. Letter case is ignored. An unknown city prints an error to stderr and exits with code 1.                                                      |
| `--csv-dir DIR` | Also writes `average_max.csv`, `hottest_day.csv` and `rainy_days.csv` into `DIR`. The folder is created if needed. Missing values become empty cells. Works together with `--city`. |

| Exit code | Meaning                                                                                  |
| --------- | ---------------------------------------------------------------------------------------- |
| 0         | Success                                                                                  |
| 1         | A city failed to fetch, `report` found no data, or the city given to `--city` is unknown |
| 2         | Invalid command-line usage                                                               |
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
- Reports filter on `date >= today`, computed in Python in the machine's local timezone and passed to SQL as a named parameter. The optional city filter uses a named parameter too, so user input is never placed in the SQL string.

## Sample report output

Output of `python -m api_to_sqlite report` for the forecast of 15 to 21 October 2026:

```text
1. Average maximum temperature per city
City      Avg max
--------  -------
Jericho   30.7 C
Jenin     27.1 C
Nablus    24.3 C
Ramallah  21.8 C
Hebron    21.5 C

2. Hottest day per city
City      Date        Max temp
--------  ----------  --------
Jericho   2026-10-15  31.8 C
Jenin     2026-10-15  28.5 C
Nablus    2026-10-15  25.0 C
Nablus    2026-10-21  25.0 C
Ramallah  2026-10-21  22.4 C
Hebron    2026-10-15  22.0 C

3. Days with rain per city
City      Rainy days
--------  ----------
Nablus    1
Hebron    0
Jenin     0
Jericho   0
Ramallah  0
```

Report 2 shows every day that ties for a city's maximum, which is why Nablus appears twice. Report 3 lists cities with no rainy days as 0. Rain means `precipitation` above 0, which includes rain, showers and snowfall.

## Tests

```bash
pytest
```

The tests cover `parse_daily` and use a saved response in `tests/data/sample_response.json`, so they need no internet.

## Project layout

```text
src/api_to_sqlite/
├── api.py        fetching, error handling and parsing
├── config.py     cities, API settings and database path
├── db.py         schema, upserts and report queries
├── main.py       command-line interface
└── __main__.py   entry point for python -m api_to_sqlite
tests/
├── data/sample_response.json
└── test_api.py
```
## Data source

[Open-Meteo Forecast API](https://open-meteo.com/en/docs). The free tier is for non-commercial use, with fewer than 10,000 calls per day. The tool makes 5 calls per `fetch`.
