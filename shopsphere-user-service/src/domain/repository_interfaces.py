from abc import ABC, abstractmethod
import uuid
from typing import Sequence
from src.domain.models import User, RefreshToken

class UserRepositoryInterface(ABC):
    """Abstract interface for user persistence operations."""

    @abstractmethod
    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        """Retrieve a user by their unique UUID."""
        pass

    @abstractmethod
    async def get_by_email(self, email: str) -> User | None:
        """Retrieve a user by their email address."""
        pass

    @abstractmethod
    async def add(self, user: User) -> User:
        """Add a new user to persistence."""
        pass

    @abstractmethod
    async def update(self, user: User) -> User:
        """Update an existing user."""
        pass

    @abstractmethod
    async def delete(self, user: User) -> None:
        """Remove a user from persistence."""
        pass

    @abstractmethod
    async def list_all(self, skip: int = 0, limit: int = 100) -> Sequence[User]:
        """Retrieve a paginated list of users (Admin helper)."""
        pass


class RefreshTokenRepositoryInterface(ABC):
    """Abstract interface for refresh token operations."""

    @abstractmethod
    async def get_by_token(self, token: str) -> RefreshToken | None:
        """Retrieve a refresh token record by its token string."""
        pass

    @abstractmethod
    async def add(self, refresh_token: RefreshToken) -> RefreshToken:
        """Add a new refresh token to persistence."""
        pass

    @abstractmethod
    async def revoke_all_for_user(self, user_id: uuid.UUID) -> None:
        """Revoke (or delete) all refresh tokens associated with a user."""
        pass
