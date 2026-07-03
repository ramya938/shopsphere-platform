import uuid
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from src.domain.models import OrderStatus

class OrderItemRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    product_id: uuid.UUID = Field(..., description="Unique UUID of the product.")
    quantity: int = Field(..., gt=0, description="Quantity to purchase, must be greater than 0.")


class DirectOrderCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    items: list[OrderItemRequest] = Field(..., min_items=1, description="List of items to order.")
    shipping_address: str = Field(..., min_length=1, description="Shipping destination address.")


class CartCheckout(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    shipping_address: str = Field(..., min_length=1, description="Shipping destination address.")


class OrderItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    order_id: uuid.UUID
    product_id: uuid.UUID
    quantity: int
    price_at_purchase: float


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    total_price: float
    status: OrderStatus
    shipping_address: str
    created_at: datetime
    updated_at: datetime
    items: list[OrderItemResponse] = []


class OrderStatusUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status: OrderStatus = Field(..., description="The target status transition for the order.")
