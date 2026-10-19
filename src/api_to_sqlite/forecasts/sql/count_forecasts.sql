-- Number of forecast rows that match the same filters, ignoring paging.
SELECT COUNT(*)
FROM daily_weather AS w
JOIN cities AS c ON c.id = w.city_id
WHERE w.date >= %(start_date)s
  AND ( %(end_date)s IS NULL OR w.date <= %(end_date)s )
  AND ( %(city)s IS NULL OR c.name = %(city)s )
