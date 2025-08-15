"""
RabbitMQ Connection Manager for ScholarAI

Handles connection management, queue setup, and message routing for
the ScholarAI messaging system.
"""

import asyncio
import logging
from typing import Optional, Dict, Any
from aio_pika import connect_robust, Message, ExchangeType, Queue, Connection, Channel
from app.core.config import settings

logger = logging.getLogger(__name__)


class RabbitMQConnection:
    """
    Manages RabbitMQ connections, exchanges, and queues for ScholarAI.
    
    Handles connection lifecycle, queue setup, and provides interfaces
    for message publishing and consumption.
    """

    def __init__(self):
        # Use settings from core config
        pass
        
        # Connection state
        self.connection: Optional[Connection] = None
        self.channel: Optional[Channel] = None
        
        # Queues and exchanges
        self.websearch_queue: Optional[Queue] = None
        self.websearch_exchange = None
        
        # Connection status
        self.is_connected = False
        self.is_setup = False

    async def connect(self) -> bool:
        """
        Establish connection to RabbitMQ server.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            logger.info(f"🔗 Connecting to RabbitMQ at {settings.rabbitmq_host}:{settings.rabbitmq_port}")
            
            # Build connection URL
            connection_url = (
                f"amqp://{settings.rabbitmq_user}:{settings.rabbitmq_password}"
                f"@{settings.rabbitmq_host}:{settings.rabbitmq_port}{settings.rabbitmq_vhost}"
            )
            
            # Establish connection
            self.connection = await connect_robust(connection_url)
            self.channel = await self.connection.channel()
            
            self.is_connected = True
            logger.info("✅ RabbitMQ connection established")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to RabbitMQ: {str(e)}")
            self.is_connected = False
            return False

    async def setup_queues(self) -> bool:
        """
        Setup exchanges and queues for ScholarAI messaging.
        
        Returns:
            bool: True if setup successful, False otherwise
        """
        if not self.is_connected or not self.channel:
            logger.error("❌ Cannot setup queues: not connected to RabbitMQ")
            return False
            
        try:
            logger.info("🛠️ Setting up RabbitMQ exchanges and queues...")
            
            # Declare exchange
            self.websearch_exchange = await self.channel.declare_exchange(
                "scholarai.exchange",
                ExchangeType.TOPIC,
                durable=True
            )
            
            # Declare websearch queue
            self.websearch_queue = await self.channel.declare_queue(
                "scholarai.websearch.queue",
                durable=True,
                arguments={
                    "x-message-ttl": 300000,  # 5 minutes TTL
                    "x-max-length": 1000,     # Max 1000 messages
                }
            )
            
            # Bind queue to exchange
            await self.websearch_queue.bind(
                self.websearch_exchange,
                routing_key="scholarai.websearch"
            )
            
            self.is_setup = True
            logger.info("✅ RabbitMQ queues and exchanges setup complete")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to setup queues: {str(e)}")
            self.is_setup = False
            return False

    async def publish_message(
        self, 
        routing_key: str, 
        message_data: Dict[str, Any],
        exchange_name: Optional[str] = None
    ) -> bool:
        """
        Publish a message to RabbitMQ.
        
        Args:
            routing_key: Message routing key
            message_data: Message data to publish
            exchange_name: Exchange name (uses default if not specified)
            
        Returns:
            bool: True if message published successfully
        """
        if not self.is_connected or not self.channel:
            logger.error("❌ Cannot publish message: not connected to RabbitMQ")
            return False
            
        try:
            import json
            
            # Serialize message
            message_body = json.dumps(message_data).encode()
            
            # Create message
            message = Message(
                body=message_body,
                delivery_mode=2,  # Persistent
                content_type="application/json"
            )
            
            # Get exchange
            exchange = self.websearch_exchange
            if exchange_name:
                exchange = await self.channel.get_exchange(exchange_name)
            
            # Publish message
            await exchange.publish(message, routing_key=routing_key)
            
            logger.debug(f"📤 Message published to {routing_key}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to publish message: {str(e)}")
            return False

    async def publish_websearch_result(self, result: Dict[str, Any]) -> bool:
        """
        Publish websearch result to the result queue.
        
        Args:
            result: Websearch result data
            
        Returns:
            bool: True if result published successfully
        """
        return await self.publish_message(
            routing_key="scholarai.websearch.completed",
            message_data=result
        )

    def get_websearch_queue(self) -> Optional[Queue]:
        """Get the websearch queue instance."""
        return self.websearch_queue

    def get_extraction_queue(self) -> Optional[Queue]:
        """Get the extraction queue instance (for compatibility)."""
        return None  # Not implemented in paper-search

    def get_structuring_queue(self) -> Optional[Queue]:
        """Get the structuring queue instance (for compatibility)."""
        return None  # Not implemented in paper-search

    async def close(self):
        """Close RabbitMQ connection and cleanup resources."""
        try:
            if self.channel:
                await self.channel.close()
            if self.connection:
                await self.connection.close()
                
            self.is_connected = False
            self.is_setup = False
            logger.info("🔒 RabbitMQ connection closed")
            
        except Exception as e:
            logger.error(f"❌ Error closing RabbitMQ connection: {str(e)}")

    def is_healthy(self) -> bool:
        """Check if the connection is healthy."""
        return self.is_connected and self.is_setup
