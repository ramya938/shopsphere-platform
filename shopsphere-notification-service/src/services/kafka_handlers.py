import uuid
from loguru import logger
from src.services.notification_service import NotificationService

class NotificationKafkaHandler:
    """Processes system events and dispatches notifications."""

    def __init__(self, notification_service: NotificationService):
        self.notification_service = notification_service

    async def handle_event(self, event_dict: dict):
        event_type = event_dict.get("event_type")
        payload = event_dict.get("payload", {})
        
        logger.info(f"Notification Kafka Handler processing event '{event_type}'")
        
        order_id_str = payload.get("order_id")
        if not order_id_str:
            logger.error("Event payload missing order_id. Skipping notification.")
            return
            
        order_id = uuid.UUID(order_id_str)
        recipient_email = "customer@shopsphere.ai"  # Default simulated recipient

        if event_type == "OrderCreated":
            amount = payload.get("total_price")
            await self.notification_service.send_notification(
                order_id=order_id,
                recipient_email=recipient_email,
                subject="Order Received!",
                message=f"Your order '{order_id}' totaling ${amount} was created and is pending payment."
            )
            
        elif event_type == "PaymentCompleted":
            tx_id = payload.get("transaction_id")
            await self.notification_service.send_notification(
                order_id=order_id,
                recipient_email=recipient_email,
                subject="Payment Confirmed!",
                message=f"We received your payment for order '{order_id}'. Transaction Reference: {tx_id}."
            )
            
        elif event_type == "PaymentFailed":
            reason = payload.get("reason", "Limit exceeded")
            await self.notification_service.send_notification(
                order_id=order_id,
                recipient_email=recipient_email,
                subject="Payment Attempt Failed!",
                message=f"Payment for order '{order_id}' was declined. Reason: {reason}."
            )
            
        elif event_type == "OrderCancelled":
            reason = payload.get("reason", "Cancellation request")
            await self.notification_service.send_notification(
                order_id=order_id,
                recipient_email=recipient_email,
                subject="Order Cancelled!",
                message=f"Your order '{order_id}' has been cancelled. Reason: {reason}."
            )
        else:
            logger.debug(f"Received unhandled event '{event_type}' in Notification Service")
network_config = {}
