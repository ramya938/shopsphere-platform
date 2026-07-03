import uuid
from loguru import logger
from src.core.kafka import KafkaProducerManager
from src.domain.events import EventEnvelope, NotificationSentPayload

class NotificationService:
    """Simulates sending user notifications and produces NotificationSent events to Kafka."""

    def __init__(self, producer_manager: KafkaProducerManager | None = None):
        self.producer_manager = producer_manager

    async def send_notification(self, order_id: uuid.UUID, recipient_email: str, subject: str, message: str, notification_type: str = "email") -> uuid.UUID:
        notification_id = uuid.uuid4()
        logger.info(
            f"Notification [{notification_type.upper()}] Sent (ID: {notification_id}) "
            f"to {recipient_email} | Subject: '{subject}' | Content: '{message}'"
        )
        
        # Publish NotificationSent event
        if self.producer_manager:
            try:
                payload = NotificationSentPayload(
                    notification_id=notification_id,
                    order_id=order_id,
                    recipient_email=recipient_email,
                    type=notification_type
                )
                envelope = EventEnvelope(
                    event_type="NotificationSent",
                    payload=payload.model_dump()
                )
                await self.producer_manager.send_event("notification-sent", envelope)
            except Exception as e:
                logger.error(f"Failed to publish NotificationSent event for order {order_id}: {e}")
                
        return notification_id
