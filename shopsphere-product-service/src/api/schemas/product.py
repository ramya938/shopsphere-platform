import uuid
from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field, field_validator
from src.domain.models import ProductStatus

class ProductCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255, description="Product name")
    description: str | None = Field(default=None, max_length=5000, description="Product details")
    price: float = Field(..., gt=0, description="Product unit price (must be positive)")
    inventory_quantity: int = Field(default=0, ge=0, description="Available stock quantity")
    image_url: str | None = Field(default=None, max_length=512, description="Product image link")
    status: ProductStatus = Field(default=ProductStatus.ACTIVE, description="Product status state")
    category_id: uuid.UUID | None = Field(default=None, description="Linked category UUID")

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "iPhone 15 Pro",
                "description": "Apple smartphone with titanium design.",
                "price": 999.99,
                "inventory_quantity": 50,
                "image_url": "https://example.com/iphone15.jpg",
                "status": "ACTIVE",
                "category_id": "e987c6b5-d4a3-2c1b-0a98-76543210fedc"
            }
        }
    }


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    description: str | None = Field(default=None, max_length=5000)
    price: float | None = Field(default=None, gt=0)
    inventory_quantity: int | None = Field(default=None, ge=0)
    image_url: str | None = Field(default=None, max_length=512)
    status: ProductStatus | None = Field(default=None)
    category_id: uuid.UUID | None = Field(default=None)

    model_config = {
        "json_schema_extra": {
            "example": {
                "price": 949.99,
                "inventory_quantity": 45
            }
        }
    }


class ProductResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    description: str | None
    price: float
    inventory_quantity: int
    image_url: str | None
    status: ProductStatus
    category_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime

    # Format Decimal price from db to float for schema serialization
    @field_validator("price", mode="before")
    @classmethod
    def serialize_price(cls, v: Any) -> float:
        if v is not None:
            return float(v)
        return v

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "a9b8c7d6-e5f4-3c2b-1a09-876543210fed",
                "name": "iPhone 15 Pro",
                "slug": "iphone-15-pro",
                "description": "Apple smartphone with titanium design.",
                "price": 999.99,
                "inventory_quantity": 50,
                "image_url": "https://example.com/iphone15.jpg",
                "status": "ACTIVE",
                "category_id": "e987c6b5-d4a3-2c1b-0a98-76543210fedc",
                "created_at": "2026-06-23T12:00:00Z",
                "updated_at": "2026-06-23T12:00:00Z"
            }
        }
    }


class ProductListResponse(BaseModel):
    total_count: int = Field(..., description="Total matching products in database")
    products: list[ProductResponse] = Field(..., description="Paginated products list")
    skip: int = Field(..., description="Number of skipped items")
    limit: int = Field(..., description="Maximum returned items limit")


class InventoryUpdate(BaseModel):
    quantity: int = Field(..., gt=0, description="Quantity of inventory items to add/deduct (must be positive)")

    model_config = {
        "json_schema_extra": {
            "example": {
                "quantity": 5
            }
        }
    }
