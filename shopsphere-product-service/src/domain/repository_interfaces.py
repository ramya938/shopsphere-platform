from abc import ABC, abstractmethod
import uuid
from typing import Sequence
from src.domain.models import Category, Product, ProductStatus

class CategoryRepositoryInterface(ABC):
    """Abstract interface for Category persistence operations."""

    @abstractmethod
    async def get_by_id(self, category_id: uuid.UUID) -> Category | None:
        """Retrieve a category by UUID."""
        pass

    @abstractmethod
    async def get_by_slug(self, slug: str) -> Category | None:
        """Retrieve a category by its slug."""
        pass

    @abstractmethod
    async def add(self, category: Category) -> Category:
        """Add a new category."""
        pass

    @abstractmethod
    async def update(self, category: Category) -> Category:
        """Update an existing category."""
        pass

    @abstractmethod
    async def delete(self, category: Category) -> None:
        """Delete a category."""
        pass

    @abstractmethod
    async def list_all(self) -> Sequence[Category]:
        """Retrieve all categories."""
        pass


class ProductRepositoryInterface(ABC):
    """Abstract interface for Product persistence operations."""

    @abstractmethod
    async def get_by_id(self, product_id: uuid.UUID) -> Product | None:
        """Retrieve a product by UUID."""
        pass

    @abstractmethod
    async def get_by_slug(self, slug: str) -> Product | None:
        """Retrieve a product by its slug."""
        pass

    @abstractmethod
    async def add(self, product: Product) -> Product:
        """Add a new product."""
        pass

    @abstractmethod
    async def update(self, product: Product) -> Product:
        """Update an existing product."""
        pass

    @abstractmethod
    async def delete(self, product: Product) -> None:
        """Delete a product."""
        pass

    @abstractmethod
    async def list_and_filter(
        self,
        search: str | None = None,
        category_id: uuid.UUID | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        status: ProductStatus | None = None,
        sort_by: str | None = None,     # e.g., 'price', 'created_at', 'name'
        sort_order: str | None = "asc", # 'asc' or 'desc'
        skip: int = 0,
        limit: int = 100
    ) -> tuple[Sequence[Product], int]:
        """
        Search, filter, sort and paginate products.
        Returns a tuple of (products_list, total_matching_count).
        """
        pass
