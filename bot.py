import os
import time
import requests
import ccxt
import pandas as pd
import pandas_ta as ta
from flask import Flask
from threading import Thread

# === Flask for Render health check ===
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running"

def run_flask():
    app.run(host="0.0.0.0", port=8080)

Thread(target=run_flask).start()

# === Load environment variables ===
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
KRAKEN_API_KEY = os.environ.get("KRAKEN_API_KEY")
KRAKEN_API_SECRET = os.environ.get("KRAKEN_API_SECRET")
SYMBOL = os.environ.get("SYMBOL", "XBT/USD")
TIMEFRAME = os.environ.get("TIMEFRAME", "5m")
CANDLES = int(os.environ.get("CANDLES", 300))
POLL_SECONDS = int(os.environ.get("POLL_SECONDS", 30))

# === Setup Kraken exchange ===
exchange = ccxt.kraken({
    "apiKey": KRAKEN_API_KEY,
    "secret": KRAKEN_API_SECRET
})

# === Telegram helper ===
def send_telegram(msg):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": msg}
        )
    except Exception as e:
        print("Telegram send error:", e)

# === Fetch OHLCV ===
def get_ohlcv():
    try:
        ohlcv = exchange.fetch_ohlcv(SYMBOL, timeframe=TIMEFRAME, limit=CANDLES)
        df = pd.DataFrame(ohlcv, columns=["time","open","high","low","close","volume"])
        df["time"] = pd.to_datetime(df["time"], unit="ms")
        return df
    except Exception as e:
        print("Fetch error:", e)
        return pd.DataFrame()

# === Generate trading signals ===
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

if __name__ == "__main__":
    send_telegram("🚀 Kraken Day Trading Bot Started!")
    run_bot()
