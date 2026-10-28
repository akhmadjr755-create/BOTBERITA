# bot.py
# Bot Berita Finansial - Versi Final (Sistematis, Terstruktur, Nol Ambiguitas)
# Mode: GitHub Actions

import json
import time
import hashlib
import re
import traceback
from datetime import datetime, timezone, timedelta
from pathlib import Path

import requests
import feedparser
from groq import Groq

import config

# ==========================================
# 1. SETUP & UTILITY
# ==========================================
WIB = timezone(timedelta(hours=7))
groq_client = Groq(api_key=config.GROQ_API_KEY)

BASE_DIR = Path(__file__).parent
HISTORY_PATH = BASE_DIR / "news_history.json"
STATE_PATH = BASE_DIR / "bot_state.json"
PAUSE_PATH = BASE_DIR / "paused.flag"

def now_wib():
    return datetime.now(WIB)

def log(msg):
    print(f"[{now_wib().strftime('%Y-%m-%d %H:%M:%S')}] {msg}")

def load_json(path, default):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return default
    return default

def save_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def title_hash(title):
    return hashlib.md5(title.strip().lower().encode()).hexdigest()

def is_paused():
    return PAUSE_PATH.exists()

# ==========================================
# 2. TELEGRAM API
# ==========================================
def send_telegram(text, parse_mode="HTML"):
    # Batas maksimal Telegram 4096 karakter. Kita potong aman di 4000.
    if len(text) > 4000:
        text = text[:4000] + "\n\n... (dipotong)"
    
    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": config.TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": True,
    }
    try:
        r = requests.post(url, json=payload, timeout=30)
        if r.status_code != 200:
            log(f"Telegram error: {r.status_code} {r.text[:200]}")
            return False
        return True
    except Exception as e:
        log(f"Telegram exception: {e}")
        return False

def send_error(msg):
    send_telegram(f"<b>BOT ERROR</b>\n\n{msg[:3500]}")

# ==========================================
# 3. GIST BACKUP & SYNC
# ==========================================
def upload_to_gist():
    if not config.GITHUB_TOKEN or not config.GIST_ID:
        return
    try:
        history = load_json(HISTORY_PATH, [])
        state = load_json(STATE_PATH, {"last_runs": {}})
        combined_data = {"history": history[-1000:], "state": state}
        
        content = json.dumps(combined_data, ensure_ascii=False, indent=2)
        headers = {"Authorization": f"token {config.GITHUB_TOKEN}", "Accept": "application/vnd.github+json"}
        url = f"https://api.github.com/gists/{config.GIST_ID}"
        payload = {"files": {config.GIST_FILENAME: {"content": content}}}
        
        r = requests.patch(url, headers=headers, json=payload, timeout=30)
        if r.status_code == 200:
            log("Upload ke Gist sukses.")
        else:
            log(f"Upload Gist gagal: {r.status_code}")
    except Exception as e:
        log(f"Upload error: {e}")

def download_from_gist():
    if not config.GITHUB_TOKEN or not config.GIST_ID:
        return
    try:
        headers = {"Authorization": f"token {config.GITHUB_TOKEN}", "Accept": "application/vnd.github+json"}
        url = f"https://api.github.com/gists/{config.GIST_ID}"
        r = requests.get(url, headers=headers, timeout=30)
        
        if r.status_code == 200:
            files = r.json().get("files", {})
            if config.GIST_FILENAME in files:
                content_raw = files[config.GIST_FILENAME].get("content", "{}")
                try:
                    data = json.loads(content_raw)
                    save_json(HISTORY_PATH, data.get("history", []))
                    save_json(STATE_PATH, data.get("state", {"last_runs": {}}))
                    log("Download dari Gist sukses.")
                except json.JSONDecodeError:
                    log("Format Gist bukan JSON valid.")
        else:
            log(f"Download Gist gagal: {r.status_code}")
    except Exception as e:
        log(f"Download error: {e}")

# ==========================================
# 4. FETCH & FILTER BERITA
# ==========================================
def fetch_rss(url, source_name):
    items = []
    try:
        feed = feedparser.parse(url)
        for entry in feed.entries[:10]: # Batasi 10 teratas per sumber
            title = entry.get("title", "").strip()
            link = entry.get("link", "").strip()
            summary = entry.get("summary", "") or entry.get("description", "")
            if not title or not link:
                continue
            items.append({"source": source_name, "title": title, "link": link, "summary": summary})
    except Exception as e:
        log(f"RSS error {source_name}: {e}")
    return items

