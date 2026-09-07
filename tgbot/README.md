# Balas Otomatis — AI Auto-Responder untuk Telegram Pribadi

Userbot Telegram (bukan bot @BotFather) yang membalas DM masuk secara otomatis
memakai **Google Gemini (gratis)**, lengkap dengan dashboard web modern untuk
memantau percakapan dan mengatur kepribadian bot — semuanya bisa diatur dari
browser, tanpa perlu export manual di terminal setiap kali jalan.

> 💡 Pakai Gemini karena gratis (free tier tanpa kartu kredit) dan cukup pintar
> untuk balas chat natural. Kalau nanti butuh kualitas lebih tinggi, tinggal
> ganti ke Claude/model lain — lihat bagian "Ganti model AI" di bawah.

## ⚠️ Sebelum mulai
- Ini login pakai akun Telegram **pribadimu**. Pakai secukupnya untuk membalas DM personal —
  jangan untuk broadcast/spam massal, karena berisiko akunmu dibatasi Telegram.
- `TELEGRAM_SESSION` setara akses penuh ke akun Telegrammu. Jangan pernah dibagikan
  atau di-commit ke repo publik.

## Bagian mana yang pakai "env" dan mana yang tidak
Hanya **4 kredensial rahasia** yang perlu diisi sekali di panel **Variables** Railway
(diisi lewat dashboard Railway, bukan diketik manual di terminal):
`TELEGRAM_API_ID`, `TELEGRAM_API_HASH`, `TELEGRAM_SESSION`, `GEMINI_API_KEY`.

Semua pengaturan lain — kepribadian AI, kecepatan balas, aktif/nonaktif — **diatur
langsung dari dashboard web** yang otomatis muncul begitu bot dijalankan, dan
tersimpan otomatis di database, tanpa perlu redeploy.

## 1. Ambil kredensial Telegram
1. Buka https://my.telegram.org → login dengan nomor Telegrammu.
2. "API development tools" → buat aplikasi baru → catat `api_id` dan `api_hash`.

## 2. Generate session (sekali saja, di laptop sendiri)
```bash
pip install telethon
python generate_session.py
```
Ikuti instruksi (masukkan `api_id`, `api_hash`, nomor HP, lalu kode OTP yang masuk
ke Telegram). Di akhir akan muncul sebuah string panjang — itu `TELEGRAM_SESSION`.

## 3. Ambil API key Gemini (gratis)
1. Buka https://aistudio.google.com/apikey (login pakai akun Google, tidak perlu kartu kredit).
2. Klik "Create API key" → catat key-nya.

Catatan: free tier Gemini punya batas (sekitar 15 request/menit, ~1.500/hari untuk
model `gemini-1.5-flash`). Untuk auto-reply personal ini biasanya lebih dari cukup.
Kalau suatu saat kena limit terus-menerus, tinggal aktifkan billing di Google AI
Studio untuk naik tier, atau lihat bagian "Ganti model AI" di bawah.

## 4. Deploy ke Railway
1. Push folder ini ke repo GitHub (atau upload langsung lewat Railway CLI).
2. Di Railway: **New Project → Deploy from GitHub repo**, pilih repo ini.
3. Buka tab **Variables**, tambahkan 4 variabel:
   - `TELEGRAM_API_ID`
   - `TELEGRAM_API_HASH`
   - `TELEGRAM_SESSION`
   - `GEMINI_API_KEY`
4. Railway otomatis mendeteksi `Procfile`/`railway.json` dan menjalankan `python main.py`.
5. Setelah deploy sukses, buka domain publik yang diberikan Railway (tab **Settings → Networking → Generate Domain**) — dashboardnya langsung tampil di situ.

## 5. Pakai dashboardnya
Begitu dashboard terbuka di browser:
- **Saklar Aktif/Nonaktif** di sidebar: matikan sementara kalau kamu mau balas manual sendiri.
- **Statistik**: jumlah pesan 24 jam terakhir & jumlah kontak yang menghubungi.
- **Feed percakapan**: transkrip real-time (update tiap ±3 detik), bubble abu-abu = pesan masuk, bubble ungu = balasan AI.
- **"Atur Kepribadian AI"**: buka panel untuk mengubah gaya bahasa/instruksi bot, serta jeda balas minimum & maksimum (biar terasa natural, tidak instan seperti robot).

## Struktur proyek
```
main.py               # entry point: jalankan web + worker bersamaan
app.py                 # dashboard FastAPI (routes & API)
telegram_worker.py      # logika userbot Telethon + panggilan Claude
db.py                   # penyimpanan SQLite (config & log pesan)
generate_session.py     # script sekali-jalan untuk login (lokal, bukan Railway)
templates/dashboard.html
static/style.css
requirements.txt
Procfile / railway.json
```

## Ganti model AI
Model diatur di `telegram_worker.py`, variabel `GEMINI_MODEL`:
- `gemini-1.5-flash` (default) — limit harian free tier paling longgar, cocok untuk personal.
- `gemini-2.5-flash` — kualitas jawaban sedikit lebih baik, tapi limit hariannya lebih ketat.

Kalau nanti mau pindah ke model berbayar (misalnya Claude, untuk kualitas lebih tinggi),
cukup ganti isi fungsi `_generate_reply()` di `telegram_worker.py` untuk memanggil API
lain, dan sesuaikan `requirements.txt` + variabel API key-nya.

## Catatan
- Data (SQLite) tersimpan di disk container Railway — bertahan selama service aktif,
  namun bisa reset saat redeploy kecuali kamu menambahkan [Railway Volume](https://docs.railway.app/reference/volumes)
  untuk penyimpanan permanen.
- Untuk mengubah batasan topik (misalnya "jangan pernah bahas harga/rekening"),
  cukup tulis aturan itu di kotak "Atur Kepribadian AI" — tidak perlu ubah kode.
