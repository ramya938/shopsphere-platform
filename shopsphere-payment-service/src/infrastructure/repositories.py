import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.domain.models import Payment

class SQLAlchemyPaymentRepository:
    """SQLAlchemy concrete repository for managing Payment model entities."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, payment: Payment) -> Payment:
        self.session.add(payment)
        await self.session.flush()
        await self.session.refresh(payment)
        return payment

    async def get_by_id(self, payment_id: uuid.UUID) -> Payment | None:
        result = await self.session.execute(
            select(Payment).filter(Payment.id == payment_id)
        )
        return result.scalars().first()

    async def get_by_order_id(self, order_id: uuid.UUID) -> Payment | None:
        result = await self.session.execute(
            select(Payment).filter(Payment.order_id == order_id)
        )
        return result.scalars().first()
