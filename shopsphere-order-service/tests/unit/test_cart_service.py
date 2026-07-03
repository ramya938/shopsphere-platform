import pytest
import uuid
from src.services.cart_service import CartService
from src.infrastructure.repositories.cart_repository import SQLAlchemyCartRepository
from src.core.exceptions import EntityNotFoundException, BaseAppException, InventoryInsufficientException

@pytest.mark.asyncio
async def test_get_or_create_cart(db_session, mock_product_client):
    cart_repo = SQLAlchemyCartRepository(db_session)
    cart_service = CartService(cart_repo, mock_product_client)
    
    user_id = uuid.uuid4()
    cart = await cart_service.get_or_create_cart(user_id)
    
    assert cart.user_id == user_id
    assert len(cart.items) == 0

    # Getting it again should return the same cart
    cart2 = await cart_service.get_or_create_cart(user_id)
    assert cart.id == cart2.id


@pytest.mark.asyncio
async def test_add_item_to_cart_success(db_session, mock_product_client):
    cart_repo = SQLAlchemyCartRepository(db_session)
    cart_service = CartService(cart_repo, mock_product_client)
    
    user_id = uuid.uuid4()
    product_id = uuid.uuid4()
    mock_product_client.add_mock_product(product_id, "Widget", 9.99, 10)

    cart = await cart_service.add_item_to_cart(user_id, product_id, 2)
    assert len(cart.items) == 1
    assert cart.items[0].product_id == product_id
    assert cart.items[0].quantity == 2


@pytest.mark.asyncio
async def test_add_item_to_cart_insufficient_stock(db_session, mock_product_client):
    cart_repo = SQLAlchemyCartRepository(db_session)
    cart_service = CartService(cart_repo, mock_product_client)
    
    user_id = uuid.uuid4()
    product_id = uuid.uuid4()
    mock_product_client.add_mock_product(product_id, "Widget", 9.99, 5)

    with pytest.raises(InventoryInsufficientException):
        await cart_service.add_item_to_cart(user_id, product_id, 10)


@pytest.mark.asyncio
async def test_add_item_to_cart_product_not_found(db_session, mock_product_client):
    cart_repo = SQLAlchemyCartRepository(db_session)
    cart_service = CartService(cart_repo, mock_product_client)
    
    user_id = uuid.uuid4()
    product_id = uuid.uuid4()

    with pytest.raises(EntityNotFoundException):
        await cart_service.add_item_to_cart(user_id, product_id, 1)


@pytest.mark.asyncio
async def test_update_item_quantity(db_session, mock_product_client):
    cart_repo = SQLAlchemyCartRepository(db_session)
    cart_service = CartService(cart_repo, mock_product_client)
    
    user_id = uuid.uuid4()
    product_id = uuid.uuid4()
    mock_product_client.add_mock_product(product_id, "Widget", 9.99, 10)

    await cart_service.add_item_to_cart(user_id, product_id, 2)
    
    # Update to 5
    cart = await cart_service.update_item_quantity(user_id, product_id, 5)
    assert cart.items[0].quantity == 5

    # Update to 0 (should remove)
    cart = await cart_service.update_item_quantity(user_id, product_id, 0)
    assert len(cart.items) == 0


@pytest.mark.asyncio
async def test_remove_item_from_cart(db_session, mock_product_client):
    cart_repo = SQLAlchemyCartRepository(db_session)
    cart_service = CartService(cart_repo, mock_product_client)
    
    user_id = uuid.uuid4()
    product_id = uuid.uuid4()
    mock_product_client.add_mock_product(product_id, "Widget", 9.99, 10)

    await cart_service.add_item_to_cart(user_id, product_id, 2)
    cart = await cart_service.remove_item_from_cart(user_id, product_id)
    assert len(cart.items) == 0