def is_relevant(item):
    text = (item["title"] + " " + item["summary"]).lower()
    for kw in config.KEYWORDS_GLOBAL + config.KEYWORDS_ID:
        if kw.lower() in text:
            return True
    return False

def collect_news():
    all_news = []
    for source_name, url in config.TRUSTED_SOURCES.items():
        items = fetch_rss(url, source_name)
        log(f"  {source_name}: {len(items)} item")
        all_news.extend(items)
    return all_news

def dedupe(news_list):
    history = load_json(HISTORY_PATH, [])
    seen_hashes = set(title_hash(h["title"]) for h in history if "title" in h)
    seen_links = set(h.get("link", "") for h in history)
    
    unique = []
    for item in news_list:
        h = title_hash(item["title"])
        if h in seen_hashes or item["link"] in seen_links:
            continue
        seen_hashes.add(h)
        seen_links.add(item["link"])
        unique.append(item)
    return unique

# ==========================================
# 5. AI ANALYSIS (GROQ - STRICT JSON MODE)
# ==========================================
def analyze_with_groq(item, previous_news=""):
    konteks = f"Konteks berita sebelumnya: {previous_news}\n" if previous_news else ""
    
    prompt = f"""Kamu adalah analis finansial profesional. Jawab HANYA dalam format JSON valid, tanpa teks pembuka/penutup.
{konteks}
Berita baru dari {item['source']}:
JUDUL: {item['title']}
ISI: {item['summary'][:1000]}

Tugasmu:
1. "konteks": Cek apakah berita ini ada kaitannya dengan "Konteks berita sebelumnya". Jika ada, jelaskan kaitannya (maks 1 kalimat). Jika tidak ada, tulis "Berita baru".
2. "crypto", "saham", "ihsg": Jelaskan dampaknya. MAKSIMAL 2 KALIMAT per poin. Harus to the point, tegas, langsung sebutkan alasannya.
3. "sentimen": Beri angka integer dari -100 (sangat buruk) sampai 100 (sangat baik).

Format JSON wajib:
{{
  "konteks": "...",
  "crypto": "...",
  "saham": "...",
  "ihsg": "...",
  "sentimen": 0
}}"""

    try:
        completion = groq_client.chat.completions.create(
            model=config.GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=400,
            response_format={"type": "json_object"} 
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        log(f"Groq error: {type(e).__name__}: {e}")
        return None

def analyze_coin_fundamental(coin_data):
    # (Sama seperti sebelumnya, tapi dipastikan tidak ada typo)
    desc = coin_data['desc'][:1000]
    if not desc:
        desc = "Tidak ada deskripsi di CoinGecko."

    prompt = f"""Kamu adalah analis crypto netral. Jelaskan secara OBJEKTIF koin {coin_data['name']} ({coin_data['symbol']}).
JANGAN memberikan saran beli/jual. HANYA berikan informasi.

Data dari CoinGecko:
Deskripsi: {desc}
Market Cap: ${coin_data['market_cap']:,.0f}
Volume 24j: ${coin_data['volume']:,.0f}

ATURAN:
1. Jawab pakai Bahasa Indonesia yang mudah dipahami.
2. Jangan pakai format bullet point. Pakai paragraf.
3. Jika data tidak ada, bilang "Informasi tidak ditemukan".
4. Struktur jawaban harus seperti ini:

LATAR BELAKANG:
(Jelaskan koin ini dibuat oleh siapa dan tujuannya apa)

MASALAH YANG DISELESAIKAN:
(Jelaskan masalah apa yang coba dipecahkan)

PRODUK / TEKNOLOGI:
(Apa yang sebenarnya dibuat?)

PRO & KONTRA (FAKTA):
(Sebutkan 1 fakta positif dan 1 red flag berdasarkan data di atas)."""

    try:
        completion = groq_client.chat.completions.create(
            model=config.GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=800
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        log(f"Groq Error coin analysis: {e}")
        return "Gagal menganalisis fundamental."

# ==========================================
# 6. FORMATTING MESSAGES (STRICT)
# ==========================================
def format_news_message(item, analysis):
    if not analysis:
        return f"<b>{item['source']} - {item['title']}</b>\n\nAnalisis tidak tersedia.\n\nLink: {item['link']}"

    try:
        data = json.loads(analysis)
        score = int(data.get("sentimen", 0))
        
        if score > 20:
            sent_status = f"🟢 Positif ({score})"
        elif score < -20:
            sent_status = f"🔴 Negatif ({score})"
        else:
            sent_status = f"⚪ Netral ({score})"
            
        return (
            f"<b>{item['source']} - {item['title']}</b>\n\n"
            f"<b>Konteks:</b> {data.get('konteks', 'Berita baru')}\n\n"
            f"<b>Dampak:</b>\n"
            f"• <b>Crypto:</b> {data.get('crypto', '-')}\n"
            f"• <b>Saham:</b> {data.get('saham', '-')}\n"
            f"• <b>IHSG:</b> {data.get('ihsg', '-')}\n\n"
            f"<b>{sent_status}</b>\n\n"
            f"Link: {item['link']}"
        )
    except Exception as e:
        log(f"Gagal parsing JSON: {e}")
        # Fallback jika JSON rusak
        return f"<b>{item['source']} - {item['title']}</b>\n\nAI gagal memformat teks. Silakan baca link.\n\nLink: {item['link']}"

# ==========================================
# 7. NEWS CYCLE
# ==========================================
def run_news_cycle(label="manual"):
    log(f"=== Mulai siklus: {label} ===")
    if is_paused():
        log("Bot paused, skip.")
        return

    try:
        news = collect_news()
        news = [n for n in news if is_relevant(n)]
        news = dedupe(news)
        news = news[:3] # Maksimal 3 berita per siklus

        if not news:
            log("Tidak ada berita baru.")
            return

        header = f"<b>UPDATE {label.upper()}</b>\n{now_wib().strftime('%d %b %Y, %H:%M WIB')}\n\n"
        send_telegram(header)

        sent_items = []
        # Logika Konteks (Pencarian Kata Kunci Spesifik)
        KATA_KUNCI_KONTEKS = ["msci", "fed", "powell", "anthropic", "indonesia", "singapur", "bitcoin", "ethereum", "iran", "israel", "oil", "minyak", "etf", "sec"]
        
        for i, item in enumerate(news, 1):
            log(f"Analisis {i}/{len(news)}: {item['title'][:60]}")
            
            history = load_json(HISTORY_PATH, [])
            prev_context = ""
            judul_lower = item['title'].lower()
            
            for h in history[-50:]:
                h_lower = h.get("title", "").lower()
                for kk in KATA_KUNCI_KONTEKS:
                    if kk in judul_lower and kk in h_lower and h['title'] != item['title']:
                        prev_context = f"Sebelumnya: {h['title']}"
                        break
                if prev_context: break
            
            analysis = analyze_with_groq(item, prev_context)
            msg = format_news_message(item, analysis)
            
            if send_telegram(msg):
                sent_items.append(item)
            time.sleep(2)

        # Simpan ke history
        history = load_json(HISTORY_PATH, [])
        for item in sent_items:
            history.append({
                "time": now_wib().isoformat(),
                "source": item["source"],
                "title": item["title"],
                "link": item["link"],
            })
        save_json(HISTORY_PATH, history[-2000:])
        log(f"Selesai. Terkirim: {len(sent_items)}")

    except Exception as e:
        err = f"Siklus {label} gagal:\n{traceback.format_exc()[-1000:]}"
        log(err)
        send_error(err)

# ==========================================
# 8. CRYPTO PRICE & ALERTS
# ==========================================
def get_crypto_change_1h(symbol):
    cid = config.WATCHLIST_CRYPTO.get(symbol.upper())
    if not cid: return None
    try:
        url = f"https://api.coingecko.com/api/v3/coins/{cid}/market_chart"
        r = requests.get(url, params={"vs_currency": "usd", "days": "1"}, timeout=15)
        if r.status_code != 200: return None
        prices = r.json().get("prices", [])
        if len(prices) < 2: return None
        
        now_ms = prices[-1][0]
        one_hour_ago = now_ms - 3600 * 1000
        past_price = None
        for ts, p in prices:
            if ts >= one_hour_ago:
                past_price = p
                break
        if past_price is None: past_price = prices[0][1]
        current = prices[-1][1]
        change_pct = ((current - past_price) / past_price) * 100
        return {"symbol": symbol, "current": current, "change_1h": change_pct}
    except Exception as e:
        log(f"Error change 1h {symbol}: {e}")
        return None

def check_price_alerts():
    if is_paused(): return
    for symbol in config.WATCHLIST_CRYPTO:
        data = get_crypto_change_1h(symbol)
        if not data: continue
        change = data["change_1h"]
        if abs(change) >= config.CRYPTO_ALERT_1H:
            arrow = "NAIK" if change > 0 else "TURUN"
            msg = f"<b>ALERT {symbol} ({arrow})</b>\n\nHarga: ${data['current']:,.2f}\n1 Jam: {change:+.2f}%\n\n{now_wib().strftime('%H:%M WIB')}"
            send_telegram(msg)
            log(f"Alert {symbol}: {change:+.2f}%")
        time.sleep(3)

# ==========================================
# 9. FETCH COIN DETAIL
# ==========================================
def get_coin_detail(symbol):
    try:
        search_url = f"https://api.coingecko.com/api/v3/search?query={symbol}"
        r_search = requests.get(search_url, timeout=15)
        if r_search.status_code != 200: return None
        
        coins = r_search.json().get("coins", [])
        coin_id = None
        for c in coins:
            if c["symbol"].upper() == symbol.upper():
                coin_id = c["id"]
                break
        if not coin_id: return None

        detail_url = f"https://api.coingecko.com/api/v3/coins/{coin_id}"
        r_detail = requests.get(detail_url, params={"localization": "false", "tickers": "false", "market_data": "true", "community_data": "false", "developer_data": "false"}, timeout=15)
        if r_detail.status_code != 200: return None
        
        data = r_detail.json()
        md = data.get("market_data", {})
        
        return {
            "name": data.get("name"),
            "symbol": data.get("symbol", "").upper(),
            "desc": data.get("description", {}).get("en", ""),
            "market_cap": md.get("market_cap", {}).get("usd", 0),
            "volume": md.get("total_volume", {}).get("usd", 0),
            "circ_supply": md.get("circulating_supply", 0),
            "max_supply": md.get("max_supply", 0),
            "price": md.get("current_price", {}).get("usd", 0)
        }
    except Exception as e:
        log(f"Error get_coin_detail: {e}")
        return None

# ==========================================
# 10. TELEGRAM COMMANDS
# ==========================================
last_update_id = 0

def check_telegram_commands():
    global last_update_id
    try:
        url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/getUpdates"
        params = {"timeout": 0, "allowed_updates": ["message"]}
        if last_update_id > 0:
            params["offset"] = last_update_id + 1

        r = requests.get(url, params=params, timeout=15)
        if r.status_code != 200: return
            
        updates = r.json().get("result", [])
        for upd in updates:
            last_update_id = upd["update_id"]
            msg = upd.get("message", {})
            text = msg.get("text", "").strip()
            chat_id = str(msg.get("chat", {}).get("id", ""))
            
            if chat_id != str(config.TELEGRAM_CHAT_ID): continue
            if text.startswith("/"): handle_command(text)
    except Exception as e:
        log(f"Command check error: {e}")

def handle_command(text):
    cmd = text.split()[0].lower()

    if cmd in ("/start", "/help"):
        send_telegram("<b>Bot Berita Finansial</b>\n\nCommand:\n/now - berita terbaru\n/btc - berita Bitcoin\n/ihsg - berita IHSG\n/msci - berita MSCI\n/flow - harga crypto\n/cek TICKER - cek fundamental koin\n/pause - matikan notif\n/resume - nyalakan notif\n/status - cek status bot")

    elif cmd == "/pause":
        PAUSE_PATH.write_text("paused")
        send_telegram("Bot di-pause.")
    elif cmd == "/resume":
        if PAUSE_PATH.exists(): PAUSE_PATH.unlink()
        send_telegram("Bot aktif lagi.")
    elif cmd == "/status":
        history = load_json(HISTORY_PATH, [])
        paused = "PAUSED" if is_paused() else "AKTIF"
        send_telegram(f"Status Bot\n\nStatus: {paused}\nBerita tersimpan: {len(history)}\nWaktu: {now_wib().strftime('%d %b %Y %H:%M WIB')}")
    elif cmd == "/now":
        send_telegram("Mengambil berita terbaru...")
        run_news_cycle(label="Manual")
    elif cmd in ("/btc", "/eth", "/ihsg", "/msci"):
        keyword = cmd[1:].upper()
        history = load_json(HISTORY_PATH, [])
        matched = [h for h in history if keyword.lower() in h.get("title", "").lower()][-5:]
        if matched:
            msg = f"Berita {keyword} (5 terakhir)\n\n"
            for h in matched: msg += f"{h['title']}\n{h['source']} - {h['time'][:16]}\n{h['link']}\n\n"
            send_telegram(msg)
        else:
            send_telegram(f"Tidak ada berita {keyword} tersimpan.")
    elif cmd == "/flow":
        send_telegram("<b>Harga Crypto Terbaru</b>\n\nMengambil data...")
        try:
            ids = ",".join(config.WATCHLIST_CRYPTO.values())
            r = requests.get("https://api.coingecko.com/api/v3/simple/price", params={"ids": ids, "vs_currencies": "usd", "include_24hr_change": "true"}, timeout=20)
            if r.status_code == 200:
                data = r.json()
                msg = "<b>Harga Crypto Terbaru</b>\n\n"
                for ticker, cid in config.WATCHLIST_CRYPTO.items():
                    if cid in data:
                        info = data[cid]
                        price = info.get('usd', 0)
                        change = info.get('usd_24h_change', 0)
                        price_str = f"${price:.4f}" if price < 1 else f"${price:,.2f}"
                        sign = "+" if change >= 0 else ""
                        msg += f"{ticker}: {price_str} ({sign}{change:.2f}%)\n"
                send_telegram(msg)
        except Exception as e:
            send_telegram(f"Error: {e}")
    elif cmd.startswith("/cek"):
        parts = text.split()
        if len(parts) < 2:
            send_telegram("Format salah. Contoh: <code>/cek BTC</code>")
            return
        ticker = parts[1].upper()
        send_telegram(f"Mencari data untuk <b>{ticker}</b>...")
        data = get_coin_detail(ticker)
        if not data:
            send_telegram(f"Koin <b>{ticker}</b> tidak ditemukan di CoinGecko.")
            return
        
        def f_usd(x): return f"${x:,.0f}" if x else "Tidak disebutkan"
        def f_num(x): return f"{x:,.0f}" if x else "Tidak terbatas / Tidak disebutkan"
        
        header = f"<b>{data['name']} ({data['symbol']})</b>\n\n"
        stats = f"<b>Data Angka:</b>\n• Harga: {f_usd(data['price'])}\n• Market Cap: {f_usd(data['market_cap'])}\n• Volume 24j: {f_usd(data['volume'])}\n• Supply Beredar: {f_num(data['circ_supply'])}\n• Max Supply: {f_num(data['max_supply'])}\n\n"
        
        send_telegram(header + stats + "Menyusun penjelasan fundamental...")
        fundamental = analyze_coin_fundamental(data)
        footer = f"\n\n<i>(Catatan: Data diambil otomatis. Selalu cek whitepaper dan website resmi. Bukan saran investasi).</i>"
        send_telegram(f"<b>Penjelasan Fundamental {data['symbol']}</b>\n\n{fundamental}{footer}")

# ==========================================
# 11. MAIN ENTRY
# ==========================================
def main():
    log("Bot mulai berjalan.")
    download_from_gist()

    current = now_wib()
    today_str = current.strftime("%Y-%m-%d")
    
    state = load_json(STATE_PATH, {"last_runs": {}})
    last_runs = state.get("last_runs", {})

    is_scheduled_time = False
    schedule_label = ""
    
    for sched in config.SCHEDULE_TIMES:
        sched_hour, sched_min = map(int, sched.split(":"))
        current_mins = current.hour * 60 + current.minute
        sched_mins = sched_hour * 60 + sched_min
        
        # Toleransi telat 15 menit
        if sched_mins <= current_mins <= (sched_mins + 15):
            run_key = f"{today_str}_{sched}"
            if run_key not in last_runs:
                is_scheduled_time = True
                schedule_label = sched
                last_runs[run_key] = True
                break

    if is_scheduled_time:
        log(f"Masuk jadwal: {schedule_label}.")
        run_news_cycle(label=f"Jadwal {schedule_label}")
        state["last_runs"] = last_runs
        save_json(STATE_PATH, state)
    else:
        log("Bukan jadwal push. Cek command...")

    check_telegram_commands()
    log("Cek alert harga...")
    check_price_alerts()
    
    upload_to_gist()
    log("Selesai.")

if __name__ == "__main__":
    main()
