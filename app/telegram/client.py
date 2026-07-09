import os

import httpx

TELEGRAM_API_BASE = "https://api.telegram.org"


class TelegramClient:
    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")

    async def send_message(self, chat_id: int, text: str) -> None:
        """Send a text message to a Telegram chat. Failures are caught and logged, never raised."""
        url = f"{TELEGRAM_API_BASE}/bot{self.bot_token}/sendMessage"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, json={"chat_id": chat_id, "text": text})
                resp.raise_for_status()
        except Exception as e:
            print(f"Telegram send_message failed (chat_id={chat_id}): {e}")
