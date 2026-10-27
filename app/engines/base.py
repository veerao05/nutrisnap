"""Shared error type for vision engines."""


class EngineError(Exception):
    """An engine failed; status_code is the HTTP status the API should return."""

    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.status_code = status_code
