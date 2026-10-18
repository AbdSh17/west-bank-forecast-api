"""Turn an Open-Meteo response into one record per day."""


def parse_daily(data: dict) -> list[dict]:
    """Turn the parallel daily lists into one record per day."""
    daily = data["daily"]
    return [
        {
            "date": date,
            "temp_max": temp_max,
            "temp_min": temp_min,
            "precipitation": precipitation,
        }
        for date, temp_max, temp_min, precipitation in zip(
            daily["time"],
            daily["temperature_2m_max"],
            daily["temperature_2m_min"],
            daily["precipitation_sum"],
        )
    ]
