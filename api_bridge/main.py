import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api_bridge.routers import live_feed, ocr, scam_db, stats
from api_bridge.data.db_manager import init_db
from api_bridge.services.kafka_consumer_service import start_kafka_consumer, stop_kafka_consumer

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    start_kafka_consumer()
    yield
    # Shutdown
    stop_kafka_consumer()

app = FastAPI(
    title="InfoCheckID Dashboard API",
    description="REST API bridge between InfoCheckID data stores and the monitoring dashboard.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(stats.router, prefix="/api", tags=["stats"])
app.include_router(live_feed.router, prefix="/api", tags=["live-feed"])
app.include_router(scam_db.router, prefix="/api", tags=["scam-db"])
app.include_router(ocr.router, prefix="/api", tags=["ocr"])


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "infocheckid-dashboard-api"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api_bridge.main:app", host="0.0.0.0", port=8001, reload=True)
