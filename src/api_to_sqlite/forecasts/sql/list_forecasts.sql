-- Daily forecasts with the city name, filtered by date and city, one page.
SELECT c.name, w.date, w.temp_max, w.temp_min, w.precipitation
FROM daily_weather AS w
JOIN cities AS c ON c.id = w.city_id
WHERE w.date >= %(start_date)s
  AND ( %(end_date)s IS NULL OR w.date <= %(end_date)s )
  AND ( %(city)s IS NULL OR c.name = %(city)s )
ORDER BY c.id, w.date
LIMIT %(limit)s OFFSET %(offset)s
