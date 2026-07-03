class BaseAppException(Exception):
    """Base exception for all application-specific errors."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class EntityNotFoundException(BaseAppException):
    """Exception raised when a requested product or category is not found."""
    pass


class EntityAlreadyExistsException(BaseAppException):
    """Exception raised when trying to create an entity that already exists (e.g. duplicate category slug)."""
    pass


class InventoryInsufficientException(BaseAppException):
    """Exception raised when there is not enough stock to fulfill a request."""
    pass


class TokenExpiredException(BaseAppException):
    """Exception raised when a JWT token has expired."""
    pass


class InvalidTokenException(BaseAppException):
    """Exception raised when a JWT token is malformed, invalid, or revoked."""
    pass


class PermissionDeniedException(BaseAppException):
    """Exception raised when a user does not have required roles/permissions."""
    pass
