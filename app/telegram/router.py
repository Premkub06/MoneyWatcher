from fastapi import APIRouter, BackgroundTasks

from app.telegram.handlers import dispatch_update
from app.telegram.schemas import Update

router = APIRouter()


@router.post("/webhook")
async def telegram_webhook(update: Update, background_tasks: BackgroundTasks):
    """Receive a Telegram update. Always returns 200 immediately to avoid Telegram retry storms."""
    background_tasks.add_task(dispatch_update, update)
    return {"status": "ok"}
