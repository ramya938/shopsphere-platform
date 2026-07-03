import pytest
import uuid
from unittest.mock import AsyncMock, ANY
from src.domain.models import OrderStatus
from src.services.kafka_handlers import OrderKafkaHandler
from src.services.order_service import OrderService
from src.infrastructure.repositories.order_repository import SQLAlchemyOrderRepository
from src.infrastructure.repositories.cart_repository import SQLAlchemyCartRepository

class MockSessionContext:
    """Mock database session context for event handler testing."""
    def __init__(self, session):
        self.session = session

    async def __aenter__(self):
        return self.session

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


@pytest.mark.asyncio
async def test_order_kafka_handler_payment_completed(db_session, mock_product_client):
    order_repo = SQLAlchemyOrderRepository(db_session)
    cart_repo = SQLAlchemyCartRepository(db_session)
    
    mock_producer = AsyncMock()
    
    order_service = OrderService(
        order_repo=order_repo,
        cart_repo=cart_repo,
        product_client=mock_product_client,
        producer_manager=mock_producer
    )
    
    user_id = uuid.uuid4()
    product_id = uuid.uuid4()
    mock_product_client.add_mock_product(product_id, "Monitor", 300.0, 5)
    
    order = await order_service.place_direct_order(
        user_id=user_id,
        items=[{"product_id": product_id, "quantity": 1}],
        shipping_address="Test Address"
    )
    assert order.status == OrderStatus.CREATED

    def session_maker_override():
        return MockSessionContext(db_session)

    handler = OrderKafkaHandler(
        session_maker=session_maker_override,
        producer_manager=mock_producer,
        product_client=mock_product_client
    )
    
    event_dict = {
        "event_id": str(uuid.uuid4()),
        "event_type": "PaymentCompleted",
        "payload": {
            "order_id": str(order.id),
            "payment_id": str(uuid.uuid4()),
            "amount": 300.0,
            "transaction_id": "tx_abc123"
        }
    }
    
    await handler.handle_event(event_dict)
    
    await db_session.refresh(order)
    assert order.status == OrderStatus.PAID


@pytest.mark.asyncio
async def test_order_kafka_handler_payment_failed(db_session, mock_product_client):
    order_repo = SQLAlchemyOrderRepository(db_session)
    cart_repo = SQLAlchemyCartRepository(db_session)
    
    mock_producer = AsyncMock()
    
    order_service = OrderService(
        order_repo=order_repo,
        cart_repo=cart_repo,
        product_client=mock_product_client,
        producer_manager=mock_producer
    )
    
    user_id = uuid.uuid4()
    product_id = uuid.uuid4()
    mock_product_client.add_mock_product(product_id, "Monitor", 300.0, 5)
    
    order = await order_service.place_direct_order(
        user_id=user_id,
        items=[{"product_id": product_id, "quantity": 2}],
        shipping_address="Test Address"
    )
    
    prod = await mock_product_client.get_product(product_id)
    assert prod["inventory_quantity"] == 3

    def session_maker_override():
        return MockSessionContext(db_session)

    handler = OrderKafkaHandler(
        session_maker=session_maker_override,
        producer_manager=mock_producer,
        product_client=mock_product_client
    )
    
    event_dict = {
        "event_id": str(uuid.uuid4()),
        "event_type": "PaymentFailed",
        "payload": {
            "order_id": str(order.id),
            "amount": 600.0,
            "reason": "Card declined"
        }
    }
    
    await handler.handle_event(event_dict)
    
    await db_session.refresh(order)
    assert order.status == OrderStatus.CANCELLED

    prod = await mock_product_client.get_product(product_id)
    assert prod["inventory_quantity"] == 5

    assert mock_producer.send_event.call_count >= 1
    mock_producer.send_event.assert_called_with("order-cancelled", ANY)
