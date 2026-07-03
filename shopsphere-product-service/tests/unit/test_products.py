import pytest
import uuid
from src.services.product_service import ProductService
from src.services.category_service import CategoryService
from src.infrastructure.repositories.product_repository import SQLAlchemyProductRepository
from src.infrastructure.repositories.category_repository import SQLAlchemyCategoryRepository
from src.domain.models import ProductStatus
from src.core.exceptions import (
    EntityNotFoundException,
    EntityAlreadyExistsException,
    InventoryInsufficientException
)

@pytest.fixture
def product_service(db_session) -> ProductService:
    product_repo = SQLAlchemyProductRepository(db_session)
    category_repo = SQLAlchemyCategoryRepository(db_session)
    return ProductService(product_repo, category_repo)

@pytest.fixture
def category_service(db_session) -> CategoryService:
    repo = SQLAlchemyCategoryRepository(db_session)
    return CategoryService(repo)


@pytest.mark.asyncio
async def test_create_product_success(product_service, category_service):
    """Verify product creation with valid category link."""
    category = await category_service.create_category(name="Toys")
    
    product = await product_service.create_product(
        name="Lego Star Wars Star Destroyer",
        price=159.99,
        inventory_quantity=10,
        description="Lego building kit",
        category_id=category.id
    )
    
    assert product.id is not None
    assert product.name == "Lego Star Wars Star Destroyer"
    assert product.slug == "lego-star-wars-star-destroyer"
    assert float(product.price) == 159.99
    assert product.inventory_quantity == 10
    assert product.status == ProductStatus.ACTIVE
    assert product.category_id == category.id


@pytest.mark.asyncio
async def test_create_product_out_of_stock_triggers(product_service):
    """Verify status is auto set to OUT_OF_STOCK if created with 0 quantity."""
    product = await product_service.create_product(
        name="Out of Stock Item",
        price=9.99,
        inventory_quantity=0
    )
    assert product.status == ProductStatus.OUT_OF_STOCK


@pytest.mark.asyncio
async def test_deduct_inventory_success(product_service):
    """Verify successful inventory deduction and status transition on stock exhaustion."""
    product = await product_service.create_product(
        name="Stock Item",
        price=29.99,
        inventory_quantity=5
    )
    
    deducted = await product_service.deduct_inventory(product.id, 3)
    assert deducted.inventory_quantity == 2
    assert deducted.status == ProductStatus.ACTIVE
    
    # Exhaust inventory
    exhausted = await product_service.deduct_inventory(product.id, 2)
    assert exhausted.inventory_quantity == 0
    assert exhausted.status == ProductStatus.OUT_OF_STOCK


@pytest.mark.asyncio
async def test_deduct_inventory_insufficient(product_service):
    """Verify inventory deduction raises error if stock is low."""
    product = await product_service.create_product(
        name="Limited Stock",
        price=1.99,
        inventory_quantity=2
    )
    
    with pytest.raises(InventoryInsufficientException):
        await product_service.deduct_inventory(product.id, 5)


@pytest.mark.asyncio
async def test_add_inventory_restock_transition(product_service):
    """Verify restocking increases stock and transitions status back to ACTIVE."""
    product = await product_service.create_product(
        name="Sold Out Item",
        price=10.00,
        inventory_quantity=0
    )
    assert product.status == ProductStatus.OUT_OF_STOCK
    
    restocked = await product_service.add_inventory(product.id, 15)
    assert restocked.inventory_quantity == 15
    assert restocked.status == ProductStatus.ACTIVE


@pytest.mark.asyncio
async def test_list_products_sorting_filtering(product_service):
    """Verify sorting and filtering work correctly."""
    p1 = await product_service.create_product(name="Premium Laptop", price=1200.00, inventory_quantity=5)
    p2 = await product_service.create_product(name="Cheap Keyboard", price=25.00, inventory_quantity=10)
    
    # Filter by search term
    products, total = await product_service.list_products(search="Premium")
    assert total == 1
    assert products[0].name == "Premium Laptop"
    
    # Sort by price descending
    products_sorted, total = await product_service.list_products(sort_by="price", sort_order="desc")
    assert products_sorted[0].name == "Premium Laptop"
    assert products_sorted[1].name == "Cheap Keyboard"
