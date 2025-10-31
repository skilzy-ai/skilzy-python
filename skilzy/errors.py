# skilzy/errors.py

class SkilzyError(Exception):
    """Base exception for all skilzy-sdk related errors."""
    pass


class SkilzyAPIError(SkilzyError):
    """Raised when the API returns a non-2xx status code."""
    
    def __init__(self, message, status_code):
        super().__init__(f"API Error {status_code}: {message}")
        self.status_code = status_code


class SkilzyNotFound(SkilzyAPIError):
    """Raised for 404 Not Found errors."""
    pass


class SkilzyAuthenticationError(SkilzyAPIError):
    """Raised for 401 Unauthorized errors."""
    pass


class SkilzyPermissionError(SkilzyAPIError):
    """Raised for 403 Forbidden errors."""
    pass


class SkilzyConflictError(SkilzyAPIError):
    """Raised for 409 Conflict errors."""
    pass