import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Numeric, Uuid
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func

class Base(DeclarativeBase):
    """Base class for database models."""
    pass

class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, nullable=False, index=True
    )
    amount: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(50), nullable=False  # "COMPLETED" or "FAILED"
    )
    transaction_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<Payment id={self.id} order_id={self.order_id} amount={self.amount} status={self.status}>"
