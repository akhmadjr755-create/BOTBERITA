#!/data/data/com.termux/files/usr/bin/bash
# setup.sh - Install semua dependencies bot

echo "=== Setup Bot Berita ==="
echo ""

echo "[1/3] Update pip..."
pip install --upgrade pip

echo "[2/3] Install Python packages..."
pip install -r requirements.txt

echo "[3/3] Cek instalasi..."
python -c "import requests, feedparser, groq; print('OK - library utama terinstall')"

echo ""
echo "=== Setup selesai ==="
echo ""
echo "Langkah selanjutnya:"
echo "1. Pastikan config.py sudah diisi API Key"
echo "2. Test: python bot.py"
echo "3. Kalau jalan, setup autostart pakai cronie"
