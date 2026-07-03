import pytest
import uuid
from src.services.order_service import OrderService
from src.services.cart_service import CartService
from src.infrastructure.repositories.order_repository import SQLAlchemyOrderRepository
from src.infrastructure.repositories.cart_repository import SQLAlchemyCartRepository
from src.domain.models import OrderStatus
from src.core.exceptions import (
    EntityNotFoundException,
    BaseAppException,
    InventoryInsufficientException,
    PermissionDeniedException,
    InvalidOrderStatusException
)

@pytest.mark.asyncio
async def test_checkout_cart_success(db_session, mock_product_client):
    order_repo = SQLAlchemyOrderRepository(db_session)
    cart_repo = SQLAlchemyCartRepository(db_session)
    order_service = OrderService(order_repo, cart_repo, mock_product_client)
    cart_service = CartService(cart_repo, mock_product_client)

    user_id = uuid.uuid4()
    product_id = uuid.uuid4()
    mock_product_client.add_mock_product(product_id, "Laptop", 1200.0, 5)

    # Populate cart
    await cart_service.add_item_to_cart(user_id, product_id, 2)

    # Checkout
    order = await order_service.checkout_cart(user_id, "123 Main St")
    assert order.user_id == user_id
    assert order.total_price == 2400.0
    assert order.status == OrderStatus.CREATED
    assert len(order.items) == 1
    assert order.items[0].product_id == product_id
    assert order.items[0].quantity == 2
    assert order.items[0].price_at_purchase == 1200.0

    # Cart should now be empty
    cart = await cart_service.get_or_create_cart(user_id)
    assert len(cart.items) == 0

    # Stock should be deducted
    prod = await mock_product_client.get_product(product_id)
    assert prod["inventory_quantity"] == 3


@pytest.mark.asyncio
async def test_checkout_empty_cart_fails(db_session, mock_product_client):
    order_repo = SQLAlchemyOrderRepository(db_session)
    cart_repo = SQLAlchemyCartRepository(db_session)
    order_service = OrderService(order_repo, cart_repo, mock_product_client)

    user_id = uuid.uuid4()
    with pytest.raises(BaseAppException):
        await order_service.checkout_cart(user_id, "123 Main St")


@pytest.mark.asyncio
async def test_checkout_cart_compensating_transaction(db_session, mock_product_client):
    order_repo = SQLAlchemyOrderRepository(db_session)
    cart_repo = SQLAlchemyCartRepository(db_session)
    order_service = OrderService(order_repo, cart_repo, mock_product_client)
    cart_service = CartService(cart_repo, mock_product_client)

    user_id = uuid.uuid4()
    prod_id_1 = uuid.uuid4()
    prod_id_2 = uuid.uuid4()

    mock_product_client.add_mock_product(prod_id_1, "Product 1", 10.00, 5)
    mock_product_client.add_mock_product(prod_id_2, "Product 2", 20.00, 2)

    await cart_service.add_item_to_cart(user_id, prod_id_1, 2)
    await cart_service.add_item_to_cart(user_id, prod_id_2, 2)

    # Suddenly update stock of Product 2 to be insufficient (simulating race condition)
    prod_2 = await mock_product_client.get_product(prod_id_2)
    prod_2["inventory_quantity"] = 0

    with pytest.raises(InventoryInsufficientException):
        await order_service.checkout_cart(user_id, "123 Main St")

    # Product 1 stock should have been rolled back (restocked) to 5
    prod_1 = await mock_product_client.get_product(prod_id_1)
    assert prod_1["inventory_quantity"] == 5


@pytest.mark.asyncio
async def test_place_direct_order_success(db_session, mock_product_client):
    order_repo = SQLAlchemyOrderRepository(db_session)
    cart_repo = SQLAlchemyCartRepository(db_session)
    order_service = OrderService(order_repo, cart_repo, mock_product_client)

    user_id = uuid.uuid4()
    product_id = uuid.uuid4()
    mock_product_client.add_mock_product(product_id, "Book", 15.0, 10)

    items = [{"product_id": product_id, "quantity": 3}]
    order = await order_service.place_direct_order(user_id, items, "456 Oak Rd")

    assert order.total_price == 45.0
    assert order.status == OrderStatus.CREATED
    assert order.items[0].product_id == product_id
    assert order.items[0].quantity == 3


@pytest.mark.asyncio
async def test_get_order_authorization(db_session, mock_product_client):
    order_repo = SQLAlchemyOrderRepository(db_session)
    cart_repo = SQLAlchemyCartRepository(db_session)
    order_service = OrderService(order_repo, cart_repo, mock_product_client)

    user_id = uuid.uuid4()
    other_user_id = uuid.uuid4()
    product_id = uuid.uuid4()
    mock_product_client.add_mock_product(product_id, "Book", 15.0, 10)

    items = [{"product_id": product_id, "quantity": 1}]
    order = await order_service.place_direct_order(user_id, items, "456 Oak Rd")

    # Owner can get
    res = await order_service.get_order(order.id, user_id, "CUSTOMER")
    assert res.id == order.id

    # Admin can get
    res_admin = await order_service.get_order(order.id, other_user_id, "ADMIN")
    assert res_admin.id == order.id

    # Other customer cannot get
    with pytest.raises(PermissionDeniedException):
        await order_service.get_order(order.id, other_user_id, "CUSTOMER")


@pytest.mark.asyncio
async def test_transition_status_and_cancel_restock(db_session, mock_product_client):
    order_repo = SQLAlchemyOrderRepository(db_session)
    cart_repo = SQLAlchemyCartRepository(db_session)
    order_service = OrderService(order_repo, cart_repo, mock_product_client)

    user_id = uuid.uuid4()
    product_id = uuid.uuid4()
    mock_product_client.add_mock_product(product_id, "Book", 15.0, 10)

    items = [{"product_id": product_id, "quantity": 3}]
    order = await order_service.place_direct_order(user_id, items, "456 Oak Rd")
    
    # Stock deducted to 7
    prod = await mock_product_client.get_product(product_id)
    assert prod["inventory_quantity"] == 7

    # Customer cancels order
    cancelled_order = await order_service.transition_status(order.id, user_id, "CUSTOMER", OrderStatus.CANCELLED)
    assert cancelled_order.status == OrderStatus.CANCELLED

    # Stock should be restocked back to 10
    prod = await mock_product_client.get_product(product_id)
    assert prod["inventory_quantity"] == 10
