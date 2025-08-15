"""
Message Handlers for ScholarAI

Handles different types of messages and routes them to appropriate
processing logic.
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional
from aio_pika import IncomingMessage

from .base_handler import BaseMessageHandler
from ..websearch_agent import WebSearchAgent

logger = logging.getLogger(__name__)


class WebSearchMessageHandler(BaseMessageHandler):
    """
    Handles websearch messages and processes them using the WebSearchAgent.
    
    Responsible for:
    - Message validation
    - WebSearchAgent orchestration
    - Result publishing
    - Error handling
    """

    def __init__(self):
        super().__init__()
        self.websearch_agent = None
        self.connection_manager = None

    async def initialize(self, connection_manager):
        """Initialize the handler with connection manager."""
        self.connection_manager = connection_manager
        self.websearch_agent = WebSearchAgent()
        logger.info("✅ WebSearch message handler initialized")

    async def handle_message(self, message: IncomingMessage) -> bool:
        """
        Handle websearch message processing.
        
        Args:
            message: Incoming RabbitMQ message
            
        Returns:
            bool: True if message processed successfully
        """
        try:
            # Parse message
            message_data = await self._parse_message(message)
            if not message_data:
                return False
            
            # Validate message
            if not self._validate_websearch_message(message_data):
                logger.error("❌ Invalid websearch message format")
                await message.reject(requeue=False)
                return False
            
            logger.info(f"🔍 Processing websearch request: {message_data.get('correlationId', 'unknown')}")
            
            # Process websearch request
            result = await self.websearch_agent.process_request(message_data)
            
            # Publish result
            if self.connection_manager:
                success = await self.connection_manager.publish_websearch_result(result)
                if success:
                    logger.info(f"✅ Websearch result published for: {result.get('correlationId', 'unknown')}")
                else:
                    logger.error(f"❌ Failed to publish websearch result for: {result.get('correlationId', 'unknown')}")
            
            # Acknowledge message
            await message.ack()
            return True
            
        except Exception as e:
            logger.error(f"❌ Error processing websearch message: {str(e)}")
            # Don't requeue for code errors (like missing methods)
            # Only requeue for transient errors (network, temporary failures)
            should_requeue = not ("object has no attribute" in str(e) or "AttributeError" in str(e))
            await message.reject(requeue=should_requeue)
            return False

    def _validate_websearch_message(self, message_data: Dict[str, Any]) -> bool:
        """
        Validate websearch message format.
        
        Args:
            message_data: Parsed message data
            
        Returns:
            bool: True if message is valid
        """
        required_fields = ["projectId", "queryTerms"]
        
        for field in required_fields:
            if field not in message_data:
                logger.error(f"❌ Missing required field: {field}")
                return False
        
        # Validate query terms
        query_terms = message_data.get("queryTerms", [])
        if not isinstance(query_terms, list) or len(query_terms) == 0:
            logger.error("❌ queryTerms must be a non-empty list")
            return False
        
        return True

    async def _parse_message(self, message: IncomingMessage) -> Optional[Dict[str, Any]]:
        """
        Parse incoming message body.
        
        Args:
            message: Incoming RabbitMQ message
            
        Returns:
            Parsed message data or None if parsing failed
        """
        try:
            body = message.body.decode('utf-8')
            return json.loads(body)
        except (UnicodeDecodeError, json.JSONDecodeError) as e:
            logger.error(f"❌ Failed to parse message body: {str(e)}")
            return None


class MessageHandlerFactory:
    """
    Factory for creating and managing message handlers.
    
    Provides a centralized way to register and retrieve handlers
    for different message types.
    """

    def __init__(self):
        self.handlers: Dict[str, BaseMessageHandler] = {}
        self.default_handler: Optional[BaseMessageHandler] = None

    def register_handler(self, message_type: str, handler: BaseMessageHandler):
        """
        Register a handler for a specific message type.
        
        Args:
            message_type: Type of message the handler can process
            handler: Message handler instance
        """
        self.handlers[message_type] = handler
        logger.info(f"📝 Registered handler for message type: {message_type}")

    def set_default_handler(self, handler: BaseMessageHandler):
        """
        Set the default handler for unhandled message types.
        
        Args:
            handler: Default message handler
        """
        self.default_handler = handler
        logger.info("📝 Default message handler set")

    def get_handler(self, message_type: str) -> Optional[BaseMessageHandler]:
        """
        Get handler for a specific message type.
        
        Args:
            message_type: Type of message
            
        Returns:
            Message handler or default handler if not found
        """
        return self.handlers.get(message_type, self.default_handler)

    def get_all_handlers(self) -> Dict[str, BaseMessageHandler]:
        """Get all registered handlers."""
        return self.handlers.copy()
