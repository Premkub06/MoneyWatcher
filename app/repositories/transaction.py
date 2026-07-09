from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.base import Category, Transaction


class TransactionRepo:
    async def create_transaction(self, db: AsyncSession, data: Transaction):
        """Insert a transaction into DB."""
        db.add(data)
        await db.commit()
        return data

    async def get_recent(
        self, db: AsyncSession, since: datetime, category_name: str | None = None
    ) -> list[Transaction]:
        """List transactions created since `since`, newest first, with category/account eager-loaded."""
        stmt = (
            select(Transaction)
            .options(selectinload(Transaction.category), selectinload(Transaction.account))
            .where(Transaction.created_at >= since)
            .order_by(Transaction.created_at.desc())
        )
        if category_name:
            stmt = stmt.join(Transaction.category).where(Category.name == category_name)
        result = await db.execute(stmt)
        return list(result.scalars().all())
