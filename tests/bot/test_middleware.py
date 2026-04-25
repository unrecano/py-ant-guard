from __future__ import annotations

import os
from unittest.mock import patch

from bot.middleware import verify_user
from bot.models import Chat, Message, Update, User


def create_update(user_id: int) -> Update:
    """Helper to create a mocked Update with a specific user_id."""
    return Update(
        update_id=1,
        message=Message(
            message_id=1,
            chat=Chat(id=1, type="private"),
            date=123,
            text="hello",
            **{"from": User(id=user_id, is_bot=False, first_name="Test")},
        ),
    )


@patch.dict(os.environ, {"AUTHORIZED_USER_ID": "12345"})
def test_verify_user_authorized() -> None:
    """Test middleware allows authorized user."""
    update = create_update(12345)
    assert verify_user(update) is True


@patch.dict(os.environ, {"AUTHORIZED_USER_ID": "12345"})
def test_verify_user_unauthorized() -> None:
    """Test middleware blocks unauthorized user."""
    update = create_update(99999)
    assert verify_user(update) is False


@patch.dict(os.environ, {}, clear=True)
def test_verify_user_missing_env() -> None:
    """Test middleware blocks if env var is missing."""
    update = create_update(12345)
    assert verify_user(update) is False


@patch.dict(os.environ, {"AUTHORIZED_USER_ID": "not-an-int"})
def test_verify_user_invalid_env() -> None:
    """Test middleware blocks if env var is not an int."""
    update = create_update(12345)
    assert verify_user(update) is False


def test_verify_user_no_message() -> None:
    """Test middleware blocks if update has no message."""
    update = Update(update_id=1)
    assert verify_user(update) is False
