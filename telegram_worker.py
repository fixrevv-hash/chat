"""
Worker userbot Telegram: login ke akun pribadi, dengarkan DM masuk,
balas otomatis pakai Gemini API dengan gaya senatural mungkin.
"""

import os
import random
import asyncio
import logging
from datetime import datetime, timedelta

from telethon import TelegramClient, events
from telethon.sessions import StringSession
from google import genai
from google.genai import types

import db

logger = logging.getLogger("telegram_worker")

HISTORY_TTL_MINUTES = 60
MAX_HISTORY_MESSAGES = 12

# Model gratis Gemini. "gemini-1.5-flash" dipilih karena limit harian free tier-nya
# paling longgar (cocok untuk auto-reply personal). Bisa diganti "gemini-2.5-flash"
# di bawah kalau mau kualitas sedikit lebih tinggi (limit hariannya lebih ketat).
GEMINI_MODEL = "gemini-3.6-flash"

# Riwayat percakapan sementara di memori (per user_id), format Gemini: role "user"/"model"
chat_history: dict[int, list[dict]] = {}

gemini_client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])


def _get_history(user_id: int) -> list[dict]:
    now = datetime.now()
    history = chat_history.get(user_id, [])
    history = [h for h in history if now - h["time"] < timedelta(minutes=HISTORY_TTL_MINUTES)]
    chat_history[user_id] = history
    return history


def _add_history(user_id: int, role: str, content: str):
    chat_history.setdefault(user_id, []).append(
        {"role": role, "content": content, "time": datetime.now()}
    )
    chat_history[user_id] = chat_history[user_id][-MAX_HISTORY_MESSAGES:]


def _generate_reply(user_id: int, incoming_text: str, persona: str) -> str:
    history = _get_history(user_id)
    # Format riwayat sesuai skema Gemini: role "user" / "model", isi dalam list "parts"
    gemini_history = [
        types.Content(role=h["role"], parts=[types.Part(text=h["content"])])
        for h in history
    ]

    chat = gemini_client.chats.create(
        model=GEMINI_MODEL,
        history=gemini_history,
        config=types.GenerateContentConfig(
            system_instruction=persona,
            max_output_tokens=500,
        ),
    )
    response = chat.send_message(incoming_text)
    return response.text.strip()


def _human_delay(reply_text: str, delay_min: float, delay_max: float) -> float:
    # Simulasi kecepatan mengetik manusia: lebih panjang balasan, sedikit lebih lama
    base = random.uniform(delay_min, delay_max)
    length_factor = min(len(reply_text) / 200, 1.5)
    return base + length_factor


def build_client() -> TelegramClient:
    api_id = int(os.environ["TELEGRAM_API_ID"])
    api_hash = os.environ["TELEGRAM_API_HASH"]
    session_string = os.environ.get("TELEGRAM_SESSION", "")
    return TelegramClient(StringSession(session_string), api_id, api_hash)


async def run_worker(client: TelegramClient):
    @client.on(events.NewMessage(incoming=True))
    async def handle_new_message(event):
        if not event.is_private:
            return

        config = await db.get_config()
        if config.get("active", "true") != "true":
            return  # bot sedang dinonaktifkan lewat dashboard

        sender = await event.get_sender()
        if sender is None or getattr(sender, "bot", False):
            return

        user_id = sender.id
        contact_name = (getattr(sender, "first_name", "") or "").strip() or f"User {user_id}"
        incoming_text = event.raw_text or ""
        if not incoming_text.strip():
            return

        await db.log_message(user_id, contact_name, "in", incoming_text)
        logger.info(f"Pesan masuk dari {contact_name}: {incoming_text[:50]!r}")

        try:
            await client.send_read_acknowledge(event.chat_id)

            persona = config.get("persona", "")
            delay_min = float(config.get("reply_delay_min", 2))
            delay_max = float(config.get("reply_delay_max", 5))

            async with client.action(event.chat_id, "typing"):
                reply_text = _generate_reply(user_id, incoming_text, persona)
                _add_history(user_id, "user", incoming_text)
                _add_history(user_id, "model", reply_text)
                await asyncio.sleep(_human_delay(reply_text, delay_min, delay_max))

            await event.reply(reply_text)
            await db.log_message(user_id, contact_name, "out", reply_text)
            logger.info(f"Balasan terkirim ke {contact_name}: {reply_text[:50]!r}")

        except Exception as e:
            logger.error(f"Gagal membalas {contact_name}: {e}")

    logger.info("Userbot aktif, menunggu pesan masuk...")
    await client.run_until_disconnected()
