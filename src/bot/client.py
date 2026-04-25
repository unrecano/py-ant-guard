from __future__ import annotations

import logging
from typing import Any

import httpx
from pydantic import ValidationError

from .models import Update

logger = logging.getLogger(__name__)


class TelegramClient:
    """Async client for Telegram Bot API."""

    def __init__(self, token: str) -> None:
        """Initialize the Telegram Client.

        Args:
            token: The Telegram bot token.
        """
        self.base_url = f"https://api.telegram.org/bot{token}"
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or initialize the underlying httpx.AsyncClient."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=35.0)
        return self._client

    async def aclose(self) -> None:
        """Close the underlying HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self) -> TelegramClient:
        """Enter the async context manager."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit the async context manager and close the client."""
        await self.aclose()

    async def get_updates(
        self, offset: int | None = None, timeout: int = 30
    ) -> list[Update]:
        """Fetch updates from Telegram using long polling.

        Args:
            offset: The first update to be returned.
            timeout: Timeout in seconds for long polling.

        Returns:
            A list of validated Update objects.
        """
        url = f"{self.base_url}/getUpdates"
        params = {"timeout": timeout}
        if offset is not None:
            params["offset"] = offset

        client = await self._get_client()

        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            if not data.get("ok"):
                logger.error("Telegram API returned error: %s", data)
                return []

            updates = []
            for item in data.get("result", []):
                try:
                    updates.append(Update.model_validate(item))
                except ValidationError as e:
                    logger.error("Validation error for update %s: %s", item, e)
            return updates

        except (httpx.ConnectError, httpx.ReadTimeout, httpx.HTTPError) as e:
            logger.error("Network error while fetching updates: %s", e)
            return []

    async def send_message(self, chat_id: int, text: str) -> None:
        """Send a message to a specific chat.

        Args:
            chat_id: The ID of the destination chat.
            text: The text message to send.
        """
        url = f"{self.base_url}/sendMessage"
        payload = {"chat_id": chat_id, "text": text}
        client = await self._get_client()

        try:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            if not data.get("ok"):
                logger.error("Telegram API returned error on send_message: %s", data)
        except (httpx.ConnectError, httpx.ReadTimeout, httpx.HTTPError) as e:
            logger.error("Network error while sending message: %s", e)
