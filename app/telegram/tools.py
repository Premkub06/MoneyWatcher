"""
Read-only tool functions exposed to the Gemini chat agent.
Each opens its own DB session — tool calls happen outside the request's session scope.
"""

from google.genai import types

from app.database.core import AsyncSessionLocal
from app.services.account import AccountService
from app.services.category import CategoryService
from app.services.transaction import TransactionService

_account_service = AccountService()
_transaction_service = TransactionService()
_category_service = CategoryService()


async def get_balances() -> list[dict]:
    """Current balance of every account."""
    async with AsyncSessionLocal() as db:
        accounts = await _account_service.get_all_accounts(db)
        return [
            {"provider": a.provider, "account_number": a.account_number, "balance": a.balance}
            for a in accounts
        ]


async def list_transactions(days: int = 7, category: str | None = None) -> list[dict]:
    """Recent transactions, optionally filtered by category name."""
    async with AsyncSessionLocal() as db:
        return await _transaction_service.get_recent_transactions(db, days=days, category_name=category)


def get_categories() -> list[dict]:
    """All known transaction categories (from cache, no DB query)."""
    return [
        {"name": c.name, "display_name": c.display_name, "type": c.type.value}
        for c in _category_service.get_all_categories()
    ]


TOOL_DECLARATIONS = [
    types.Tool(
        function_declarations=[
            types.FunctionDeclaration(
                name="get_balances",
                description="Get the current balance of every account.",
                parameters_json_schema={"type": "object", "properties": {}},
            ),
            types.FunctionDeclaration(
                name="list_transactions",
                description="List recent transactions, optionally filtered by category name.",
                parameters_json_schema={
                    "type": "object",
                    "properties": {
                        "days": {
                            "type": "integer",
                            "description": "How many days back to look. Defaults to 7.",
                        },
                        "category": {
                            "type": "string",
                            "description": "Filter to this category name only. Omit for all categories.",
                        },
                    },
                },
            ),
            types.FunctionDeclaration(
                name="get_categories",
                description="List all known transaction categories.",
                parameters_json_schema={"type": "object", "properties": {}},
            ),
        ]
    )
]

TOOL_FUNCTIONS = {
    "get_balances": get_balances,
    "list_transactions": list_transactions,
    "get_categories": get_categories,
}
