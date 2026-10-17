-- Average maximum temperature per city from :since on, hottest first.
SELECT c.name, ROUND(AVG(w.temp_max), 1) AS avg_max
FROM cities AS c
JOIN daily_weather AS w ON w.city_id = c.id
WHERE w.date >= :since
  AND ( :city IS NULL OR c.name = :city COLLATE NOCASE )
GROUP BY c.id
ORDER BY avg_max DESC
