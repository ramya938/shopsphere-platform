import uuid
from loguru import logger
from sqlalchemy.ext.asyncio import async_sessionmaker
from src.infrastructure.repositories import SQLAlchemyPaymentRepository
from src.services.payment_service import PaymentService
from src.core.kafka import KafkaProducerManager

class PaymentKafkaHandler:
    """Listens for OrderCreated events to process orders payments asynchronously."""

    def __init__(self, session_maker: async_sessionmaker, producer_manager: KafkaProducerManager | None = None):
        self.session_maker = session_maker
        self.producer_manager = producer_manager

    async def handle_event(self, event_dict: dict):
        event_type = event_dict.get("event_type")
        payload = event_dict.get("payload", {})
        
        logger.info(f"Payment Kafka Handler processing event '{event_type}'")
        
        if event_type != "OrderCreated":
            logger.debug(f"Received unhandled event type '{event_type}' in Payment Service")
            return

        order_id_str = payload.get("order_id")
        total_price = payload.get("total_price")
        
        if not order_id_str or total_price is None:
            logger.error("OrderCreated event payload missing order_id or total_price")
            return
            
        order_id = uuid.UUID(order_id_str)
        amount = float(total_price)
        
        # Instantiate fresh session for message processing to support concurrency safely
        async with self.session_maker() as session:
            try:
                payment_repo = SQLAlchemyPaymentRepository(session)
                payment_service = PaymentService(payment_repo=payment_repo, producer_manager=self.producer_manager)
                
                await payment_service.process_payment(order_id=order_id, amount=amount)
                # Commit the transaction
                await session.commit()
            except Exception as e:
                logger.error(f"Failed to process payment for order {order_id}: {e}")
                await session.rollback()
                raise e
