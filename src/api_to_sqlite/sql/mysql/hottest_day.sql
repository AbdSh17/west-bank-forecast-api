-- Each city's hottest day from the since date on. Ties show every tied day.
SELECT c.name, w.date, w.temp_max
FROM cities AS c
JOIN daily_weather AS w ON w.city_id = c.id
WHERE w.date >= %(since)s
  AND ( %(city)s IS NULL OR c.name = %(city)s )
  AND w.temp_max = (
      SELECT MAX(temp_max)
      FROM daily_weather
      WHERE city_id = c.id AND date >= %(since)s
  )
ORDER BY w.temp_max DESC, c.name, w.date
