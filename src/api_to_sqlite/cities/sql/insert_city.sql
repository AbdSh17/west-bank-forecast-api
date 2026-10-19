-- Insert a new city. A duplicate name raises a duplicate-key error.
INSERT INTO cities (name, latitude, longitude)
VALUES (%(name)s, %(latitude)s, %(longitude)s)
