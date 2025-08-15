"""
🚀 REFACTORED RABBITMQ CONSUMER FOR SCHOLARAI PAPER SEARCH 🚀

This file now uses a clean, modular architecture with separate services for:
- Connection management
- Message handling
- Configuration management
- WebSearch orchestration

Maintains full backward compatibility while providing improved maintainability,
testability, and separation of concerns.
"""

import asyncio
import logging

from .messaging import ScholarAIConsumer, RabbitMQConnection
from .websearch import AppConfig

logger = logging.getLogger(__name__)


class RabbitMQConsumer:
    """
    🔄 Backward compatibility wrapper for the refactored consumer.

    Maintains the same public interface as the original consumer while
    using the new modular architecture under the hood.
    """

    def __init__(self):
        # Initialize with new modular consumer
        self.config = AppConfig.from_env()
        self.consumer = ScholarAIConsumer()

        # Expose legacy properties for backward compatibility
        self.connection = None
        self.channel = None
        self.websearch_agent = None

        # Legacy configuration properties - use settings from core config
        from app.core.config import settings
        self.rabbitmq_host = settings.rabbitmq_host
        self.rabbitmq_port = settings.rabbitmq_port
        self.rabbitmq_user = settings.rabbitmq_user
        self.rabbitmq_password = settings.rabbitmq_password
        self.websearch_queue = "scholarai.websearch.queue"
        self.exchange_name = "scholarai.exchange"

    async def connect(self):
        """🔗 Establish connection to RabbitMQ (legacy interface)"""
        connected = await self.consumer.connection_manager.connect()
        if connected:
            # Set legacy properties for backward compatibility
            self.connection = self.consumer.connection_manager.connection
            self.channel = self.consumer.connection_manager.channel
            print(
                f"✅ Connected to RabbitMQ at {self.rabbitmq_host}:{self.rabbitmq_port}"
            )
        else:
            print(f"❌ Failed to connect to RabbitMQ")
            raise Exception("Failed to connect to RabbitMQ")

    async def setup_queues(self):
        """🛠️ Setup exchanges and queues (legacy interface)"""
        success = await self.consumer.connection_manager.setup_queues()
        if success:
            print("✅ RabbitMQ websearch queue and bindings setup complete")
        else:
            print("❌ Failed to setup queues")
            raise Exception("Failed to setup queues")

    async def process_websearch_message(self, message):
        """📥 Process websearch request (legacy interface - not used in new architecture)"""
        # This method is maintained for compatibility but not used
        # The new architecture handles this automatically through handlers
        logger.warning(
            "Legacy process_websearch_message called - using new handler architecture"
        )
        await self.consumer._process_message(message)

    async def send_websearch_result(self, result):
        """📤 Send websearch result back (legacy interface - not used in new architecture)"""
        # This method is maintained for compatibility but not used
        # The new architecture handles this automatically
        logger.warning("Legacy send_websearch_result called - using new architecture")
        await self.consumer.connection_manager.publish_websearch_result(result)

    async def start_consuming(self):
        """🔄 Start consuming messages from websearch queue (main entry point)"""
        try:
            print("🚀 Starting RabbitMQ Consumer with modular architecture...")
            await self.consumer.start()
        except asyncio.CancelledError:
            print("🛑 Consumer task cancelled")
        except Exception as e:
            print(f"❌ Consumer error: {e}")
            raise

    async def close(self):
        """🔒 Close RabbitMQ connection"""
        await self.consumer.stop()


# Global consumer instance for backward compatibility
consumer = RabbitMQConsumer()


# Main entry point for running the consumer standalone
async def main():
    """Main entry point for running the consumer"""
    consumer_instance = RabbitMQConsumer()

    try:
        await consumer_instance.start_consuming()
    except KeyboardInterrupt:
        print("\n🛑 Received interrupt signal")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
    finally:
        await consumer_instance.close()
        print("👋 Consumer shutdown complete")


if __name__ == "__main__":
    # Allow running this file directly for testing
    print("🚀 Starting ScholarAI Paper Search RabbitMQ Consumer...")
    asyncio.run(main())
