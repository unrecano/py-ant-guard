from __future__ import annotations

import asyncio
import logging
import os
import signal
import sys
from typing import Any

from motor.motor_asyncio import AsyncIOMotorClient

from .client import TelegramClient
from .middleware import verify_user

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def main() -> None:
    # 1. DB Initialization
    mongo_uri = os.getenv("MONGO_URI", "mongodb://mongodb:27017")
    db_client: AsyncIOMotorClient[Any] = AsyncIOMotorClient(mongo_uri)
    try:
        await db_client.admin.command("ping")
        logger.info("Bot successfully connected to MongoDB.")
    except Exception as e:
        logger.error("Failed to connect to MongoDB: %s", e)
        db_client.close()
        sys.exit(1)

    # 2. Telegram Bot Initialization
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        logger.error("TELEGRAM_TOKEN environment variable is not set.")
        db_client.close()
        sys.exit(1)

    offset: int | None = None

    # Handle graceful shutdown (simplistic approach for docker/sigint)
    shutdown_event = asyncio.Event()

    def handle_shutdown() -> None:
        logger.info("Received shutdown signal. Shutting down gracefully...")
        shutdown_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, handle_shutdown)

    logger.info("Starting Telegram Bot long-polling loop...")

    async with TelegramClient(token) as bot_client:
        while not shutdown_event.is_set():
            try:
                # Polling for updates
                updates = await bot_client.get_updates(offset=offset, timeout=30)
                for update in updates:
                    offset = update.update_id + 1

                    if verify_user(update):
                        if update.message and update.message.text:
                            logger.info(
                                "Received valid message: %s", update.message.text
                            )
                            # Provide basic feedback
                            await bot_client.send_message(
                                chat_id=update.message.chat.id,
                                text=f"Echo: {update.message.text}",
                            )
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception("Unexpected error in polling loop: %s", e)
                await asyncio.sleep(5)  # Backoff on unexpected errors

    # Cleanup
    logger.info("Closing MongoDB connection.")
    db_client.close()
    logger.info("Bot shutdown complete.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
