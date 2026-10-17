-- Table for the daily forecast rows.
CREATE TABLE IF NOT EXISTS daily_weather (
    city_id INTEGER NOT NULL REFERENCES cities(id),
    date TEXT NOT NULL,
    temp_max REAL,
    temp_min REAL,
    precipitation REAL,
    PRIMARY KEY (city_id, date)
)
