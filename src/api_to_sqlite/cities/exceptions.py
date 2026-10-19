"""Errors raised by the cities rules."""


class CityNotFound(Exception):
    """Raised when no city has the requested name."""

    def __init__(self, name: str) -> None:
        super().__init__(f"No city named {name!r}.")
        self.name = name
