import uuid
from loguru import logger
from src.domain.models import Payment
from src.infrastructure.repositories import SQLAlchemyPaymentRepository
from src.core.kafka import KafkaProducerManager
from src.domain.events import EventEnvelope, PaymentCompletedPayload, PaymentFailedPayload

class PaymentService:
    """Orchestrates order payment processing, database logging, and Kafka streaming."""

    def __init__(self, payment_repo: SQLAlchemyPaymentRepository, producer_manager: KafkaProducerManager | None = None):
        self.payment_repo = payment_repo
        self.producer_manager = producer_manager

    async def process_payment(self, order_id: uuid.UUID, amount: float) -> Payment:
        logger.info(f"Processing payment of amount {amount} for order {order_id}")
        
        # Prevent double-processing
        existing = await self.payment_repo.get_by_order_id(order_id)
        if existing:
            logger.info(f"Payment already processed for order {order_id} (ID: {existing.id})")
            return existing

        # Deterministic simulation rule: fail if amount matches exactly 9999.99
        is_success = amount != 9999.99

        if is_success:
            transaction_id = f"tx_{uuid.uuid4().hex[:12]}"
            payment = Payment(
                order_id=order_id,
                amount=amount,
                status="COMPLETED",
                transaction_id=transaction_id
            )
            saved_payment = await self.payment_repo.add(payment)
            logger.info(f"Payment COMPLETED (ID: {saved_payment.id}, Transaction: {transaction_id}) for order {order_id}")
            
            # Publish PaymentCompleted event
            if self.producer_manager:
                try:
                    payload = PaymentCompletedPayload(
                        payment_id=saved_payment.id,
                        order_id=order_id,
                        amount=amount,
                        transaction_id=transaction_id
                    )
                    envelope = EventEnvelope(
                        event_type="PaymentCompleted",
                        payload=payload.model_dump()
                    )
                    await self.producer_manager.send_event("payment-completed", envelope)
                except Exception as e:
                    logger.error(f"Failed to publish PaymentCompleted event for order {order_id}: {e}")
                    
            return saved_payment
        else:
            payment = Payment(
                order_id=order_id,
                amount=amount,
                status="FAILED",
                transaction_id=None
            )
            saved_payment = await self.payment_repo.add(payment)
            logger.warning(f"Payment FAILED (ID: {saved_payment.id}) for order {order_id}")
            
            # Publish PaymentFailed event
            if self.producer_manager:
                try:
                    payload = PaymentFailedPayload(
                        order_id=order_id,
                        amount=amount,
                        reason="Limit exceeded or card declined (simulated)"
                    )
                    envelope = EventEnvelope(
                        event_type="PaymentFailed",
                        payload=payload.model_dump()
                    )
                    await self.producer_manager.send_event("payment-failed", envelope)
                except Exception as e:
                    logger.error(f"Failed to publish PaymentFailed event for order {order_id}: {e}")
                    
            return saved_payment
