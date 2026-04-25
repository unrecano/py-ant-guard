from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class User(BaseModel):
    """Represents a Telegram user or bot."""

    model_config = ConfigDict(extra="ignore")

    id: int
    is_bot: bool
    first_name: str


class Chat(BaseModel):
    """Represents a Telegram chat."""

    model_config = ConfigDict(extra="ignore")

    id: int
    type: str


class Message(BaseModel):
    """Represents a Telegram message."""

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    message_id: int
    from_user: User | None = Field(default=None, alias="from")
    chat: Chat
    date: int
    text: str | None = None


class Update(BaseModel):
    """Represents an incoming update from Telegram."""

    model_config = ConfigDict(extra="ignore")

    update_id: int
    message: Message | None = None
