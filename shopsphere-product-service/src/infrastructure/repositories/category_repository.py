import uuid
from typing import Sequence
from sqlalchemy import select
from src.domain.models import Category
from src.domain.repository_interfaces import CategoryRepositoryInterface
from src.infrastructure.repositories.base import BaseSQLAlchemyRepository

class SQLAlchemyCategoryRepository(BaseSQLAlchemyRepository, CategoryRepositoryInterface):
    """SQLAlchemy implementation of the CategoryRepositoryInterface."""

    async def get_by_id(self, category_id: uuid.UUID) -> Category | None:
        result = await self.session.execute(
            select(Category).filter(Category.id == category_id)
        )
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Category | None:
        result = await self.session.execute(
            select(Category).filter(Category.slug == slug)
        )
        return result.scalar_one_or_none()

    async def add(self, category: Category) -> Category:
        self.session.add(category)
        await self.session.flush()
        await self.session.refresh(category)
        return category

    async def update(self, category: Category) -> Category:
        await self.session.flush()
        await self.session.refresh(category)
        return category

    async def delete(self, category: Category) -> None:
        await self.session.delete(category)
        await self.session.flush()

    async def list_all(self) -> Sequence[Category]:
        result = await self.session.execute(
            select(Category).order_by(Category.name)
        )
        return result.scalars().all()
