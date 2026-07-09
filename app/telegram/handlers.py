from app.database.core import AsyncSessionLocal
from app.services.account import AccountService
from app.telegram import auth, genai_agent
from app.telegram.client import TelegramClient
from app.telegram.schemas import Update

_account_service = AccountService()
_telegram_client = TelegramClient()

START_MESSAGE = (
    "MoneyWatcher bot ready.\n"
    "/balance <provider> <amount> — set an account's balance directly.\n"
    "Anything else — chat about your spending and balances."
)


async def dispatch_update(update: Update) -> None:
    """Route an authorized Telegram update to the right handler. Always replies via Telegram, never raises."""
    message = update.message
    if message is None or message.text is None:
        return

    chat_id = message.chat.id
    if not auth.is_authorized(chat_id):
        return

    text = message.text.strip()
    try:
        if text == "/start":
            reply = START_MESSAGE
        elif text.startswith("/balance"):
            reply = await _handle_balance(text)
        else:
            reply = await genai_agent.chat(chat_id, text)
    except Exception as e:
        reply = f"Something went wrong: {e}"

    await _telegram_client.send_message(chat_id, reply)


async def _handle_balance(text: str) -> str:
    """Parse '/balance <provider> <amount>' and update the account balance directly (no AI)."""
    parts = text.split()
    async with AsyncSessionLocal() as db:
        accounts = await _account_service.get_all_accounts(db)
        known_providers = sorted({a.provider for a in accounts})

        if len(parts) != 3:
            return f"Usage: /balance <provider> <amount>. Known providers: {', '.join(known_providers) or 'none yet'}"

        _, provider, amount_str = parts
        try:
            amount = float(amount_str)
        except ValueError:
            return f"'{amount_str}' isn't a valid amount."

        account = await _account_service.get_account(db, provider=provider)
        if account is None:
            return f"Unknown provider '{provider}'. Known providers: {', '.join(known_providers) or 'none yet'}"

        updated = await _account_service.update_balance_account(db, account.id, amount)
        return f"{updated.provider} balance set to {updated.balance:.2f}"
