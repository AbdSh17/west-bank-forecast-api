-- Days with precipitation above 0 per city from the since date on.
SELECT c.name, COUNT(w.date) AS rainy_days
FROM cities AS c
LEFT JOIN daily_weather AS w
    ON w.city_id = c.id AND w.precipitation > 0 AND w.date >= %(since)s
WHERE ( %(city)s IS NULL OR c.name = %(city)s )
GROUP BY c.id
ORDER BY rainy_days DESC, c.name
