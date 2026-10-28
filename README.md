# Bot Berita Finansial

Bot Telegram buat pantau berita crypto, saham global, dan IHSG.

## Fitur

- 15 media tepercaya (Reuters, Bloomberg, Kontan, dll)
- Analisis AI via Groq (translate ke Indonesia + ringkas + "kenapa penting")
- Push terjadwal 4x sehari: 06:00, 16:00, 19:00, 04:00 WIB
- Alert pergerakan crypto >5% dalam 1 jam
- Command manual: /now, /btc, /ihsg, /msci, /flow, /pause, /resume, /status, /backup
- Backup history ke GitHub Gist
- Deteksi duplikat (gak kirim berita sama 2x)
- Notif error otomatis ke Telegram

## Setup

### 1. Install dependencies
```bash
bash setup.sh
