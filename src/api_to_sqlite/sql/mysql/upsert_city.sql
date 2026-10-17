-- Insert a city, or update its coordinates if the name exists.
INSERT INTO cities (name, latitude, longitude)
VALUES (%(name)s, %(latitude)s, %(longitude)s) AS new_row
ON DUPLICATE KEY UPDATE
    latitude = new_row.latitude,
    longitude = new_row.longitude
