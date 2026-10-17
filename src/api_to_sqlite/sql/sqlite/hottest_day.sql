-- Each city's hottest day from :since on. Ties show every tied day.
SELECT c.name, w.date, w.temp_max
FROM cities AS c
JOIN daily_weather AS w ON w.city_id = c.id
WHERE w.date >= :since
  AND ( :city IS NULL OR c.name = :city COLLATE NOCASE )
  AND w.temp_max = (
      SELECT MAX(temp_max)
      FROM daily_weather
      WHERE city_id = c.id AND date >= :since
  )
ORDER BY w.temp_max DESC, c.name, w.date
