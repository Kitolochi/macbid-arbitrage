# MacBid Arbitrage

A full-stack web app that monitors [MacBid](https://mac.bid) liquidation auctions, compares prices against resale platforms (eBay, Amazon), and alerts you when profitable arbitrage opportunities exist.

## How It Works

1. **Scrapes MacBid** — Playwright-based scraper extracts live auction data every 10 minutes
2. **Looks up resale prices** — Queries eBay Browse API and Keepa (Amazon) for comparable listings
3. **Calculates true profit** — Factors in MacBid's full cost structure and platform selling fees
4. **Alerts you** — Email notifications when opportunities exceed your profit/ROI thresholds

### Profit Formula

```
MacBid Total Cost = Winning Bid + 15% Buyer's Premium + $3.00 Lot Fee + Sales Tax

eBay Net Revenue   = Sell Price − 13.6% FVF − $0.40 per order − Shipping
Amazon Net Revenue = Sell Price − Category Referral Fee − FBA Fee − Shipping

Profit = Net Revenue − MacBid Total Cost
ROI %  = (Profit / MacBid Total Cost) × 100
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.12, FastAPI, SQLAlchemy (async) |
| **Scraping** | Playwright (MacBid), httpx (APIs) |
| **Task Queue** | Celery + Redis |
| **Database** | PostgreSQL |
| **Cache** | Redis |
| **Frontend** | Next.js 15, TanStack Table, Recharts, Tailwind CSS |
| **Real-time** | Server-Sent Events (SSE) |
| **Notifications** | Resend (email) |
| **Infrastructure** | Docker Compose |

## Architecture

```
Browser (Next.js Dashboard)
    │  REST API + SSE
FastAPI Backend
    │           │            │
PostgreSQL    Redis        Celery Workers
(data)        (cache)      (scraping tasks)
                               │
              ┌────────────────┼────────────────┐
              │                │                │
         Playwright       eBay Browse      Keepa API
         (MacBid)         API (free)       (Amazon)
```

## Screenshots

The dashboard includes:

- **Dashboard** — Summary cards, live SSE feed, top categories, recent opportunities
- **Opportunities** — Sortable/filterable table with ROI color coding (green >30%, yellow 15-30%, red <15%)
- **Opportunity Detail** — Price breakdown, cost charts, price history, comparable listings, direct links
- **Settings** — Alert threshold configuration (min profit, min ROI, watched categories)

## Getting Started

### Prerequisites

- Docker & Docker Compose
- Python 3.12+
- Node.js 20+

### 1. Clone and configure

```bash
git clone https://github.com/Kitolochi/macbid-arbitrage.git
cd macbid-arbitrage
cp backend/.env.example backend/.env
```

Edit `backend/.env` with your API keys:

```env
EBAY_CLIENT_ID=your_ebay_client_id
EBAY_CLIENT_SECRET=your_ebay_client_secret
KEEPA_API_KEY=your_keepa_key
RESEND_API_KEY=your_resend_key
```

### 2. Start databases

```bash
docker compose up -d postgres redis
```

### 3. Set up the backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
playwright install chromium

# Run database migrations
alembic revision --autogenerate -m "initial"
alembic upgrade head

# Start the API server
uvicorn app.main:app --reload
```

### 4. Start Celery workers

In separate terminals:

```bash
# Worker (processes tasks)
celery -A app.celery_config worker --loglevel=info

# Beat (schedules periodic tasks)
celery -A app.celery_config beat --loglevel=info
```

### 5. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:3000** to view the dashboard.

### Alternative: Run everything with Docker

```bash
docker compose up --build
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/opportunities` | List opportunities (sort, filter, paginate) |
| `GET` | `/api/opportunities/{id}` | Opportunity detail with price breakdown |
| `GET` | `/api/listings` | Current MacBid listings |
| `GET` | `/api/products/{id}/prices` | Price history across platforms |
| `GET` | `/api/dashboard/stats` | Summary metrics |
| `GET` | `/api/stream` | SSE endpoint for real-time updates |
| `POST` | `/api/alerts/settings` | Create alert preferences |
| `GET` | `/api/alerts/settings` | List alert settings |
| `PUT` | `/api/alerts/settings/{id}` | Update alert preferences |

API docs available at **http://localhost:8000/docs** (Swagger UI).

## External Accounts Needed

| Service | Cost | Purpose |
|---------|------|---------|
| [eBay Developer](https://developer.ebay.com) | Free | Browse API for eBay prices |
| [Keepa](https://keepa.com) | ~€19/month | Amazon price history, BSR, offers |
| [Resend](https://resend.com) | Free tier (3k emails/mo) | Email alert notifications |
| [MacBid](https://mac.bid) | Free | Account for authenticated scraping (if needed) |

## Project Structure

```
arbitrage-app/
├── backend/
│   ├── app/
│   │   ├── api/            # FastAPI routes and Pydantic schemas
│   │   ├── integrations/   # eBay and Keepa API clients
│   │   ├── models/         # SQLAlchemy models
│   │   ├── scrapers/       # Playwright MacBid scraper
│   │   ├── services/       # Profit calculator, opportunity engine
│   │   ├── tasks/          # Celery tasks (scrape, lookup, calculate, alerts)
│   │   ├── main.py         # FastAPI app entry point
│   │   └── config.py       # Settings from environment variables
│   ├── alembic/            # Database migrations
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/            # Next.js pages (dashboard, opportunities, settings)
│   │   ├── components/     # Sidebar navigation
│   │   └── lib/            # API client, utility functions
│   ├── package.json
│   └── tailwind.config.ts
└── docker-compose.yml
```

## License

MIT
