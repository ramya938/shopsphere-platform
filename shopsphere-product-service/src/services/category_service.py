import re
import uuid
from typing import Sequence
from loguru import logger
from src.domain.models import Category
from src.domain.repository_interfaces import CategoryRepositoryInterface
from src.core.exceptions import EntityNotFoundException, EntityAlreadyExistsException

def generate_slug(name: str) -> str:
    """Generate a URL-safe lowercase slug from a name string."""
    name = name.lower().strip()
    name = re.sub(r"[^\w\s-]", "", name)
    name = re.sub(r"[\s_-]+", "-", name)
    return name

class CategoryService:
    def __init__(self, category_repo: CategoryRepositoryInterface):
        self.category_repo = category_repo

    async def create_category(self, name: str, description: str | None = None) -> Category:
        """Create a new category, ensuring slug uniqueness."""
        slug = generate_slug(name)
        logger.info(f"Creating category: {name} (slug: {slug})")

        existing = await self.category_repo.get_by_slug(slug)
        if existing:
            logger.warning(f"Category creation failed: Category with slug {slug} already exists")
            raise EntityAlreadyExistsException("Category with this name or slug already exists.")

        new_category = Category(
            name=name,
            slug=slug,
            description=description
        )
        saved = await self.category_repo.add(new_category)
        return saved

    async def get_category(self, category_id: uuid.UUID) -> Category:
        """Retrieve a category by UUID."""
        category = await self.category_repo.get_by_id(category_id)
        if not category:
            raise EntityNotFoundException("Category not found.")
        return category

    async def get_category_by_slug(self, slug: str) -> Category:
        """Retrieve a category by slug."""
        category = await self.category_repo.get_by_slug(slug)
        if not category:
            raise EntityNotFoundException("Category not found.")
        return category

    async def update_category(
        self, category_id: uuid.UUID, name: str | None = None, description: str | None = None
    ) -> Category:
        """Update category name and/or description, re-generating slug if name changes."""
        category = await self.category_repo.get_by_id(category_id)
        if not category:
            raise EntityNotFoundException("Category not found.")

        if name:
            new_slug = generate_slug(name)
            if new_slug != category.slug:
                existing = await self.category_repo.get_by_slug(new_slug)
                if existing:
                    raise EntityAlreadyExistsException("Category name or slug already in use.")
                category.slug = new_slug
            category.name = name

        if description is not None:
            category.description = description

        updated = await self.category_repo.update(category)
        logger.info(f"Category updated successfully: {category_id}")
        return updated

    async def delete_category(self, category_id: uuid.UUID) -> None:
        """Delete a category by UUID."""
        category = await self.category_repo.get_by_id(category_id)
        if not category:
            raise EntityNotFoundException("Category not found.")
        
        await self.category_repo.delete(category)
        logger.info(f"Category deleted successfully: {category_id}")

    async def list_categories(self) -> Sequence[Category]:
        """List all categories."""
        return await self.category_repo.list_all()
