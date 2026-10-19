"""Errors raised by the cities rules."""


class CityNotFound(Exception):
    """Raised when no city has the requested name."""

    def __init__(self, name: str) -> None:
        super().__init__(f"No city named {name!r}.")
        self.name = name


class CityAlreadyExists(Exception):
    """Raised when a city with the same name is already stored."""

    def __init__(self, name: str) -> None:
        super().__init__(f"A city named {name!r} already exists.")
        self.name = name
