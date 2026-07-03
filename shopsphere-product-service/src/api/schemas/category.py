import uuid
from datetime import datetime
from pydantic import BaseModel, Field

class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255, description="Category name")
    description: str | None = Field(default=None, max_length=1000, description="Description of the category")

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Electronics",
                "description": "Smartphones, laptops, and gadgets."
            }
        }
    }


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255, description="New category name")
    description: str | None = Field(default=None, max_length=1000, description="New description")

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Consumer Electronics",
                "description": "Updated gadgets category description."
            }
        }
    }


class CategoryResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    description: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "e987c6b5-d4a3-2c1b-0a98-76543210fedc",
                "name": "Electronics",
                "slug": "electronics",
                "description": "Smartphones, laptops, and gadgets.",
                "created_at": "2026-06-23T12:00:00Z",
                "updated_at": "2026-06-23T12:00:00Z"
            }
        }
    }
