from __future__ import annotations

import json

import httpx
import pytest
import respx

from bot.client import TelegramClient


@pytest.mark.asyncio
async def test_get_updates_success() -> None:
    """Test get_updates correctly parses a valid response."""
    mock_response = {
        "ok": True,
        "result": [
            {
                "update_id": 123,
                "message": {
                    "message_id": 1,
                    "from": {"id": 999, "is_bot": False, "first_name": "Test"},
                    "chat": {"id": 999, "type": "private"},
                    "date": 1612345678,
                    "text": "hello",
                },
            }
        ],
    }

    with respx.mock:
        respx.get("https://api.telegram.org/botTOKEN/getUpdates").mock(
            return_value=httpx.Response(200, json=mock_response)
        )
        async with TelegramClient("TOKEN") as client:
            updates = await client.get_updates(offset=None)

            assert len(updates) == 1
            assert updates[0].update_id == 123
            assert updates[0].message is not None
            assert updates[0].message.text == "hello"


@pytest.mark.asyncio
async def test_get_updates_api_error() -> None:
    """Test get_updates handles ok: False responses gracefully."""
    mock_response = {"ok": False, "error_code": 401, "description": "Unauthorized"}

    with respx.mock:
        respx.get("https://api.telegram.org/botTOKEN/getUpdates").mock(
            return_value=httpx.Response(200, json=mock_response)
        )
        async with TelegramClient("TOKEN") as client:
            updates = await client.get_updates()
            assert updates == []


@pytest.mark.asyncio
async def test_get_updates_network_error() -> None:
    """Test get_updates catches network exceptions."""
    with respx.mock:
        respx.get("https://api.telegram.org/botTOKEN/getUpdates").mock(
            side_effect=httpx.ConnectError("Connection refused")
        )
        async with TelegramClient("TOKEN") as client:
            updates = await client.get_updates()
            assert updates == []


@pytest.mark.asyncio
async def test_get_updates_invalid_json() -> None:
    """Test get_updates ignores invalid items causing ValidationError."""
    mock_response = {
        "ok": True,
        "result": [
            {"update_id": 123},  # Valid (message is optional)
            {"message": {}},  # Invalid (missing update_id)
        ],
    }

    with respx.mock:
        respx.get("https://api.telegram.org/botTOKEN/getUpdates").mock(
            return_value=httpx.Response(200, json=mock_response)
        )
        async with TelegramClient("TOKEN") as client:
            updates = await client.get_updates()
            assert len(updates) == 1
            assert updates[0].update_id == 123


@pytest.mark.asyncio
async def test_send_message_success() -> None:
    """Test send_message posts correct payload."""
    with respx.mock:
        route = respx.post("https://api.telegram.org/botTOKEN/sendMessage").mock(
            return_value=httpx.Response(200, json={"ok": True})
        )
        async with TelegramClient("TOKEN") as client:
            await client.send_message(chat_id=123, text="Hi")

            assert route.called
            request = route.calls.last.request
            content = json.loads(request.content)
            assert content["chat_id"] == 123
            assert content["text"] == "Hi"


@pytest.mark.asyncio
async def test_send_message_network_error() -> None:
    """Test send_message handles network error."""
    with respx.mock:
        respx.post("https://api.telegram.org/botTOKEN/sendMessage").mock(
            side_effect=httpx.ReadTimeout("Timeout")
        )
        async with TelegramClient("TOKEN") as client:
            # Should not raise exception
            await client.send_message(chat_id=123, text="Hi")
