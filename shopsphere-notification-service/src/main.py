import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from src.config import settings
from src.core.logging import setup_logging
from src.core.kafka import KafkaProducerManager, KafkaConsumerManager
from src.services.notification_service import NotificationService
from src.services.kafka_handlers import NotificationKafkaHandler

# Initialize logging configuration before FastAPI bootstrap
setup_logging()

# Global producer manager singleton
_kafka_producer = KafkaProducerManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup:
    # 1. Start Kafka Producer
    await _kafka_producer.start()

    # 2. Start Kafka Consumer subscribing to all order & payment lifecycle events
    notification_service = NotificationService(producer_manager=_kafka_producer)
    handler = NotificationKafkaHandler(notification_service=notification_service)
    
    consumer_manager = KafkaConsumerManager(
        topics=["order-created", "payment-completed", "payment-failed", "order-cancelled"],
        group_id="notification-service-group",
        producer_manager=_kafka_producer
    )
    await consumer_manager.start()

    # 3. Start consume loop as a background task
    polling_task = asyncio.create_task(consumer_manager.consume_loop(handler.handle_event))

    yield

    # Shutdown:
    await consumer_manager.stop()
    polling_task.cancel()
    try:
        await polling_task
    except asyncio.CancelledError:
        pass
    
    await _kafka_producer.stop()


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Enterprise-grade Clean Architecture Notification Microservice for ShopSphere AI.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configurations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health", tags=["Health"])
async def health_check():
    """Simple service health probe."""
    return {"status": "healthy", "service": settings.PROJECT_NAME}
