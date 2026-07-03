import uuid
from datetime import datetime, timezone
from typing import Any, Dict
from pydantic import BaseModel, Field

class EventEnvelope(BaseModel):
    event_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    event_type: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    payload: Dict[str, Any]


class OrderCreatedItem(BaseModel):
    product_id: uuid.UUID
    quantity: int


class OrderCreatedPayload(BaseModel):
    order_id: uuid.UUID
    user_id: uuid.UUID
    total_price: float
    items: list[OrderCreatedItem]
    shipping_address: str


class OrderCancelledPayload(BaseModel):
    order_id: uuid.UUID
    reason: str
    items: list[OrderCreatedItem]


class PaymentCompletedPayload(BaseModel):
    payment_id: uuid.UUID
    order_id: uuid.UUID
    amount: float
    transaction_id: str


class PaymentFailedPayload(BaseModel):
    order_id: uuid.UUID
    amount: float
    reason: str


class NotificationSentPayload(BaseModel):
    notification_id: uuid.UUID
    order_id: uuid.UUID
    recipient_email: str
    type: str
