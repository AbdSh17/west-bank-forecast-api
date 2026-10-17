-- Days with precipitation above 0 per city from :since on.
SELECT c.name, COUNT(w.date) AS rainy_days
FROM cities AS c
LEFT JOIN daily_weather AS w
    ON w.city_id = c.id AND w.precipitation > 0 AND w.date >= :since
WHERE ( :city IS NULL OR c.name = :city COLLATE NOCASE )
GROUP BY c.id
ORDER BY rainy_days DESC, c.name
