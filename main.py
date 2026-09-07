"""
Entry point: menjalankan dashboard web (FastAPI/uvicorn) dan worker Telegram
(Telethon) secara bersamaan dalam satu proses -- cocok untuk Railway (satu service).
"""

import os
import asyncio
import logging

import uvicorn

import db
from app import app
from telegram_worker import build_client, run_worker

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


async def run_web():
    port = int(os.environ.get("PORT", 8000))
    config = uvicorn.Config(app, host="0.0.0.0", port=port, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


async def main():
    await db.init_db()

    client = build_client()
    await client.start()

    await asyncio.gather(
        run_web(),
        run_worker(client),
    )


if __name__ == "__main__":
    asyncio.run(main())
