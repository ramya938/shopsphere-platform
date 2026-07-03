import uuid
from unittest.mock import AsyncMock, patch
import pytest

from src.services.notification_service import NotificationService
from src.services.kafka_handlers import NotificationKafkaHandler
from src.core.kafka import KafkaProducerManager, KafkaConsumerManager
from src.domain.events import EventEnvelope

@pytest.mark.asyncio
async def test_notification_service_send():
    mock_producer = AsyncMock(spec=KafkaProducerManager)
    service = NotificationService(producer_manager=mock_producer)
    
    order_id = uuid.uuid4()
    notification_id = await service.send_notification(
        order_id=order_id,
        recipient_email="test@shopsphere.ai",
        subject="Hello",
        message="Your order status update."
    )
    
    assert isinstance(notification_id, uuid.UUID)
    
    # Check event sent to Kafka
    mock_producer.send_event.assert_called_once()
    args, kwargs = mock_producer.send_event.call_args
    assert args[0] == "notification-sent"
    envelope = args[1]
    assert isinstance(envelope, EventEnvelope)
    assert envelope.event_type == "NotificationSent"
    assert envelope.payload["order_id"] == order_id
    assert envelope.payload["recipient_email"] == "test@shopsphere.ai"
    assert envelope.payload["type"] == "email"

@pytest.mark.asyncio
async def test_notification_kafka_handler_order_created():
    mock_service = AsyncMock(spec=NotificationService)
    handler = NotificationKafkaHandler(notification_service=mock_service)
    
    order_id = uuid.uuid4()
    event_payload = {
        "event_type": "OrderCreated",
        "payload": {
            "order_id": str(order_id),
            "total_price": 299.99
        }
    }
    
    await handler.handle_event(event_payload)
    mock_service.send_notification.assert_called_once_with(
        order_id=order_id,
        recipient_email="customer@shopsphere.ai",
        subject="Order Received!",
        message=f"Your order '{order_id}' totaling $299.99 was created and is pending payment."
    )

@pytest.mark.asyncio
async def test_notification_kafka_handler_payment_completed():
    mock_service = AsyncMock(spec=NotificationService)
    handler = NotificationKafkaHandler(notification_service=mock_service)
    
    order_id = uuid.uuid4()
    event_payload = {
        "event_type": "PaymentCompleted",
        "payload": {
            "order_id": str(order_id),
            "transaction_id": "tx_abc123"
        }
    }
    
    await handler.handle_event(event_payload)
    mock_service.send_notification.assert_called_once_with(
        order_id=order_id,
        recipient_email="customer@shopsphere.ai",
        subject="Payment Confirmed!",
        message=f"We received your payment for order '{order_id}'. Transaction Reference: tx_abc123."
    )

@pytest.mark.asyncio
async def test_notification_kafka_handler_payment_failed():
    mock_service = AsyncMock(spec=NotificationService)
    handler = NotificationKafkaHandler(notification_service=mock_service)
    
    order_id = uuid.uuid4()
    event_payload = {
        "event_type": "PaymentFailed",
        "payload": {
            "order_id": str(order_id),
            "reason": "Card declined"
        }
    }
    
    await handler.handle_event(event_payload)
    mock_service.send_notification.assert_called_once_with(
        order_id=order_id,
        recipient_email="customer@shopsphere.ai",
        subject="Payment Attempt Failed!",
        message=f"Payment for order '{order_id}' was declined. Reason: Card declined."
    )

@pytest.mark.asyncio
async def test_notification_kafka_handler_order_cancelled():
    mock_service = AsyncMock(spec=NotificationService)
    handler = NotificationKafkaHandler(notification_service=mock_service)
    
    order_id = uuid.uuid4()
    event_payload = {
        "event_type": "OrderCancelled",
        "payload": {
            "order_id": str(order_id),
            "reason": "Customer request"
        }
    }
    
    await handler.handle_event(event_payload)
    mock_service.send_notification.assert_called_once_with(
        order_id=order_id,
        recipient_email="customer@shopsphere.ai",
        subject="Order Cancelled!",
        message=f"Your order '{order_id}' has been cancelled. Reason: Customer request."
    )

@pytest.mark.asyncio
async def test_notification_kafka_handler_missing_order_id():
    mock_service = AsyncMock(spec=NotificationService)
    handler = NotificationKafkaHandler(notification_service=mock_service)
    
    event_payload = {
        "event_type": "OrderCreated",
        "payload": {
            "total_price": 299.99
        }
    }
    
    await handler.handle_event(event_payload)
    mock_service.send_notification.assert_not_called()

@pytest.mark.asyncio
async def test_notification_kafka_handler_unhandled_event():
    mock_service = AsyncMock(spec=NotificationService)
    handler = NotificationKafkaHandler(notification_service=mock_service)
    
    event_payload = {
        "event_type": "UnknownEvent",
        "payload": {
            "order_id": str(uuid.uuid4())
        }
    }
    
    await handler.handle_event(event_payload)
    mock_service.send_notification.assert_not_called()
