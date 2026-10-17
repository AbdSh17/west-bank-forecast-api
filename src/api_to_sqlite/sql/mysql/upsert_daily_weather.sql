-- Insert one daily row, or overwrite it if the city and date exist.
INSERT INTO daily_weather
    (city_id, date, temp_max, temp_min, precipitation)
VALUES
    (%(city_id)s, %(date)s, %(temp_max)s, %(temp_min)s, %(precipitation)s) AS new_row
ON DUPLICATE KEY UPDATE
    temp_max = new_row.temp_max,
    temp_min = new_row.temp_min,
    precipitation = new_row.precipitation
