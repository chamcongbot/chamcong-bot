import os
import json
from flask import Flask, request
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# =====================
# ENV
# =====================
BOT_TOKEN = os.environ["BOT_TOKEN"]
WEBHOOK_URL = os.environ["WEBHOOK_URL"]
GOOGLE_CREDENTIALS = json.loads(os.environ["GOOGLE_CREDENTIALS"])
PORT = int(os.environ.get("PORT", 10000))

# =====================
# FLASK APP
# =====================
app = Flask(__name__)

# =====================
# GOOGLE SHEETS
# =====================
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_info(
    GOOGLE_CREDENTIALS,
    scopes=scope
)

client = gspread.authorize(creds)

EMPLOYEES = {
    "Lê": "BangLuong_Sy",
    "Nguyễn": "BangLuong_Hieu"
}

# =====================
# TELEGRAM APP
# =====================
application = ApplicationBuilder().token(BOT_TOKEN).build()

# =====================
# HANDLERS
# =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 Bot chấm công production đang chạy!")

async def cis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Check-in sáng OK")

async def cos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Check-out sáng OK")

async def cic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Check-in chiều OK")

async def coc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Check-out chiều OK")

# =====================
# REGISTER HANDLERS
# =====================
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("cis", cis))
application.add_handler(CommandHandler("cos", cos))
application.add_handler(CommandHandler("cic", cic))
application.add_handler(CommandHandler("coc", coc))

# =====================
# WEBHOOK ROUTE
# =====================
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
async def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    await application.process_update(update)
    return "ok"

# =====================
# SET WEBHOOK
# =====================
async def setup_webhook():
    await application.bot.set_webhook(url=f"{WEBHOOK_URL}/{BOT_TOKEN}")

# =====================
# RUN SERVER
# =====================
if __name__ == "__main__":
    import asyncio

    asyncio.run(setup_webhook())

    app.run(
        host="0.0.0.0",
        port=PORT
    )
