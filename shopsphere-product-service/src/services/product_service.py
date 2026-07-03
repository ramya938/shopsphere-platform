import uuid
from typing import Sequence
from loguru import logger
from src.domain.models import Product, ProductStatus
from src.domain.repository_interfaces import ProductRepositoryInterface, CategoryRepositoryInterface
from src.core.exceptions import (
    EntityNotFoundException,
    EntityAlreadyExistsException,
    InventoryInsufficientException
)
from src.services.category_service import generate_slug

class ProductService:
    def __init__(
        self,
        product_repo: ProductRepositoryInterface,
        category_repo: CategoryRepositoryInterface
    ):
        self.product_repo = product_repo
        self.category_repo = category_repo

    async def create_product(
        self,
        name: str,
        price: float,
        inventory_quantity: int = 0,
        description: str | None = None,
        image_url: str | None = None,
        status: ProductStatus = ProductStatus.ACTIVE,
        category_id: uuid.UUID | None = None
    ) -> Product:
        """Create a new product, verifying category if specified."""
        slug = generate_slug(name)
        logger.info(f"Creating product: {name} (slug: {slug})")

        # Check category existence
        if category_id:
            category = await self.category_repo.get_by_id(category_id)
            if not category:
                raise EntityNotFoundException("Category not found.")

        # Check slug collision
        existing = await self.product_repo.get_by_slug(slug)
        if existing:
            raise EntityAlreadyExistsException("Product with this name or slug already exists.")

        # Force status out of stock if stock is 0
        if inventory_quantity <= 0 and status == ProductStatus.ACTIVE:
            status = ProductStatus.OUT_OF_STOCK

        new_product = Product(
            name=name,
            slug=slug,
            description=description,
            price=price,
            inventory_quantity=inventory_quantity,
            image_url=image_url,
            status=status,
            category_id=category_id
        )

        return await self.product_repo.add(new_product)

    async def get_product(self, product_id: uuid.UUID) -> Product:
        """Retrieve a product by UUID."""
        product = await self.product_repo.get_by_id(product_id)
        if not product:
            raise EntityNotFoundException("Product not found.")
        return product

    async def get_product_by_slug(self, slug: str) -> Product:
        """Retrieve a product by slug."""
        product = await self.product_repo.get_by_slug(slug)
        if not product:
            raise EntityNotFoundException("Product not found.")
        return product

    async def update_product(
        self,
        product_id: uuid.UUID,
        name: str | None = None,
        price: float | None = None,
        inventory_quantity: int | None = None,
        description: str | None = None,
        image_url: str | None = None,
        status: ProductStatus | None = None,
        category_id: uuid.UUID | None = None
    ) -> Product:
        """Update product attributes with validation."""
        product = await self.product_repo.get_by_id(product_id)
        if not product:
            raise EntityNotFoundException("Product not found.")

        if category_id:
            category = await self.category_repo.get_by_id(category_id)
            if not category:
                raise EntityNotFoundException("Category not found.")
            product.category_id = category_id
        elif category_id is False: # sentinel to remove category association
            product.category_id = None

        if name:
            new_slug = generate_slug(name)
            if new_slug != product.slug:
                existing = await self.product_repo.get_by_slug(new_slug)
                if existing:
                    raise EntityAlreadyExistsException("Product name or slug already in use.")
                product.slug = new_slug
            product.name = name

        if price is not None:
            if price < 0:
                raise ValueError("Price cannot be negative.")
            product.price = price

        if inventory_quantity is not None:
            if inventory_quantity < 0:
                raise ValueError("Inventory quantity cannot be negative.")
            product.inventory_quantity = inventory_quantity
            # Auto update status on stock changes
            if inventory_quantity == 0:
                product.status = ProductStatus.OUT_OF_STOCK
            elif product.status == ProductStatus.OUT_OF_STOCK and inventory_quantity > 0:
                product.status = ProductStatus.ACTIVE

        if description is not None:
            product.description = description

        if image_url is not None:
            product.image_url = image_url

        if status:
            # Prevent setting active status if stock is 0
            if status == ProductStatus.ACTIVE and product.inventory_quantity <= 0:
                status = ProductStatus.OUT_OF_STOCK
            product.status = status

        return await self.product_repo.update(product)

    async def delete_product(self, product_id: uuid.UUID) -> None:
        """Permanently delete a product."""
        product = await self.product_repo.get_by_id(product_id)
        if not product:
            raise EntityNotFoundException("Product not found.")
        await self.product_repo.delete(product)

    async def list_products(
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
        """List and search products."""
        return await self.product_repo.list_and_filter(
            search=search,
            category_id=category_id,
            min_price=min_price,
            max_price=max_price,
            status=status,
            sort_by=sort_by,
            sort_order=sort_order,
            skip=skip,
            limit=limit
        )

    async def deduct_inventory(self, product_id: uuid.UUID, quantity: int) -> Product:
        """Deduct stock from product inventory, verifying availability."""
        if quantity <= 0:
            raise ValueError("Deduction quantity must be positive.")
        
        product = await self.product_repo.get_by_id(product_id)
        if not product:
            raise EntityNotFoundException("Product not found.")

        if product.inventory_quantity < quantity:
            logger.warning(f"Inventory deduction failed: Product {product_id} has {product.inventory_quantity} in stock, requested {quantity}")
            raise InventoryInsufficientException(
                f"Insufficient stock. Available: {product.inventory_quantity}, Requested: {quantity}"
            )

        product.inventory_quantity -= quantity
        if product.inventory_quantity == 0:
            product.status = ProductStatus.OUT_OF_STOCK

        logger.info(f"Deducted {quantity} items from product {product_id}. New stock: {product.inventory_quantity}")
        return await self.product_repo.update(product)

    async def add_inventory(self, product_id: uuid.UUID, quantity: int) -> Product:
        """Add stock to product inventory."""
        if quantity <= 0:
            raise ValueError("Restock quantity must be positive.")

        product = await self.product_repo.get_by_id(product_id)
        if not product:
            raise EntityNotFoundException("Product not found.")

        product.inventory_quantity += quantity
        if product.status == ProductStatus.OUT_OF_STOCK and product.inventory_quantity > 0:
            product.status = ProductStatus.ACTIVE

        logger.info(f"Added {quantity} items to product {product_id}. New stock: {product.inventory_quantity}")
        return await self.product_repo.update(product)
