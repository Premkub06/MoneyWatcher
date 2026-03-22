import json
import re

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Transaction
from app.repositories.transaction import TransactionRepo
from app.services import category_cache as cache
from app.services.account import AccountService
from app.services.raw_data import RawDataService


class TransactionService:
    """Silver layer service — transforms raw data into transactions."""

    def __init__(self):
        self.repo = TransactionRepo()
        self.account_service = AccountService()
        self.raw_data_service = RawDataService()

    async def process_raw_data(self, db: AsyncSession, raw_data_id, category_name: str):
        """ETL: Bronze -> Silver. Parse raw notification, create account if needed, create transaction. Returns None if amount is 0."""
        raw = await self.raw_data_service.repo.get_by_id(db, raw_data_id)
        if raw is None:
            raise ValueError(f"Raw data {raw_data_id} not found")

        payload = json.loads(raw.raw_payload)
        text = payload.get("notification", "")

        # Parse provider
        provider_match = re.search(r"(Krungthai)", payload.get("title", ""), re.IGNORECASE)
        provider = provider_match.group(1) if provider_match else raw.source

        # Parse account number
        acc_match = re.search(r"บัญชี\s+(\w+)", text)
        account_number = acc_match.group(1) if acc_match else "unknown"

        # Parse amount — if 0 will not add (as per note.md)
        amount_match = re.search(r"(-?[\d,]+\.\d{2})\s+บาท", text)
        amount = float(amount_match.group(1).replace(",", "")) if amount_match else 0
        if amount == 0:
            return None  # note.md: if amount is 0 will not add

        # Ensure account exists
        account_data = await self.account_service.create_account_if_not_existed(
            db, provider=provider, account_number=account_number
        )

        # Get category (from cache — no DB query)
        category = cache.get_by_name(category_name)
        if category is None:
            raise ValueError(f"Category '{category_name}' not found")

        # Update balance
        await self.account_service.update_balance_account(
            db, account_data.id, account_data.balance + amount
        )

        # Create transaction
        note = payload.get("note")
        new_transaction = Transaction(
            account_id=account_data.id,
            category_id=category.id,
            amount=amount,
            bank_timestamp=str(payload.get("timestamp", "")),
            note=note,
        )
        return await self.create_transaction(db, new_transaction)

    async def process_webhook(self, db: AsyncSession, source: str, payload, category_name: str):
        """Full pipeline: save raw payload (Bronze) then process to transaction (Silver)."""
        raw = await self.raw_data_service.save_raw(db, source, payload)
        return await self.process_raw_data(db, raw.id, category_name)

    async def create_transaction(self, db: AsyncSession, transaction: Transaction):
        """Save a transaction to DB."""
        return await self.repo.create_transaction(db, transaction)
