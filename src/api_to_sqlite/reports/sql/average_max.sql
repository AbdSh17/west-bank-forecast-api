-- Average maximum temperature per city from the since date on, hottest first.
SELECT c.name, ROUND(AVG(w.temp_max), 1) AS avg_max
FROM cities AS c
JOIN daily_weather AS w ON w.city_id = c.id
WHERE w.date >= %(since)s
  AND ( %(city)s IS NULL OR c.name = %(city)s )
GROUP BY c.id
ORDER BY avg_max DESC
