# BOTBERITA - Asisten Riset Finansial Otomatis

Bot Telegram berbasis Python yang berjalan secara otomatis (serverless) menggunakan GitHub Actions. Bot ini dirancang sebagai **Informan**, bukan pemberi sinyal beli/jual.

## 1. Arsitektur & Prinsip
Proyek ini dibangun dengan prinsip algoritma: **Sistematis, Terstruktur, Jelas, dan Nol Ambiguitas**.
- **Input:** RSS Feed (Bloomberg, CNBC, Kontan, dll) & API CoinGecko.
- **Proses:** Filter kata kunci -> Analisis AI (Groq) dengan output JSON ketat -> Skor Sentimen.
- **Output:** Format pesan Telegram yang baku, padat, dan berurutan.
- **Penyimpanan:** GitHub Gist (History & State) untuk mencegah pengiriman berita ganda.

## 2. Fitur Utama
1. **Push Berita Terjadwal:** Berita dikirim pada jam 04:00, 06:00, 12:00, 16:00, dan 19:00 WIB.
2. **Analisis Berkelanjutan (Konteks):** AI mendeteksi jika berita baru adalah lanjutan dari berita sebelumnya.
3. **Strict Output:** Analisis dampak (Crypto, Saham, IHSG) dibatasi maksimal 2 kalimat per poin. Tegas, tanpa basa-basi.
4. **Cek Fundamental Koin (`/cek`):** Menarik data CoinGecko + penjelasan AI (Latar belakang, Produk, Pro/Kontra).
5. **Alert Pergerakan Harga:** Notifikasi otomatis jika harga koin naik/turun drastis >5% dalam 1 jam.

## 3. Daftar Command Telegram
- `/now` : Memaksa bot mencari dan mengirim berita saat ini juga.
- `/cek [TICKER]` : Analisis fundamental koin (Contoh: `/cek BTC`).
- `/flow` : Menampilkan harga puluhan koin di watchlist.
- `/btc`, `/ihsg`, `/msci` : Mencari berita spesifik berdasarkan kata kunci.
- `/pause` & `/resume` : Menghentikan/menjalankan notifikasi.
- `/status` : Cek status bot dan jumlah berita tersimpan.

## 4. Struktur File
- `bot.py` : Logika utama (Nol Ambiguitas, Strict JSON).
- `config.py` : API Key, Watchlist, dan Kata Kunci.
- `.github/workflows/bot.yml` : Penjadwal (Cron).
- `requirements.txt` : Dependensi versi terkunci.

## 5. Cara Deploy (Untuk Developer)
1. Fork repositori ini.
2. Masuk ke **Settings > Secrets and variables > Actions**, lalu tambahkan:
   - `GROQ_API_KEY`
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
   - `GH_TOKEN` (Personal Access Token GitHub)
   - `GIST_ID` (ID Gist untuk database)
3. Lakukan commit. GitHub Actions akan berjalan otomatis sesuai jadwal.
