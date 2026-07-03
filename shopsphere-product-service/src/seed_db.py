import asyncio
import uuid
from src.infrastructure.database import AsyncSessionLocal
from src.domain.models import Category, Product, ProductStatus

async def seed():
    async with AsyncSessionLocal() as session:
        # Create categories
        electronics = Category(
            id=uuid.uuid4(),
            name="Electronics",
            slug="electronics",
            description="Phones, laptops, and gadgets"
        )
        home = Category(
            id=uuid.uuid4(),
            name="Home & Living",
            slug="home-living",
            description="Furniture and appliances"
        )
        session.add_all([electronics, home])
        await session.commit()

        # Create products
        headphones = Product(
            id=uuid.uuid4(),
            name="Wireless Headphones",
            slug="wireless-headphones",
            description="Premium active noise-cancelling headphones",
            price=199.99,
            inventory_quantity=42,
            category_id=electronics.id,
            status=ProductStatus.ACTIVE
        )
        keyboard = Product(
            id=uuid.uuid4(),
            name="Mechanical Keyboard",
            slug="mechanical-keyboard",
            description="Tactile switches with customizable RGB lighting",
            price=129.99,
            inventory_quantity=15,
            category_id=electronics.id,
            status=ProductStatus.ACTIVE
        )
        chair = Product(
            id=uuid.uuid4(),
            name="Ergonomic Office Chair",
            slug="ergonomic-office-chair",
            description="High-back mesh chair with lumbar support",
            price=249.99,
            inventory_quantity=8,
            category_id=home.id,
            status=ProductStatus.ACTIVE
        )
        session.add_all([headphones, keyboard, chair])
        await session.commit()
        print("Seeded successfully!")

if __name__ == "__main__":
    asyncio.run(seed())
