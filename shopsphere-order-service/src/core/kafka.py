import asyncio
import json
import uuid
from typing import Callable, Awaitable
from datetime import datetime, timezone
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from loguru import logger
from src.config import settings
from src.domain.events import EventEnvelope

class KafkaProducerManager:
    """Async producer manager for Apache Kafka integration."""

    def __init__(self, bootstrap_servers: str = settings.KAFKA_BOOTSTRAP_SERVERS):
        self.bootstrap_servers = bootstrap_servers
        self.producer = None

    async def start(self):
        logger.info(f"Starting Kafka Producer on servers: {self.bootstrap_servers}")
        self.producer = AIOKafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            value_serializer=lambda v: json.dumps(v, default=str).encode('utf-8')
        )
        await self.producer.start()
        logger.info("Kafka Producer started successfully.")

    async def stop(self):
        if self.producer:
            logger.info("Stopping Kafka Producer...")
            await self.producer.stop()
            logger.info("Kafka Producer stopped successfully.")

    async def send_event(self, topic: str, event: EventEnvelope):
        if not self.producer:
            raise RuntimeError("Kafka Producer is not started. Call start() first.")
        
        event_dict = event.model_dump()
        # Convert UUID to string for JSON serialization
        event_dict["event_id"] = str(event.event_id)
        event_dict["timestamp"] = event.timestamp.isoformat()
        
        logger.info(f"Publishing event {event.event_type} (id: {event.event_id}) to topic '{topic}'")
        await self.producer.send_and_wait(topic, event_dict)


class KafkaConsumerManager:
    """Async consumer manager with auto-retries and Dead Letter Queue routing."""

    def __init__(
        self,
        topics: list[str],
        group_id: str,
        bootstrap_servers: str = settings.KAFKA_BOOTSTRAP_SERVERS,
        producer_manager: KafkaProducerManager | None = None
    ):
        self.topics = topics
        self.group_id = group_id
        self.bootstrap_servers = bootstrap_servers
        self.consumer = None
        self.producer_manager = producer_manager
        self.is_running = False

    async def start(self):
        logger.info(f"Starting Kafka Consumer for topics {self.topics} (Group ID: {self.group_id})")
        self.consumer = AIOKafkaConsumer(
            *self.topics,
            bootstrap_servers=self.bootstrap_servers,
            group_id=self.group_id,
            auto_offset_reset="earliest",
            enable_auto_commit=True,
            value_deserializer=lambda m: json.loads(m.decode('utf-8'))
        )
        await self.consumer.start()
        self.is_running = True
        logger.info("Kafka Consumer started successfully.")

    async def stop(self):
        self.is_running = False
        if self.consumer:
            logger.info("Stopping Kafka Consumer...")
            await self.consumer.stop()
            logger.info("Kafka Consumer stopped successfully.")

    async def consume_loop(self, handler_callback: Callable[[dict], Awaitable[None]]):
        """Infinite polling loop routing messages to handling callbacks."""
        logger.info("Starting Kafka consume loop...")
        while self.is_running:
            try:
                # Retrieve messages batch
                msg_set = await self.consumer.getmany(timeout_ms=1000)
                for topic_partition, messages in msg_set.items():
                    for message in messages:
                        if not self.is_running:
                            break
                        event_dict = message.value
                        topic = topic_partition.topic
                        await self._process_message_with_retry(topic, event_dict, handler_callback)
            except Exception as e:
                logger.error(f"Error in Kafka consumer loop: {e}")
                await asyncio.sleep(2)  # Backoff before loop retry

    async def _process_message_with_retry(
        self,
        topic: str,
        event_dict: dict,
        handler_callback: Callable[[dict], Awaitable[None]]
    ):
        max_retries = 3
        backoff = 1.0  # seconds

        for attempt in range(1, max_retries + 1):
            try:
                await handler_callback(event_dict)
                return  # Processed successfully, exit retry loop
            except Exception as exc:
                logger.warning(
                    f"Attempt {attempt}/{max_retries} failed to process event {event_dict.get('event_type')} "
                    f"(id: {event_dict.get('event_id')}) in topic '{topic}'. Error: {exc}"
                )
                if attempt < max_retries:
                    await asyncio.sleep(backoff)
                    backoff *= 2  # Exponential backoff
                else:
                    # Retries exhausted, route to DLQ
                    await self._route_to_dlq(topic, event_dict, str(exc))

    async def _route_to_dlq(self, original_topic: str, event_dict: dict, error_message: str):
        dlq_topic = f"{original_topic}-dlq"
        logger.error(
            f"Retries exhausted. Routing toxic event {event_dict.get('event_type')} "
            f"(id: {event_dict.get('event_id')}) from topic '{original_topic}' to DLQ '{dlq_topic}'"
        )
        
        dlq_payload = {
            "event_id": event_dict.get("event_id", str(uuid.uuid4())),
            "event_type": f"{event_dict.get('event_type')}_DLQ",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "original_topic": original_topic,
            "error_reason": error_message,
            "payload": event_dict.get("payload", event_dict)
        }

        if self.producer_manager:
            try:
                envelope = EventEnvelope(
                    event_id=uuid.UUID(dlq_payload["event_id"]),
                    event_type=dlq_payload["event_type"],
                    payload=dlq_payload
                )
                await self.producer_manager.send_event(dlq_topic, envelope)
            except Exception as e:
                logger.critical(f"Failed to publish event to Dead Letter Queue '{dlq_topic}': {e}")
        else:
            logger.critical(f"No Kafka Producer Manager associated with consumer to route to DLQ: {dlq_payload}")
