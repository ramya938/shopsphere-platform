import uuid
from loguru import logger
from src.domain.models import Cart, CartItem
from src.domain.repository_interfaces import CartRepositoryInterface
from src.infrastructure.clients.product_client import ProductClient
from src.core.exceptions import EntityNotFoundException, BaseAppException, InventoryInsufficientException

class CartService:
    """Service to orchestrate shopping cart operations."""

    def __init__(self, cart_repo: CartRepositoryInterface, product_client: ProductClient):
        self.cart_repo = cart_repo
        self.product_client = product_client

    async def get_or_create_cart(self, user_id: uuid.UUID) -> Cart:
        """Fetch the user's cart, creating it if it doesn't already exist."""
        cart = await self.cart_repo.get_by_user_id(user_id)
        if not cart:
            logger.info(f"Creating new cart for user: {user_id}")
            cart = Cart(user_id=user_id)
            cart = await self.cart_repo.add(cart)
        return cart

    async def add_item_to_cart(self, user_id: uuid.UUID, product_id: uuid.UUID, quantity: int) -> Cart:
        """Add a product item to the user's cart after checking stock levels."""
        if quantity <= 0:
            raise BaseAppException("Quantity must be greater than 0")

        # Verify product availability from Product Service
        product = await self.product_client.get_product(product_id)
        if not product:
            raise EntityNotFoundException("Product not found")
        
        if product.get("status") != "ACTIVE":
            raise BaseAppException("Cannot add inactive product to cart")

        cart = await self.get_or_create_cart(user_id)

        # Check if the product is already in the cart
        existing_item = next((item for item in cart.items if item.product_id == product_id), None)
        target_quantity = quantity
        if existing_item:
            target_quantity += existing_item.quantity

        # Validate that stock is sufficient for addition
        available_stock = product.get("inventory_quantity", 0)
        if target_quantity > available_stock:
            raise InventoryInsufficientException(
                f"Cannot add {quantity} items. Available stock: {available_stock}. Current in cart: {existing_item.quantity if existing_item else 0}"
            )

        if existing_item:
            existing_item.quantity = target_quantity
        else:
            cart_item = CartItem(cart_id=cart.id, product_id=product_id, quantity=quantity)
            cart.items.append(cart_item)

        await self.cart_repo.update(cart)
        logger.info(f"Added product {product_id} (qty: {quantity}) to cart for user {user_id}")
        return cart

    async def update_item_quantity(self, user_id: uuid.UUID, product_id: uuid.UUID, quantity: int) -> Cart:
        """Update the quantity of a product inside the user's cart."""
        cart = await self.cart_repo.get_by_user_id(user_id)
        if not cart:
            raise EntityNotFoundException("Cart not found")

        existing_item = next((item for item in cart.items if item.product_id == product_id), None)
        if not existing_item:
            raise EntityNotFoundException("Product item not found in cart")

        if quantity <= 0:
            # Remove item from cart if quantity is 0 or negative
            cart.items.remove(existing_item)
        else:
            # Verify stock from Product Service
            product = await self.product_client.get_product(product_id)
            if not product:
                raise EntityNotFoundException("Product not found")
            if product.get("status") != "ACTIVE":
                raise BaseAppException("Cannot add inactive product to cart")
            
            available_stock = product.get("inventory_quantity", 0)
            if quantity > available_stock:
                raise InventoryInsufficientException(
                    f"Requested quantity {quantity} exceeds available stock {available_stock}"
                )
            
            existing_item.quantity = quantity

        await self.cart_repo.update(cart)
        logger.info(f"Updated product {product_id} quantity to {quantity} for user {user_id}")
        return cart

    async def remove_item_from_cart(self, user_id: uuid.UUID, product_id: uuid.UUID) -> Cart:
        """Remove a product item entirely from the user's cart."""
        cart = await self.cart_repo.get_by_user_id(user_id)
        if not cart:
            raise EntityNotFoundException("Cart not found")

        existing_item = next((item for item in cart.items if item.product_id == product_id), None)
        if not existing_item:
            raise EntityNotFoundException("Product item not found in cart")

        cart.items.remove(existing_item)
        await self.cart_repo.update(cart)
        logger.info(f"Removed product {product_id} from cart for user {user_id}")
        return cart

    async def clear_cart(self, user_id: uuid.UUID) -> None:
        """Remove all items from the user's cart."""
        cart = await self.cart_repo.get_by_user_id(user_id)
        if cart and cart.items:
            cart.items.clear()
            await self.cart_repo.update(cart)
            logger.info(f"Cleared all cart items for user {user_id}")
