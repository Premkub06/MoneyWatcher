from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Account
from app.repositories.account import AccountRepo


class AccountService:
    def __init__(self):
        self.repo = AccountRepo()

    async def get_account(
        self, db: AsyncSession, id=None, account_number=None, provider=None
    ):
        """Find an account by id, account_number, or provider."""
        return await self.repo.get_account(db, id, account_number, provider)

    async def create_or_update_account(self, db: AsyncSession, data: Account):
        """Create or update an account in DB."""
        return await self.repo.create_or_update_account(db, data)

    async def create_account_if_not_existed(
        self, db: AsyncSession, account_number: str, provider: str
    ):
        """Create an account if it doesn't exist, then return it."""
        is_account_existed = await self.get_account(
            db, account_number=account_number, provider=provider
        )
        if is_account_existed is None:
            account = Account(
                name=f"{provider} {account_number}",
                account_number=account_number,
                provider=provider,
            )
            await self.create_or_update_account(db, data=account)
        return await self.get_account(
            db, account_number=account_number, provider=provider
        )
    async def update_balance_account(self, db: AsyncSession, account_id: int, new_balance: float):
        """Update account balance."""
        account = await self.get_account(db, id=account_id)
        if account:
            account.balance = new_balance
            await self.create_or_update_account(db, data=account)
        return account

    async def get_all_accounts(self, db: AsyncSession) -> list[Account]:
        """List all accounts."""
        return await self.repo.get_all(db)