"""
Lapisan penyimpanan (SQLite) untuk:
- config: pengaturan yang bisa diubah dari dashboard (persona, status aktif/nonaktif, dll)
- messages: log percakapan untuk ditampilkan real-time di dashboard
Tidak butuh environment variable -- semua pengaturan "sehari-hari" hidup di sini.
"""

import aiosqlite
import time
import json

DB_PATH = "autoresponder.db"

DEFAULT_CONFIG = {
    "active": "true",
    "persona": (
        "Kamu adalah asisten pribadi yang membalas pesan Telegram atas nama pemilik akun. "
        "Balas dengan ramah, hangat, dan singkat seperti manusia sungguhan lagi mengetik -- "
        "bukan seperti robot formal. Boleh pakai bahasa santai sehari-hari. "
        "Kalau pertanyaannya butuh keputusan pribadi dari pemilik akun (harga, jadwal, hal sensitif), "
        "bilang bahwa pemilik akun akan membalas langsung nanti. Jangan mengarang jawaban. "
        "Kalau ditanya langsung apakah ini AI/bot, jujur akui bahwa ini asisten otomatis "
        "yang membantu merespons sementara pemilik akun belum sempat balas."
    ),
    "greeting_style": "santai",
    "reply_delay_min": "2",
    "reply_delay_max": "5",
}


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """CREATE TABLE IF NOT EXISTS config (
                key TEXT PRIMARY KEY,
                value TEXT
            )"""
        )
        await db.execute(
            """CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                contact_name TEXT,
                direction TEXT,      -- 'in' atau 'out'
                content TEXT,
                ts REAL
            )"""
        )
        for k, v in DEFAULT_CONFIG.items():
            await db.execute(
                "INSERT OR IGNORE INTO config (key, value) VALUES (?, ?)", (k, v)
            )
        await db.commit()


async def get_config() -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT key, value FROM config")
        rows = await cursor.fetchall()
        return {k: v for k, v in rows}


async def set_config(key: str, value: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO config (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, value),
        )
        await db.commit()


async def log_message(user_id: int, contact_name: str, direction: str, content: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO messages (user_id, contact_name, direction, content, ts) "
            "VALUES (?, ?, ?, ?, ?)",
            (user_id, contact_name, direction, content, time.time()),
        )
        await db.commit()


async def get_recent_messages(limit: int = 50) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM messages ORDER BY ts DESC LIMIT ?", (limit,)
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows][::-1]


async def get_stats() -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        today_start = time.time() - 24 * 3600
        cursor = await db.execute(
            "SELECT COUNT(*) FROM messages WHERE ts > ?", (today_start,)
        )
        msg_today = (await cursor.fetchone())[0]

        cursor = await db.execute("SELECT COUNT(DISTINCT user_id) FROM messages")
        total_contacts = (await cursor.fetchone())[0]

        cursor = await db.execute("SELECT MAX(ts) FROM messages")
        last_ts = (await cursor.fetchone())[0]

        return {
            "messages_today": msg_today,
            "active_contacts": total_contacts,
            "last_activity": last_ts,
        }
