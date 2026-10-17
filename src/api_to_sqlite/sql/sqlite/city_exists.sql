-- One row if a city with this name exists, in any letter case.
SELECT 1 FROM cities WHERE name = :city COLLATE NOCASE
