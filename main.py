from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI

from app.api.v1 import category, webhook
from app.database.init_data import init_master_data
from app.telegram.router import router as telegram_router

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await init_master_data()
    except Exception as e:
        print(f"Init Data Failed: {e}")

    yield
    print("Shutting down...")


app = FastAPI(
    title="MoneyWatcher API",
    version="1.0.0",
    description="API for ingesting Krungthai NEXT notificaition via Macrodroid webhook.",
    lifespan=lifespan,
)

app.include_router(webhook.router, prefix="/api/v1/webhook", tags=["Webhook"])
app.include_router(category.router, prefix="/api/v1/categories", tags=["Categories"])
app.include_router(telegram_router, prefix="/api/v1/telegram", tags=["Telegram"])


@app.get("/")
def read_root():
    """Health check endpoint."""
    return {"message": "MoneyWatcher API is running"}
