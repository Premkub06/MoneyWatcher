# MoneyWatcher 💰

Personal automated expense tracker — captures Krungthai bank notifications via MacroDroid and records transactions through a webhook-based data pipeline.

**Built for personal use.** Not a general-purpose tool.

## How It Works

```
KTB Notification → MacroDroid → Webhook API → Bronze (raw) → Silver (cleaned) → Grafana
```

1. **MacroDroid** captures Krungthai bank notifications on Android
2. User selects a category from a dialog (fetched from API)
3. MacroDroid sends the data to the webhook
4. API stores the raw payload in the **Bronze layer** (`bronze.raw_data`)
5. ETL cleans the data and creates a **Silver layer** transaction (`public.transactions`)
6. **Grafana** reads from Silver tables for dashboards

## Tech Stack

- **Python 3.13** / FastAPI / Uvicorn
- **SQLAlchemy** (async) + asyncpg
- **Supabase** PostgreSQL (via pgbouncer)
- **Alembic** for migrations
- **MacroDroid** for Android notification capture
- **Grafana** for visualization

## Project Structure

```
MoneyWatcher/
├── main.py                          # FastAPI entry point
├── alembic.ini
├── requirements.txt
├── app/
│   ├── api/v1/
│   │   ├── webhook.py               # POST /krungthai, POST /process-raw
│   │   └── category.py              # GET / POST / DELETE categories
│   ├── database/
│   │   ├── core.py                  # Async engine & session
│   │   └── init_data.py             # Load category cache on startup
│   ├── models/
│   │   ├── base.py                  # RawData, Account, Category, Transaction
│   │   └── enums.py                 # CategoryType (INCOME, EXPENSE, OTHER)
│   ├── repositories/
│   │   ├── account.py
│   │   ├── category.py
│   │   ├── raw_data.py
│   │   └── transaction.py
│   ├── schemas/
│   │   └── webhook.py               # Pydantic models
│   └── services/
│       ├── account.py
│       ├── category.py
│       ├── category_cache.py        # In-memory cache (O(1) lookup)
│       ├── raw_data.py
│       └── transaction.py           # ETL: raw → cleaned transaction
├── migrations/
│   └── versions/                    # Alembic migrations + seed data
└── macrodroid/
    ├── MoneyWatcher_Noti.macro       # Macro 1 — notification capture
    └── MoneyWatcher_Selector.macro   # Macro 2 — category selection & webhook
```

## Database Schema

### Bronze Layer (`bronze` schema)

| Table | Columns |
|-------|---------|
| **raw_data** | id (UUID), source, raw_payload, is_processed, created_at, process_status |

### Silver Layer (`public` schema)

| Table | Columns |
|-------|---------|
| **categories** | id, name, display_name (with emoji), type (INCOME/EXPENSE/OTHER) |
| **accounts** | id, name, account_number, provider, balance, created_at |
| **transactions** | id, account_id, category_id, amount, bank_timestamp, note, created_at |

### Default Categories

| Name | Display | Type |
|------|---------|------|
| food | 🍕 food | EXPENSE |
| travel | 🚗 travel | EXPENSE |
| shopping | 🛒 shopping | EXPENSE |
| bill | 💡 bill | EXPENSE |
| transfer_in | 📥 transfer_in | INCOME |
| transfer_out | 📤 transfer_out | EXPENSE |
| other | 📝 other | OTHER |

## MacroDroid Setup

Import the two macro exports in [`macrodroid/`](macrodroid/) directly into MacroDroid — no need to build them from scratch.

**Important:** both macros share a global `webhook_url` variable (defaults to `http://localhost:8000`). It's only set in one place — the "set global variable" action in `MoneyWatcher_Noti.macro` — so just edit it there to point at wherever the API is actually reachable (e.g. your server's public URL or LAN IP); both macros pick up the change since it's a shared global variable.

### Macro 1 — `MoneyWatcher_Noti.macro` (Notification Capture)

- **Trigger**: Krungthai app notification
- **Action**: Create a persistent notification with amount info

### Macro 2 — `MoneyWatcher_Selector.macro` (Category Selection & Webhook)

- **Trigger**: Click the persistent notification
- **Actions**:
  1. Fetch categories from `GET /api/v1/categories`
  2. Show selection dialog (Food, Travel, Shopping, Bill, Transfer IN/OUT, Other)
  3. Send choice + notification data to `POST /api/v1/webhook/krungthai`

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/webhook/krungthai` | Receive MacroDroid webhook |
| `POST` | `/api/v1/webhook/process-raw` | Trigger ETL on raw data |
| `GET` | `/api/v1/categories` | List all categories (for MacroDroid selector) |
| `POST` | `/api/v1/categories` | Add a category |
| `DELETE` | `/api/v1/categories/{name}` | Remove a category |

## Setup

```bash
pip install -r requirements.txt

# create .env with DATABASE_URI
export DATABASE_URI=postgresql+asyncpg://user:pass@host:port/dbname
# if want to migration use your direct uri
export DATABASE_URI_DIRECT=postgresql+asyncpg://user:pass@host:port/dbname

alembic upgrade head
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```