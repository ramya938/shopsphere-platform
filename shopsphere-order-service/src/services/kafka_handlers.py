import uuid
from loguru import logger
from sqlalchemy.ext.asyncio import async_sessionmaker
from src.domain.models import OrderStatus
from src.infrastructure.repositories.order_repository import SQLAlchemyOrderRepository
from src.infrastructure.repositories.cart_repository import SQLAlchemyCartRepository
from src.infrastructure.clients.product_client import ProductClient
from src.services.order_service import OrderService
from src.core.kafka import KafkaProducerManager

class OrderKafkaHandler:
    """Processes incoming payment events from Kafka to update order states within dedicated sessions."""

    def __init__(
        self,
        session_maker: async_sessionmaker,
        producer_manager: KafkaProducerManager | None = None,
        product_client: ProductClient | None = None
    ):
        self.session_maker = session_maker
        self.producer_manager = producer_manager
        self.product_client = product_client or ProductClient()

    async def handle_event(self, event_dict: dict):
        event_type = event_dict.get("event_type")
        payload = event_dict.get("payload", {})
        
        logger.info(f"Order Kafka Handler processing event '{event_type}'")
        
        if event_type not in ("PaymentCompleted", "PaymentFailed"):
            logger.debug(f"Received unhandled event type '{event_type}' in Order Service")
            return

        order_id_str = payload.get("order_id")
        if not order_id_str:
            logger.error(f"Event {event_type} payload missing order_id")
            return
        
        order_id = uuid.UUID(order_id_str)
        
        # Instantiate fresh session for message processing to support concurrency safely
        async with self.session_maker() as session:
            try:
                order_repo = SQLAlchemyOrderRepository(session)
                cart_repo = SQLAlchemyCartRepository(session)
                
                order_service = OrderService(
                    order_repo=order_repo,
                    cart_repo=cart_repo,
                    product_client=self.product_client,
                    producer_manager=self.producer_manager
                )
                
                system_user = uuid.UUID("00000000-0000-0000-0000-000000000000")
                
                if event_type == "PaymentCompleted":
                    logger.info(f"Handling PaymentCompleted: Transitioning order {order_id} to PAID")
                    await order_service.transition_status(
                        order_id=order_id,
                        user_id=system_user,
                        user_role="ADMIN",
                        new_status=OrderStatus.PAID
                    )
                    await session.commit()
                    
                elif event_type == "PaymentFailed":
                    reason = payload.get("reason", "Payment failed")
                    logger.warning(f"Handling PaymentFailed for order {order_id}. Reason: {reason}")
                    await order_service.transition_status(
                        order_id=order_id,
                        user_id=system_user,
                        user_role="ADMIN",
                        new_status=OrderStatus.CANCELLED
                    )
                    await session.commit()
            except Exception as e:
                logger.error(f"Failed to handle event {event_type} for order {order_id}: {e}")
                await session.rollback()
                raise e
