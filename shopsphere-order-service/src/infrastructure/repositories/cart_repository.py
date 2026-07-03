import uuid
from sqlalchemy import select
from src.domain.models import Cart
from src.domain.repository_interfaces import CartRepositoryInterface
from src.infrastructure.repositories.base import BaseSQLAlchemyRepository

class SQLAlchemyCartRepository(BaseSQLAlchemyRepository, CartRepositoryInterface):
    """SQLAlchemy implementation of the CartRepositoryInterface."""

    async def get_by_user_id(self, user_id: uuid.UUID) -> Cart | None:
        """Retrieve a user's active shopping cart, including its items."""
        result = await self.session.execute(
            select(Cart).filter(Cart.user_id == user_id)
        )
        return result.scalars().first()

    async def add(self, cart: Cart) -> Cart:
        """Add a new shopping cart."""
        self.session.add(cart)
        await self.session.flush()
        await self.session.refresh(cart)
        return cart

    async def update(self, cart: Cart) -> Cart:
        """Update a shopping cart's items or details."""
        self.session.add(cart)
        await self.session.flush()
        await self.session.refresh(cart)
        return cart

    async def delete(self, cart: Cart) -> None:
        """Delete a shopping cart."""
        await self.session.delete(cart)
        await self.session.flush()
