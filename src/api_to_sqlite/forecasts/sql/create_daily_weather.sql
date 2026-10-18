-- Table for the daily forecast rows.
CREATE TABLE IF NOT EXISTS daily_weather (
    city_id INT NOT NULL,
    date DATE NOT NULL,
    temp_max DOUBLE,
    temp_min DOUBLE,
    precipitation DOUBLE,
    PRIMARY KEY (city_id, date),
    FOREIGN KEY (city_id) REFERENCES cities(id)
)
