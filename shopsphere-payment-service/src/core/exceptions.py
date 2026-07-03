class BaseAppException(Exception):
    """Base exception for all application-specific errors."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class EntityNotFoundException(BaseAppException):
    """Exception raised when a requested resource is not found."""
    pass


class EntityAlreadyExistsException(BaseAppException):
    """Exception raised when trying to create a resource that already exists."""
    pass


class PaymentProcessingException(BaseAppException):
    """Exception raised when payment processing fails."""
    pass
