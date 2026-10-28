import os

# === API KEYS ===
# Sengaja dibiarkan kosong. Nilai asli diambil dari GitHub Secrets.
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

COINGLASS_API_KEY = ""
GITHUB_TOKEN = os.environ.get("GH_TOKEN", "")
GIST_ID = os.environ.get("GIST_ID", "")
GIST_FILENAME = "news_history.json"

# ... (biarin sisa kodenya sama kayak sebelumnya) ...

# ============================================================
# JADWAL PUSH (WIB / UTC+7)
# ============================================================
SCHEDULE_TIMES = ["04:00", "06:00", "12:00", "16:00", "19:00"]

# ============================================================
# THRESHOLD NOTIF PERGERAKAN HARGA (dalam persen)
# ============================================================
CRYPTO_ALERT_1H = 5.0
STOCK_ALERT_1H = 3.0
IHSG_ALERT_1H = 1.0

# ============================================================
# WATCHLIST DEFAULT
# ============================================================
# Format: "TICKER": "id-coingecko"
WATCHLIST_CRYPTO = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "SOL": "solana",
    "BNB": "binancecoin",
    "XRP": "ripple",
    "LINK": "chainlink",
    "UNI": "uniswap",
    "HBAR": "hedera-hashgraph",
    "GRT": "the-graph",
    "ADA": "cardano",
    "NEAR": "near",
    "VET": "vechain",
    "ARB": "arbitrum",
    "SUI": "sui",
    "ANKR": "ankr",
    "CELR": "celer-network",
    "CFX": "conflux-token",
    "CYBER": "cyberconnect",
    "ENS": "ethereum-name-service",
    "FET": "fetch-ai",
    "FIDA": "bonfida",
    "FLUX": "zelcash",
    "INJ": "injective-protocol",
    "PHA": "pha",
    "STG": "stargate-finance",
    "TWT": "trust-wallet-token",
    "MANTA": "manta-network",
    "ONDO": "ondo-finance",
    "RONIN": "ronin",
    "CORE": "coredaoorg",
    "AIOZ": "aioz-network",
    "CGPT": "chaingpt",
    "TRAC": "origintrail",
    "HYPE": "hyperliquid",
    "NEWT": "newton-protocol",
    "PROVE": "succinct",
    "EDEN": "openeden",
    "ESP": "espresso"
}
WATCHLIST_US = ["AAPL", "NVDA", "TSLA", "MSFT", "GOOGL"]
WATCHLIST_ID = ["BBCA", "BBRI", "BMRI", "TLKM", "ASII"]

# ============================================================
# KEYWORD FILTER BERITA
# ============================================================
KEYWORDS_GLOBAL = [
    "MSCI", "Fed", "Powell", "Trump", "tariff", "suku bunga",
    "inflation", "inflasi", "rate cut", "rate hike", "ETF",
    "SEC", "acquisition", "akuisisi", "merger", "IPO",
    "war", "perang", "Hormuz", "Iran", "Israel", "oil", "minyak",
    "Bitcoin", "Ethereum", "crypto", "stablecoin",
    "AI", "artificial intelligence", "semiconductor", "chip",
]

KEYWORDS_ID = [
    "IHSG", "BEI", "OJK", "BI-Rate", "Bank Indonesia", "rupiah",
    "asing", "net buy", "net sell", "emiten", "saham",
    "BBCA", "BBRI", "BMRI", "TLKM", "ASII", "GOTO", "ADRO",
    "MSCI", "reklasifikasi", "standalone", "emerging market",
]

# ============================================================
# WHITELIST MEDIA (15 sumber)
# ============================================================
TRUSTED_SOURCES = {
    # Internasional (English -> auto translate ke Indo)
    "Reuters": "https://www.reuters.com/markets/",
    "Bloomberg": "https://feeds.bloomberg.com/markets/news.rss",
    "AFP": "https://www.afp.com/en/rss",
    "Business Times SG": "https://www.businesstimes.com.sg/rss",
    "CNA": "https://www.channelnewsasia.com/rss",
    "CNBC Asia": "https://www.cnbc.com/id/100003114/device/rss/rss.html",
    "ZAWYA": "https://www.zawya.com/en/rss",
    "CoinDesk": "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "CoinTelegraph": "https://cointelegraph.com/rss",
    # Indonesia (langsung)
    "Kontan": "https://rss.kontan.co.id/",
    "Katadata": "https://katadata.co.id/rss",
    "Bisnis": "https://www.bisnis.com/rss",
    "CNBC Indonesia": "https://www.cnbcindonesia.com/rss",
    "Investor.id": "https://investor.id/rss",
    "Kompas": "https://www.kompas.id/rss",
}

# ============================================================
# GROQ MODEL
# ============================================================
GROQ_MODEL = "openai/gpt-oss-120b"

# ============================================================
# NAMA FILE (jangan diubah)
# ============================================================
HISTORY_FILE = "news_history.json"
SEEN_FILE = "seen_titles.json"
PAUSE_FILE = "paused.flag"
