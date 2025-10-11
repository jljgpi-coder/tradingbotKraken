from flask import Flask
from threading import Thread
import ccxt
import pandas as pd
import pandas_ta as ta
import time
import requests
import yaml
import numpy as np

# === Flask setup for Render Free Plan ===
app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Kraken Bot is running!"

# === Load config from environment variables if available ===
import os

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
SYMBOL = os.getenv("SYMBOL", "XBT/USD")
TIMEFRAME = os.getenv("TIMEFRAME", "5m")
CANDLES = int(os.getenv("CANDLES", 300))
POLL_SECONDS = int(os.getenv("POLL_SECONDS", 30))

# Fallback to config.yaml if needed
def load_config():
    try:
        with open("config.yaml", "r") as f:
            cfg = yaml.safe_load(f)
            global TELEGRAM_TOKEN, CHAT_ID, SYMBOL, TIMEFRAME, CANDLES, POLL_SECONDS
            TELEGRAM_TOKEN = TELEGRAM_TOKEN or cfg["telegram"]["bot_token"]
            CHAT_ID = CHAT_ID or cfg["telegram"]["chat_id"]
            SYMBOL = SYMBOL or cfg["kraken"]["symbol"]
            TIMEFRAME = TIMEFRAME or cfg["kraken"]["timeframe"]
            CANDLES = CANDLES or cfg["kraken"]["candles"]
            POLL_SECONDS = POLL_SECONDS or cfg["poll_seconds"]
    except FileNotFoundError:
        print("⚠️ config.yaml not found, using environment variables.")

load_config()

# === Initialize Kraken exchange ===
exchange = ccxt.kraken({
    "apiKey": os.getenv("KRAKEN_API_KEY"),
    "secret": os.getenv("KRAKEN_API_SECRET")
})

# === Telegram helper ===
def send_telegram(msg):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("⚠️ Telegram token or chat ID missing")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": msg}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print("Telegram send error:", e)

# === Fetch OHLCV data ===
def get_ohlcv():
    try:
        ohlcv = exchange.fetch_ohlcv(SYMBOL, timeframe=TIMEFRAME, limit=CANDLES)
        df = pd.DataFrame(ohlcv, columns=["time","open","high","low","close","volume"])
        df["time"] = pd.to_datetime(df["time"], unit="ms")
        return df
    except Exception as e:
        print("Fetch error:", e)
        return pd.DataFrame()

# === Generate signals ===
def generate_signal(df):
    df["ema20"] = ta.ema(df["close"], length=20)
    df["ema50"] = ta.ema(df["close"], length=50)
    df["rsi"] = ta.rsi(df["close"], length=14)
    bb = ta.bbands(df["close"], length=20, std=2)
    df["bb_upper"] = bb["BBU_20_2.0"]
    df["bb_lower"] = bb["BBL_20_2.0"]
    macd = ta.macd(df["close"])
    df["macd"] = macd["MACD_12_26_9"]
    df["signal"] = macd["MACDs_12_26_9"]

    close = df["close"].iloc[-1]
    ema20 = df["ema20"].iloc[-1]
    ema50 = df["ema50"].iloc[-1]
    rsi = df["rsi"].iloc[-1]
    macd_val = df["macd"].iloc[-1]
    macd_sig = df["signal"].iloc[-1]

    signal = None
    reason = ""

    if close > ema20 > ema50 and rsi < 70 and macd_val > macd_sig:
        signal = "LONG"
        reason = f"Price {close:.2f} above EMA20/50, RSI {rsi:.1f}, MACD bullish."
    elif close < ema20 < ema50 and rsi > 30 and macd_val < macd_sig:
        signal = "SHORT"
        reason = f"Price {close:.2f} below EMA20/50, RSI {rsi:.1f}, MACD bearish."

    return signal, reason

# === Main bot loop ===
def run_bot():
    last_signal = None
    while True:
        df = get_ohlcv()
        if df.empty:
            time.sleep(POLL_SECONDS)
            continue

        signal, reason = generate_signal(df)

        if signal and signal != last_signal:
            msg = f"📊 {SYMBOL} Day Trade Alert\nSignal: {signal}\n{reason}\n\nTP1: +0.5%\nTP2: +1%\nTP3: +2%\nSL: -0.5%"
            send_telegram(msg)
            last_signal = signal

        time.sleep(POLL_SECONDS)

# === Start Flask and bot thread ===
if __name__ == "__main__":
    try:
        send_telegram("🚀 Kraken Day Trading Bot Started!")
    except Exception as e:
        print("Telegram start message failed:", e)

    # Start bot loop in daemon thread
    Thread(target=run_bot, daemon=True).start()

    # Keep Flask running for Render Free
    print("✅ Starting Flask server on port 10000...")
    app.run(host="0.0.0.0", port=10000)
