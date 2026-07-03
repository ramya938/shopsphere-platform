import uuid
from typing import Sequence
from loguru import logger
from src.domain.models import Order, OrderItem, OrderStatus, Cart
from src.domain.repository_interfaces import OrderRepositoryInterface, CartRepositoryInterface
from src.infrastructure.clients.product_client import ProductClient
from src.core.exceptions import (
    EntityNotFoundException,
    BaseAppException,
    InventoryInsufficientException,
    PermissionDeniedException,
    InvalidOrderStatusException
)
from src.core.kafka import KafkaProducerManager
from src.domain.events import EventEnvelope, OrderCreatedPayload, OrderCreatedItem, OrderCancelledPayload

class OrderService:
    """Service to orchestrate order lifecycle operations."""

    def __init__(
        self,
        order_repo: OrderRepositoryInterface,
        cart_repo: CartRepositoryInterface,
        product_client: ProductClient,
        producer_manager: KafkaProducerManager | None = None
    ):
        self.order_repo = order_repo
        self.cart_repo = cart_repo
        self.product_client = product_client
        self.producer_manager = producer_manager

    async def checkout_cart(self, user_id: uuid.UUID, shipping_address: str) -> Order:
        """Process checkout from the user's active shopping cart, deducting stock and creating an order."""
        if not shipping_address or not shipping_address.strip():
            raise BaseAppException("Shipping address is required")

        cart = await self.cart_repo.get_by_user_id(user_id)
        if not cart or not cart.items:
            raise BaseAppException("Shopping cart is empty")

        # 1. Fetch products information and validate stock first
        items_to_process = []
        total_price = 0.0

        for item in cart.items:
            product = await self.product_client.get_product(item.product_id)
            if not product:
                raise EntityNotFoundException(f"Product {item.product_id} no longer exists")
            if product.get("status") != "ACTIVE":
                raise BaseAppException(f"Product {product.get('name')} is no longer active")
            
            available_stock = product.get("inventory_quantity", 0)
            if item.quantity > available_stock:
                raise InventoryInsufficientException(
                    f"Insufficient stock for product '{product.get('name')}'. Available: {available_stock}, Requested: {item.quantity}"
                )
            
            price = float(product.get("price", 0.0))
            total_price += price * item.quantity
            items_to_process.append({
                "product_id": item.product_id,
                "quantity": item.quantity,
                "price": price,
                "name": product.get("name")
            })

        # 2. Reserve inventory (Deduct stock via Product Client) with compensating transaction logic
        deducted_items = []
        try:
            for item in items_to_process:
                success = await self.product_client.deduct_stock(item["product_id"], item["quantity"])
                if not success:
                    raise InventoryInsufficientException(
                        f"Failed to reserve inventory for product '{item['name']}'"
                    )
                deducted_items.append(item)
        except Exception as exc:
            # Trigger compensating restocks for already reserved items
            logger.warning("Checkout failed. Rolling back inventory deductions...")
            for item in deducted_items:
                await self.product_client.restock_stock(item["product_id"], item["quantity"])
            raise exc

        # 3. Create the Order and OrderItems
        try:
            order = Order(
                user_id=user_id,
                total_price=total_price,
                status=OrderStatus.CREATED,
                shipping_address=shipping_address
            )
            for item in items_to_process:
                order_item = OrderItem(
                    product_id=item["product_id"],
                    quantity=item["quantity"],
                    price_at_purchase=item["price"]
                )
                order.items.append(order_item)

            saved_order = await self.order_repo.add(order)
            
            # 4. Clear the shopping cart
            cart.items.clear()
            await self.cart_repo.update(cart)
            
            logger.info(f"Order created successfully from checkout: {saved_order.id} for user {user_id}")

            # Emit OrderCreated event
            if self.producer_manager:
                try:
                    items_payload = [
                        OrderCreatedItem(product_id=item.product_id, quantity=item.quantity)
                        for item in saved_order.items
                    ]
                    payload = OrderCreatedPayload(
                        order_id=saved_order.id,
                        user_id=saved_order.user_id,
                        total_price=saved_order.total_price,
                        items=items_payload,
                        shipping_address=saved_order.shipping_address
                    )
                    envelope = EventEnvelope(
                        event_type="OrderCreated",
                        payload=payload.model_dump()
                    )
                    await self.producer_manager.send_event("order-created", envelope)
                except Exception as e:
                    logger.error(f"Failed to publish OrderCreated event for order {saved_order.id}: {e}")

            return saved_order
            
        except Exception as exc:
            # If DB creation fails, restock inventory as fallback
            logger.error(f"Database error during order creation. Restocking all reserved items: {exc}")
            for item in items_to_process:
                await self.product_client.restock_stock(item["product_id"], item["quantity"])
            raise exc

    async def place_direct_order(self, user_id: uuid.UUID, items: list[dict], shipping_address: str) -> Order:
        """Place an order directly without using a shopping cart."""
        if not shipping_address or not shipping_address.strip():
            raise BaseAppException("Shipping address is required")
        if not items:
            raise BaseAppException("Order items list cannot be empty")

        items_to_process = []
        total_price = 0.0

        # Validate product and stock
        for req_item in items:
            prod_id = req_item.get("product_id")
            qty = req_item.get("quantity")
            if not prod_id or qty <= 0:
                raise BaseAppException("Invalid product_id or quantity")

            product = await self.product_client.get_product(prod_id)
            if not product:
                raise EntityNotFoundException(f"Product {prod_id} not found")
            if product.get("status") != "ACTIVE":
                raise BaseAppException(f"Product {product.get('name')} is not active")

            available_stock = product.get("inventory_quantity", 0)
            if qty > available_stock:
                raise InventoryInsufficientException(
                    f"Insufficient stock for '{product.get('name')}'. Available: {available_stock}, Requested: {qty}"
                )

            price = float(product.get("price", 0.0))
            total_price += price * qty
            items_to_process.append({
                "product_id": prod_id,
                "quantity": qty,
                "price": price,
                "name": product.get("name")
            })

        # Reserve inventory (Deduct stock)
        deducted_items = []
        try:
            for item in items_to_process:
                success = await self.product_client.deduct_stock(item["product_id"], item["quantity"])
                if not success:
                    raise InventoryInsufficientException(
                        f"Failed to reserve inventory for '{item['name']}'"
                    )
                deducted_items.append(item)
        except Exception as exc:
            logger.warning("Direct order placement stock reservation failed. Rolling back inventory...")
            for item in deducted_items:
                await self.product_client.restock_stock(item["product_id"], item["quantity"])
            raise exc

        # Create Order
        try:
            order = Order(
                user_id=user_id,
                total_price=total_price,
                status=OrderStatus.CREATED,
                shipping_address=shipping_address
            )
            for item in items_to_process:
                order.items.append(
                    OrderItem(
                        product_id=item["product_id"],
                        quantity=item["quantity"],
                        price_at_purchase=item["price"]
                    )
                )

            saved_order = await self.order_repo.add(order)
            logger.info(f"Direct order placed successfully: {saved_order.id} for user {user_id}")

            # Emit OrderCreated event
            if self.producer_manager:
                try:
                    items_payload = [
                        OrderCreatedItem(product_id=item.product_id, quantity=item.quantity)
                        for item in saved_order.items
                    ]
                    payload = OrderCreatedPayload(
                        order_id=saved_order.id,
                        user_id=saved_order.user_id,
                        total_price=saved_order.total_price,
                        items=items_payload,
                        shipping_address=saved_order.shipping_address
                    )
                    envelope = EventEnvelope(
                        event_type="OrderCreated",
                        payload=payload.model_dump()
                    )
                    await self.producer_manager.send_event("order-created", envelope)
                except Exception as e:
                    logger.error(f"Failed to publish OrderCreated event for order {saved_order.id}: {e}")

            return saved_order
        except Exception as exc:
            logger.error(f"Database error placing direct order. Restocking reserved items: {exc}")
            for item in items_to_process:
                await self.product_client.restock_stock(item["product_id"], item["quantity"])
            raise exc

    async def get_order(self, order_id: uuid.UUID, user_id: uuid.UUID, user_role: str) -> Order:
        """Get order details by UUID with authorization check."""
        order = await self.order_repo.get_by_id(order_id)
        if not order:
            raise EntityNotFoundException("Order not found")

        # Users can only view their own orders; admins can view all
        if user_role != "ADMIN" and order.user_id != user_id:
            raise PermissionDeniedException("Access denied. Insufficient permissions.")

        return order

    async def list_my_orders(self, user_id: uuid.UUID) -> Sequence[Order]:
        """List order history for a specific customer."""
        return await self.order_repo.list_by_user(user_id)

    async def list_all_orders(self, skip: int = 0, limit: int = 100) -> Sequence[Order]:
        """List all orders (Admin only)."""
        return await self.order_repo.list_all(skip=skip, limit=limit)

    async def transition_status(
        self,
        order_id: uuid.UUID,
        user_id: uuid.UUID,
        user_role: str,
        new_status: OrderStatus
    ) -> Order:
        """Modify an order status, validating valid state transitions and performing restocking on cancellation."""
        order = await self.order_repo.get_by_id(order_id)
        if not order:
            raise EntityNotFoundException("Order not found")

        # Authorization Checks
        if user_role != "ADMIN":
            if order.user_id != user_id:
                raise PermissionDeniedException("Access denied. Insufficient permissions.")
            if new_status != OrderStatus.CANCELLED:
                raise PermissionDeniedException("Customers can only cancel their own orders.")
            if order.status not in (OrderStatus.CREATED, OrderStatus.PAID):
                raise InvalidOrderStatusException("Order cannot be cancelled at this stage.")

        # State Machine Transitions
        current = order.status
        allowed = False

        if current == OrderStatus.CREATED:
            allowed = new_status in (OrderStatus.PAID, OrderStatus.CANCELLED)
        elif current == OrderStatus.PAID:
            allowed = new_status in (OrderStatus.PROCESSING, OrderStatus.CANCELLED)
        elif current == OrderStatus.PROCESSING:
            allowed = new_status in (OrderStatus.SHIPPED, OrderStatus.CANCELLED)
        elif current == OrderStatus.SHIPPED:
            allowed = new_status == OrderStatus.DELIVERED
        elif current in (OrderStatus.DELIVERED, OrderStatus.CANCELLED):
            allowed = False  # Terminal states

        if not allowed:
            raise InvalidOrderStatusException(f"Invalid status transition from {current} to {new_status}")

        # Process restocking if transitioning to CANCELLED
        if new_status == OrderStatus.CANCELLED:
            logger.info(f"Restocking items for cancelled order: {order.id}")
            for item in order.items:
                await self.product_client.restock_stock(item.product_id, item.quantity)

            # Emit OrderCancelled event
            if self.producer_manager:
                try:
                    items_payload = [
                        OrderCreatedItem(product_id=item.product_id, quantity=item.quantity)
                        for item in order.items
                    ]
                    payload = OrderCancelledPayload(
                        order_id=order.id,
                        reason="Order cancelled or payment failed",
                        items=items_payload
                    )
                    envelope = EventEnvelope(
                        event_type="OrderCancelled",
                        payload=payload.model_dump()
                    )
                    await self.producer_manager.send_event("order-cancelled", envelope)
                except Exception as e:
                    logger.error(f"Failed to publish OrderCancelled event for order {order.id}: {e}")

        order.status = new_status
        updated_order = await self.order_repo.update(order)
        logger.info(f"Order {order.id} status updated to {new_status}")
        return updated_order
