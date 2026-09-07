"""
JALANKAN INI DI LAPTOP/KOMPUTERMU SENDIRI, SATU KALI SAJA -- bukan di Railway.

Tujuannya: login interaktif ke akun Telegram pribadimu (masukkan nomor + kode OTP),
lalu menghasilkan "session string". String ini nanti kamu paste ke Railway Variables
sebagai TELEGRAM_SESSION, supaya di Railway tidak perlu login interaktif lagi.

Cara pakai:
    pip install telethon
    python generate_session.py
"""

from telethon.sync import TelegramClient
from telethon.sessions import StringSession

print("=== Setup Session Telegram ===")
api_id = int(input("Masukkan API_ID (dari my.telegram.org): ").strip())
api_hash = input("Masukkan API_HASH (dari my.telegram.org): ").strip()

with TelegramClient(StringSession(), api_id, api_hash) as client:
    session_string = client.session.save()
    print("\n✅ Berhasil login!")
    print("\nSalin string di bawah ini, lalu paste ke Railway Variables dengan nama TELEGRAM_SESSION:\n")
    print(session_string)
    print("\n⚠️  Jangan bagikan string ini ke siapa pun -- ini setara akses penuh ke akun Telegrammu.")
