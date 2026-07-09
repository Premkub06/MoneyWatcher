"""
One-off script: register this app's Telegram webhook URL with Telegram.
Usage: python scripts/set_webhook.py https://your-deployed-app.com
"""

import os
import sys

import httpx
from dotenv import load_dotenv

load_dotenv()


def main():
    if len(sys.argv) != 2:
        print("Usage: python scripts/set_webhook.py <base_url>")
        sys.exit(1)

    base_url = sys.argv[1].rstrip("/")
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    if not bot_token:
        print("TELEGRAM_BOT_TOKEN not set")
        sys.exit(1)

    webhook_url = f"{base_url}/api/v1/telegram/webhook"
    resp = httpx.post(
        f"https://api.telegram.org/bot{bot_token}/setWebhook",
        json={"url": webhook_url},
    )
    print(resp.status_code, resp.json())


if __name__ == "__main__":
    main()
