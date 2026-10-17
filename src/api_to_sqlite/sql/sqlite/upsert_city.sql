-- Insert a city, or update its coordinates if the name exists.
INSERT INTO cities (name, latitude, longitude)
VALUES (:name, :latitude, :longitude)
ON CONFLICT(name) DO UPDATE SET
    latitude = excluded.latitude,
    longitude = excluded.longitude
