import uuid
from typing import Sequence
from sqlalchemy import select, delete
from src.domain.models import User, RefreshToken
from src.domain.repository_interfaces import UserRepositoryInterface, RefreshTokenRepositoryInterface
from src.infrastructure.repositories.base import BaseSQLAlchemyRepository

class SQLAlchemyUserRepository(BaseSQLAlchemyRepository, UserRepositoryInterface):
    """SQLAlchemy implementation of the UserRepositoryInterface."""

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        result = await self.session.execute(
            select(User).filter(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(
            select(User).filter(User.email == email)
        )
        return result.scalar_one_or_none()

    async def add(self, user: User) -> User:
        self.session.add(user)
        # Flush sends the insert statement to DB to populate database-generated values
        # like UUIDs and timestamps without committing the transaction.
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def update(self, user: User) -> User:
        # SQLAlchemy tracks changes on objects that are part of the session.
        # We just flush to synchronize the state with the database.
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def delete(self, user: User) -> None:
        await self.session.delete(user)
        await self.session.flush()

    async def list_all(self, skip: int = 0, limit: int = 100) -> Sequence[User]:
        result = await self.session.execute(
            select(User).offset(skip).limit(limit)
        )
        return result.scalars().all()


class SQLAlchemyRefreshTokenRepository(BaseSQLAlchemyRepository, RefreshTokenRepositoryInterface):
    """SQLAlchemy implementation of the RefreshTokenRepositoryInterface."""

    async def get_by_token(self, token: str) -> RefreshToken | None:
        result = await self.session.execute(
            select(RefreshToken).filter(RefreshToken.token == token)
        )
        return result.scalar_one_or_none()

    async def add(self, refresh_token: RefreshToken) -> RefreshToken:
        self.session.add(refresh_token)
        await self.session.flush()
        await self.session.refresh(refresh_token)
        return refresh_token

    async def revoke_all_for_user(self, user_id: uuid.UUID) -> None:
        await self.session.execute(
            delete(RefreshToken).filter(RefreshToken.user_id == user_id)
        )
        await self.session.flush()
