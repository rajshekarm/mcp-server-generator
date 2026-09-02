class InsuranceMCPError(Exception):
    """Base exception for expected workflow errors."""


class NotFoundError(InsuranceMCPError):
    pass


class AuthorizationError(InsuranceMCPError):
    pass


class ValidationError(InsuranceMCPError):
    pass
