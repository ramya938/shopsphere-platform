import uuid
from typing import Sequence
from sqlalchemy import select
from src.domain.models import Order
from src.domain.repository_interfaces import OrderRepositoryInterface
from src.infrastructure.repositories.base import BaseSQLAlchemyRepository

class SQLAlchemyOrderRepository(BaseSQLAlchemyRepository, OrderRepositoryInterface):
    """SQLAlchemy implementation of the OrderRepositoryInterface."""

    async def get_by_id(self, order_id: uuid.UUID) -> Order | None:
        """Retrieve an order by its UUID, including items."""
        result = await self.session.execute(
            select(Order).filter(Order.id == order_id)
        )
        return result.scalars().first()

    async def add(self, order: Order) -> Order:
        """Add a new order to database."""
        self.session.add(order)
        await self.session.flush()
        await self.session.refresh(order)
        return order

    async def update(self, order: Order) -> Order:
        """Update an existing order (status, etc.)."""
        self.session.add(order)
        await self.session.flush()
        await self.session.refresh(order)
        return order

    async def list_by_user(self, user_id: uuid.UUID) -> Sequence[Order]:
        """Retrieve all orders placed by a specific user, ordered by creation date desc."""
        result = await self.session.execute(
            select(Order).filter(Order.user_id == user_id).order_by(Order.created_at.desc())
        )
        return result.scalars().all()

    async def list_all(self, skip: int = 0, limit: int = 100) -> Sequence[Order]:
        """Retrieve all orders, ordered by creation date desc (Admin view)."""
        result = await self.session.execute(
            select(Order).order_by(Order.created_at.desc()).offset(skip).limit(limit)
        )
        return result.scalars().all()
