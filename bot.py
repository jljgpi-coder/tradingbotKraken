import os
import asyncio
import ccxt
import pandas as pd
import pandas_ta as ta
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ======= LOAD ENVIRONMENT =======
load_dotenv()

# ======= TELEGRAM BOT SETUP =======
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
bot = app.bot

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot is online!")

async def send_message(text: str):
    """Send a message to your Telegram chat."""
    await bot.send_message(chat_id=CHAT_ID, text=text)
