-- Table for the cities.
CREATE TABLE IF NOT EXISTS cities (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    latitude DOUBLE NOT NULL,
    longitude DOUBLE NOT NULL
)
