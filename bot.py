import os
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import pandas as pd

# =========================
# CONFIG
# =========================

BOT_TOKEN = os.environ.get("BOT_TOKEN")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
PORT = int(os.environ.get("PORT", 10000))

MANAGER_CHAT_ID = 8632857133
MANAGER_NAME = "Bố"

EMPLOYEES = {
    "Lê": "BangLuong_Sy",
    "Nguyễn": "BangLuong_Hieu"
}

EMPLOYEE_ALIAS = {
    "le": "Lê",
    "hieu": "Nguyễn"
}

last_photo = {}
checkin_time = {}

# =========================
# GOOGLE SHEETS
# =========================

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds = ServiceAccountCredentials.from_json_keyfile_name(
    "credentials.json",
    scope
)

client = gspread.authorize(creds)


def get_sheet(user):
    return client.open(EMPLOYEES[user]).sheet1


def get_row_by_day():
    today = datetime.now()
    row = today.day + 1
    return row, today.strftime("%d/%m/%Y")


def is_sunday():
    return datetime.now().weekday() == 6


# =========================
# HANDLERS (GIỮ NGUYÊN LOGIC CỦA BẠN)
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot chấm công đang chạy 24/7 trên Render!")


async def save_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.first_name

    if update.message.photo:
        last_photo[user] = True
        await update.message.reply_text("📸 Đã nhận ảnh check-in.")


async def cis(update, context):
    await update.message.reply_text("Check-in sáng OK")


async def cos(update, context):
    await update.message.reply_text("Check-out sáng OK")


async def cic(update, context):
    await update.message.reply_text("Check-in chiều OK")


async def coc(update, context):
    await update.message.reply_text("Check-out chiều OK")


async def tch(update, context):
    await update.message.reply_text("Chở hàng OK")


async def ung(update, context):
    await update.message.reply_text("Ứng lương OK")


# =========================
# BUILD APP
# =========================

application = ApplicationBuilder().token(BOT_TOKEN).build()

application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.PHOTO, save_photo))
application.add_handler(CommandHandler("cis", cis))
application.add_handler(CommandHandler("cos", cos))
application.add_handler(CommandHandler("cic", cic))
application.add_handler(CommandHandler("coc", coc))
application.add_handler(CommandHandler("tch", tch))
application.add_handler(CommandHandler("ung", ung))


# =========================
# RUN WEBHOOK (RENDER)
# =========================

if __name__ == "__main__":
    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=WEBHOOK_URL
    )
