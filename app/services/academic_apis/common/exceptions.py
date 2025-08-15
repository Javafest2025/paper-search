"""
Common exceptions for academic API clients.
"""


class RateLimitError(Exception):
    """Raised when API rate limits are exceeded"""

    pass


class APIError(Exception):
    """Raised when API returns an error response"""

    pass


class InvalidResponseError(Exception):
    """Raised when API response cannot be parsed or is invalid"""

    pass


class AuthenticationError(Exception):
    """Raised when API authentication fails"""

    pass


class QuotaExceededError(Exception):
    """Raised when API quota is exceeded"""

    pass
