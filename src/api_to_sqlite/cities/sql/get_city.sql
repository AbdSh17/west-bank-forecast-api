-- One city by name, in any letter case.
SELECT id, name, latitude, longitude FROM cities WHERE name = %(city)s
