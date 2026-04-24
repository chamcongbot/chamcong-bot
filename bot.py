
# bot.py
# Full webhook version chạy Render Free Web Service

from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

import asyncio
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
from gspread_formatting import (
    CellFormat,
    Color,
    format_cell_range
)

# ======================================
# CONFIG
# ======================================

# Telegram Bot Token
BOT_TOKEN = "8608324582:AAFBw4nKRZkzU3_cb4wVmP6cr-QxUl1VTi0"

# URL Render sau khi deploy
WEBHOOK_URL = "https://chamcong-bot.onrender.com"

# Chat ID quản lý
MANAGER_CHAT_ID = 8632857133

# Tên Telegram của quản lý
MANAGER_NAME = "Bố"

# Nhân viên + file Google Sheet
EMPLOYEES = {
    "Lê": "BangLuong_Sy",
    "Nguyễn": "BangLuong_Hieu"
}

# Tên viết nhanh dùng cho /ung
EMPLOYEE_ALIAS = {
    "le": "Lê",
    "hieu": "Nguyễn"
}

# Lưu ảnh check-in
last_photo = {}

# Lưu thời gian check-in
checkin_time = {}

# ======================================
# GOOGLE SHEETS
# ======================================

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
    file_name = EMPLOYEES[user]
    return client.open(file_name).sheet1


def get_row_by_today():
    """
    A2 = ngày 1
    A3 = ngày 2
    ...
    A32 = ngày 31
    """
    day = datetime.now().day
    return day + 1


def is_sunday():
    return datetime.now().weekday() == 6


def mark_sunday(sheet, row):
    """
    Chủ nhật:
    - tô đỏ hàng
    - ghi chú cột F
    """
    if is_sunday():
        red_format = CellFormat(
            backgroundColor=Color(1, 0.85, 0.85)
        )

        format_cell_range(
            sheet,
            f"A{row}:F{row}",
            red_format
        )

        sheet.update(
            f"F{row}",
            [["Chủ nhật"]]
        )


# ======================================
# SAVE PHOTO
# ======================================

async def save_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.first_name

    if user not in EMPLOYEES:
        return

    if update.message.photo:
        last_photo[user] = True

        await update.message.reply_text(
            "📸 Đã nhận ảnh. Bạn có thể check-in."
        )


# ======================================
# CHECK-IN
# ======================================

async def handle_checkin(update, context, shift):
    user = update.effective_user.first_name

    if user not in EMPLOYEES:
        await update.message.reply_text(
            "❌ Bạn không có quyền."
        )
        return

    if user not in last_photo:
        await update.message.reply_text(
            "⚠️ Vui lòng gửi ảnh trước khi check-in."
        )
        return

    now = datetime.now()
    key = f"{user}_{shift}"

    checkin_time[key] = now

    await update.message.reply_text(
        f"✅ {user} check-in ca {shift}\n"
        f"🕒 {now.strftime('%H:%M:%S')}"
    )

    del last_photo[user]


# ======================================
# CHECK-OUT
# ======================================

async def handle_checkout(update, context, shift):
    user = update.effective_user.first_name
    key = f"{user}_{shift}"

    if user not in EMPLOYEES:
        await update.message.reply_text(
            "❌ Bạn không có quyền."
        )
        return

    if key not in checkin_time:
        await update.message.reply_text(
            "⚠️ Chưa có check-in trước đó."
        )
        return

    sheet = get_sheet(user)
    row = get_row_by_today()
    today = datetime.now().strftime("%d/%m/%Y")

    # Cột A = ngày
    sheet.update(
        f"A{row}",
        [[today]]
    )

    # B = công sáng
    if shift == "Sáng":
        sheet.update(
            f"B{row}",
            [["1 công sáng"]]
        )

    # C = công chiều
    if shift == "Chiều":
        sheet.update(
            f"C{row}",
            [["1 công chiều"]]
        )

    mark_sunday(sheet, row)

    await update.message.reply_text(
        f"✅ Đã ghi công ca {shift}"
    )

    del checkin_time[key]


