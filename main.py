import logging
from contextlib import asynccontextmanager

import asyncio

from fastapi import FastAPI

from api.router import router

from sync.sync_worker import run_sync

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def sync_loop():
    while True:
        try:
            await run_sync()
        except Exception as e:
            logger.exception("Sync failed: %s", e)
        await asyncio.sleep(24 * 60 * 60)


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(sync_loop())

    yield

    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


app = FastAPI(title="Events Aggregator", lifespan=lifespan)
app.include_router(router, prefix="/api")
