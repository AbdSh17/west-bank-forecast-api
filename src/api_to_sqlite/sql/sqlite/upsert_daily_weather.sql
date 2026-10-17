-- Insert one daily row, or overwrite it if the city and date exist.
INSERT INTO daily_weather
    (city_id, date, temp_max, temp_min, precipitation)
VALUES
    (:city_id, :date, :temp_max, :temp_min, :precipitation)
ON CONFLICT(city_id, date) DO UPDATE SET
    temp_max = excluded.temp_max,
    temp_min = excluded.temp_min,
    precipitation = excluded.precipitation
