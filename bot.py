import os
import asyncio
import ccxt
import pandas as pd
import pandas_ta as ta
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ======= TELEGRAM BOT SETUP =======
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")  # store your token in .env
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")       # store chat id in .env

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot is online!")

async def send_message(text: str):
    """Send a message to your Telegram chat."""
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    async with app:
        await app.bot.send_message(chat_id=CHAT_ID, text=text)
