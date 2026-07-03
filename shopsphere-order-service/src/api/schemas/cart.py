import uuid
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class CartItemAdd(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    product_id: uuid.UUID = Field(..., description="The unique UUID of the product to add.")
    quantity: int = Field(..., gt=0, description="Quantity of the product to add, must be greater than 0.")


class CartItemUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    quantity: int = Field(..., ge=0, description="New quantity for the cart item. Setting to 0 removes the item.")


class CartItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    cart_id: uuid.UUID
    product_id: uuid.UUID
    quantity: int
    created_at: datetime
    updated_at: datetime


class CartResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    items: list[CartItemResponse] = []
