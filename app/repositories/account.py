from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Account


class AccountRepo:
    async def get_account(
        self, db: AsyncSession, id=None, account_number=None, provider=None
    ):
        """Find an account by id, account_number, or provider."""
        stmt = select(Account)
        if id:
            stmt = stmt.where(Account.id == id)
        if account_number:
            stmt = stmt.where(Account.account_number == account_number)
        if provider:
            stmt = stmt.where(Account.provider == provider)
        result = await db.execute(stmt)
        existing_account = result.scalar_one_or_none()
        return existing_account

    async def create_or_update_account(self, db: AsyncSession, data: Account):
        """Insert or update an account in DB."""
        db.add(data)
        await db.commit()
        return data

    async def get_all(self, db: AsyncSession) -> list[Account]:
        """List all accounts."""
        stmt = select(Account)
        result = await db.execute(stmt)
        return list(result.scalars().all())