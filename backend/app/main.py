from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.api.routes import router as api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    yield
    # Shutdown


settings = get_settings()

app = FastAPI(
    title="MacBid Arbitrage",
    description="Monitor MacBid auctions and find profitable resale opportunities",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "ok"}
