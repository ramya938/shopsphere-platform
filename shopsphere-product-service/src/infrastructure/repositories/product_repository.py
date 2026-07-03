import uuid
from typing import Sequence
from sqlalchemy import select, func, or_, desc, asc
from src.domain.models import Product, ProductStatus
from src.domain.repository_interfaces import ProductRepositoryInterface
from src.infrastructure.repositories.base import BaseSQLAlchemyRepository

class SQLAlchemyProductRepository(BaseSQLAlchemyRepository, ProductRepositoryInterface):
    """SQLAlchemy implementation of the ProductRepositoryInterface."""

    async def get_by_id(self, product_id: uuid.UUID) -> Product | None:
        result = await self.session.execute(
            select(Product).filter(Product.id == product_id)
        )
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Product | None:
        result = await self.session.execute(
            select(Product).filter(Product.slug == slug)
        )
        return result.scalar_one_or_none()

    async def add(self, product: Product) -> Product:
        self.session.add(product)
        await self.session.flush()
        await self.session.refresh(product)
        return product

    async def update(self, product: Product) -> Product:
        await self.session.flush()
        await self.session.refresh(product)
        return product

    async def delete(self, product: Product) -> None:
        await self.session.delete(product)
        await self.session.flush()

    async def list_and_filter(
        self,
        search: str | None = None,
        category_id: uuid.UUID | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        status: ProductStatus | None = None,
        sort_by: str | None = None,
        sort_order: str | None = "asc",
        skip: int = 0,
        limit: int = 100
    ) -> tuple[Sequence[Product], int]:
        """
        Builds dynamic filters, counts matching results, applies sorting/pagination,
        and retrieves products list.
        """
        # Base query
        query = select(Product)

        # Filters
        if search:
            query = query.filter(
                or_(
                    Product.name.ilike(f"%{search}%"),
                    Product.description.ilike(f"%{search}%")
                )
            )
        if category_id:
            query = query.filter(Product.category_id == category_id)
        if min_price is not None:
            query = query.filter(Product.price >= min_price)
        if max_price is not None:
            query = query.filter(Product.price <= max_price)
        if status:
            query = query.filter(Product.status == status)

        # Retrieve total matching count
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await self.session.execute(count_query)
        total_count = count_result.scalar_one()

        # Sort order and attribute
        sort_attr = getattr(Product, sort_by) if sort_by and hasattr(Product, sort_by) else Product.created_at
        if sort_order == "desc":
            query = query.order_by(desc(sort_attr))
        else:
            query = query.order_by(asc(sort_attr))

        # Pagination
        query = query.offset(skip).limit(limit)

        # Execute query
        result = await self.session.execute(query)
        products = result.scalars().all()

        return products, total_count