# ======================================
# COMMANDS
# ======================================

async def cis(update, context):
    await handle_checkin(update, context, "Sáng")


async def cos(update, context):
    await handle_checkout(update, context, "Sáng")


async def cic(update, context):
    await handle_checkin(update, context, "Chiều")


async def coc(update, context):
    await handle_checkout(update, context, "Chiều")


# ======================================
# /TCH
# /tch 5000000
# ======================================

async def tch(update, context):
    user = update.effective_user.first_name

    if user not in EMPLOYEES:
        await update.message.reply_text(
            "❌ Bạn không có quyền."
        )
        return

    if len(context.args) == 0:
        await update.message.reply_text(
            "Ví dụ: /tch 5000000"
        )
        return

    try:
        amount = int(context.args[0])

        sheet = get_sheet(user)
        row = get_row_by_today()

        # D = chở hàng
        sheet.update(
            f"D{row}",
            [[amount]]
        )

        await update.message.reply_text(
            f"🚚 Đã ghi tiền chở hàng: {amount:,}đ"
        )

    except:
        await update.message.reply_text(
            "❌ Sai cú pháp. Ví dụ: /tch 5000000"
        )


# ======================================
# /UNG
# /ung hieu 500000
# ======================================

async def ung(update, context):
    user = update.effective_user.first_name

    if user != MANAGER_NAME:
        await update.message.reply_text(
            "❌ Chỉ quản lý mới dùng được."
        )
        return

    if len(context.args) < 2:
        await update.message.reply_text(
            "Ví dụ: /ung hieu 500000"
        )
        return

    try:
        alias = context.args[0].lower()
        amount = int(context.args[1])

        if alias not in EMPLOYEE_ALIAS:
            await update.message.reply_text(
                "❌ Không tìm thấy nhân viên.\n"
                "Ví dụ:\n"
                "/ung hieu 500000\n"
                "/ung le 300000"
            )
            return

        target_name = EMPLOYEE_ALIAS[alias]
        sheet = get_sheet(target_name)
        row = get_row_by_today()
        today = datetime.now().strftime("%d/%m/%Y")

        # A = ngày
        sheet.update(
            f"A{row}",
            [[today]]
        )

        # E = ứng lương
        sheet.update(
            f"E{row}",
            [[amount]]
        )

        await update.message.reply_text(
            f"💸 Đã ứng {amount:,}đ cho {target_name}"
        )

    except:
        await update.message.reply_text(
            "❌ Sai cú pháp. Ví dụ: /ung hieu 500000"
        )


# ======================================
# TELEGRAM APPLICATION
# ======================================

telegram_app = Application.builder().token(
    BOT_TOKEN
).build()

telegram_app.add_handler(
    MessageHandler(
        filters.PHOTO,
        save_photo
    )
)

telegram_app.add_handler(CommandHandler("cis", cis))
telegram_app.add_handler(CommandHandler("cos", cos))
telegram_app.add_handler(CommandHandler("cic", cic))
telegram_app.add_handler(CommandHandler("coc", coc))
telegram_app.add_handler(CommandHandler("tch", tch))
telegram_app.add_handler(CommandHandler("ung", ung))


# ======================================
# FLASK WEBHOOK
# ======================================

app = Flask(__name__)


@app.route("/", methods=["GET"])
def home():
    return "Bot Telegram đang chạy"


@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(
        request.get_json(force=True),
        Bot(BOT_TOKEN)
    )

    asyncio.run(
        telegram_app.process_update(update)
    )

    return "ok"


# ======================================
# SET WEBHOOK
# ======================================

async def setup_webhook():
    bot = Bot(BOT_TOKEN)

    await bot.set_webhook(
        url=f"{WEBHOOK_URL}/{BOT_TOKEN}"
    )


asyncio.run(setup_webhook())

print("🔥 Bot webhook đang chạy...")