import pytest
import uuid
from src.services.category_service import CategoryService
from src.infrastructure.repositories.category_repository import SQLAlchemyCategoryRepository
from src.core.exceptions import EntityNotFoundException, EntityAlreadyExistsException

@pytest.fixture
def category_service(db_session) -> CategoryService:
    repo = SQLAlchemyCategoryRepository(db_session)
    return CategoryService(repo)


@pytest.mark.asyncio
async def test_create_category_success(category_service):
    """Verify category creation and slug generation."""
    category = await category_service.create_category(
        name="Smart Phones & Gadgets",
        description="Mobile devices category"
    )
    assert category.id is not None
    assert category.name == "Smart Phones & Gadgets"
    assert category.slug == "smart-phones-gadgets"
    assert category.description == "Mobile devices category"


@pytest.mark.asyncio
async def test_create_category_duplicate(category_service):
    """Verify category creation fails on duplicate slug name."""
    await category_service.create_category(name="Laptops")
    
    with pytest.raises(EntityAlreadyExistsException):
        await category_service.create_category(name="laptops")


@pytest.mark.asyncio
async def test_get_category_not_found(category_service):
    """Verify category retrieval fails if not found."""
    random_id = uuid.uuid4()
    with pytest.raises(EntityNotFoundException):
        await category_service.get_category(random_id)


@pytest.mark.asyncio
async def test_update_category_success(category_service):
    """Verify category updates fields and re-evaluates slug if name changes."""
    category = await category_service.create_category(name="Old Name")
    
    updated = await category_service.update_category(
        category_id=category.id,
        name="New Name",
        description="New Description"
    )
    assert updated.name == "New Name"
    assert updated.slug == "new-name"
    assert updated.description == "New Description"


@pytest.mark.asyncio
async def test_delete_category_success(category_service):
    """Verify category can be deleted and is no longer retrievable."""
    category = await category_service.create_category(name="Books")
    
    await category_service.delete_category(category.id)
    
    with pytest.raises(EntityNotFoundException):
        await category_service.get_category(category.id)
