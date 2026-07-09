from typing import Optional

from pydantic import BaseModel


class Chat(BaseModel):
    id: int


class Message(BaseModel):
    text: Optional[str] = None
    chat: Chat


class Update(BaseModel):
    """Telegram webhook update payload. Only the fields we use."""
    update_id: int
    message: Optional[Message] = None
