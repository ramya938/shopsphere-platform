import uuid
from unittest.mock import AsyncMock, patch
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.models import Payment
from src.infrastructure.repositories import SQLAlchemyPaymentRepository
from src.services.payment_service import PaymentService
from src.services.kafka_handlers import PaymentKafkaHandler
from src.core.kafka import KafkaProducerManager, KafkaConsumerManager
from src.domain.events import EventEnvelope

@pytest.mark.asyncio
async def test_payment_repository_add_and_get(db_session: AsyncSession):
    repo = SQLAlchemyPaymentRepository(db_session)
    order_id = uuid.uuid4()
    payment = Payment(
        order_id=order_id,
        amount=150.50,
        status="COMPLETED",
        transaction_id="tx_12345"
    )
    
    saved = await repo.add(payment)
    assert saved.id is not None
    assert saved.amount == 150.50
    assert saved.status == "COMPLETED"
    
    # Get by ID
    fetched = await repo.get_by_id(saved.id)
    assert fetched is not None
    assert fetched.order_id == order_id
    
    # Get by order ID
    fetched_order = await repo.get_by_order_id(order_id)
    assert fetched_order is not None
    assert fetched_order.id == saved.id

@pytest.mark.asyncio
async def test_payment_service_success(db_session: AsyncSession):
    repo = SQLAlchemyPaymentRepository(db_session)
    mock_producer = AsyncMock(spec=KafkaProducerManager)
    service = PaymentService(payment_repo=repo, producer_manager=mock_producer)
    
    order_id = uuid.uuid4()
    payment = await service.process_payment(order_id=order_id, amount=100.00)
    
    assert payment.status == "COMPLETED"
    assert payment.transaction_id.startswith("tx_")
    assert payment.amount == 100.00
    
    # Verify Kafka event published
    mock_producer.send_event.assert_called_once()
    args, kwargs = mock_producer.send_event.call_args
    assert args[0] == "payment-completed"
    envelope = args[1]
    assert isinstance(envelope, EventEnvelope)
    assert envelope.event_type == "PaymentCompleted"
    assert envelope.payload["order_id"] == order_id
    assert envelope.payload["amount"] == 100.00
    assert envelope.payload["transaction_id"] == payment.transaction_id

@pytest.mark.asyncio
async def test_payment_service_failure_simulation(db_session: AsyncSession):
    repo = SQLAlchemyPaymentRepository(db_session)
    mock_producer = AsyncMock(spec=KafkaProducerManager)
    service = PaymentService(payment_repo=repo, producer_manager=mock_producer)
    
    order_id = uuid.uuid4()
    payment = await service.process_payment(order_id=order_id, amount=9999.99)
    
    assert payment.status == "FAILED"
    assert payment.transaction_id is None
    
    # Verify Kafka event published
    mock_producer.send_event.assert_called_once()
    args, kwargs = mock_producer.send_event.call_args
    assert args[0] == "payment-failed"
    envelope = args[1]
    assert isinstance(envelope, EventEnvelope)
    assert envelope.event_type == "PaymentFailed"
    assert envelope.payload["order_id"] == order_id
    assert envelope.payload["amount"] == 9999.99
    assert "declined" in envelope.payload["reason"]

@pytest.mark.asyncio
async def test_payment_service_idempotent(db_session: AsyncSession):
    repo = SQLAlchemyPaymentRepository(db_session)
    mock_producer = AsyncMock(spec=KafkaProducerManager)
    service = PaymentService(payment_repo=repo, producer_manager=mock_producer)
    
    order_id = uuid.uuid4()
    p1 = await service.process_payment(order_id=order_id, amount=50.0)
    mock_producer.send_event.reset_mock()
    
    # Second payment process on same order_id
    p2 = await service.process_payment(order_id=order_id, amount=50.0)
    assert p1.id == p2.id
    mock_producer.send_event.assert_not_called()

@pytest.mark.asyncio
async def test_payment_kafka_handler_handles_order_created(db_session: AsyncSession):
    # Prepare handler
    mock_producer = AsyncMock(spec=KafkaProducerManager)
    class MockContext:
        async def __aenter__(self):
            return db_session
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass
    session_maker = lambda: MockContext()
    
    handler = PaymentKafkaHandler(session_maker=session_maker, producer_manager=mock_producer)
    
    order_id = uuid.uuid4()
    event_payload = {
        "event_type": "OrderCreated",
        "payload": {
            "order_id": str(order_id),
            "total_price": 75.50
        }
    }
    
    await handler.handle_event(event_payload)
    
    # Check that payment was inserted in DB
    repo = SQLAlchemyPaymentRepository(db_session)
    payment = await repo.get_by_order_id(order_id)
    assert payment is not None
    assert payment.amount == 75.50
    assert payment.status == "COMPLETED"
    
    # Check that event was produced
    mock_producer.send_event.assert_called_once()

@pytest.mark.asyncio
async def test_payment_kafka_handler_ignores_other_events(db_session: AsyncSession):
    mock_producer = AsyncMock(spec=KafkaProducerManager)
    session_maker = AsyncMock()
    handler = PaymentKafkaHandler(session_maker=session_maker, producer_manager=mock_producer)
    
    event_payload = {
        "event_type": "OtherEvent",
        "payload": {
            "order_id": str(uuid.uuid4())
        }
    }
    
    await handler.handle_event(event_payload)
    session_maker.assert_not_called()
    mock_producer.send_event.assert_not_called()

@pytest.mark.asyncio
async def test_kafka_consumer_manager_retry_and_dlq():
    mock_producer = AsyncMock(spec=KafkaProducerManager)
    consumer = KafkaConsumerManager(
        topics=["order-created"],
        group_id="test-group",
        producer_manager=mock_producer
    )
    
    # Handler callback that always fails
    calls = []
    async def failing_handler(event):
        calls.append(event)
        raise ValueError("Simulated processing error")
        
    event_dict = {
        "event_id": str(uuid.uuid4()),
        "event_type": "OrderCreated",
        "payload": {"order_id": str(uuid.uuid4()), "total_price": 100.0}
    }
    
    with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        await consumer._process_message_with_retry("order-created", event_dict, failing_handler)
        
        # Should have called handler 3 times
        assert len(calls) == 3
        # Should have slept twice (exponential backoff)
        assert mock_sleep.call_count == 2
        # Verify first sleep was 1.0s, second was 2.0s
        mock_sleep.assert_any_call(1.0)
        mock_sleep.assert_any_call(2.0)
        
        # Verify routed to DLQ
        mock_producer.send_event.assert_called_once()
        args, kwargs = mock_producer.send_event.call_args
        assert args[0] == "order-created-dlq"
        envelope = args[1]
        assert envelope.event_type == "OrderCreated_DLQ"
        assert envelope.payload["error_reason"] == "Simulated processing error"
