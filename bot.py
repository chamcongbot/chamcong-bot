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
import os

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

# Chat ID quản lý
MANAGER_CHAT_ID = 8632857133

# Tên Telegram của quản lý
MANAGER_NAME = "Bố"

# Nhân viên + tên file Google Sheet
EMPLOYEES = {
    "Lê": "BangLuong_Sy",
    "Hiếu": "BangLuong_Hieu"
}

# Tên viết nhanh dùng cho /ung
EMPLOYEE_ALIAS = {
    "le": "Lê",
    "hieu": "Hiếu"
}

# Lưu trạng thái đã gửi ảnh
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


def get_row_by_day():
    """
    Ví dụ:
    hôm nay ngày 21
    -> ghi vào hàng 22

    A22 sẽ là 21/04/2026
    """

    today = datetime.now()

    day = today.day
    row = day + 1

    full_date = today.strftime("%d/%m/%Y")

    return row, full_date


def is_sunday():
    """
    Monday = 0
    Sunday = 6
    """
    return datetime.now().weekday() == 6


def mark_sunday(sheet, row):
    """
    Nếu là Chủ nhật:
    - tô đỏ cả hàng A -> I
    - ghi chú cột H = Chủ nhật
    """

    red_format = CellFormat(
        backgroundColor=Color(
            red=1,
            green=0.85,
            blue=0.85
        )
    )

    # tô đỏ cả dòng
    format_cell_range(
        sheet,
        f"A{row}:I{row}",
        red_format
    )

    # ghi chú cột H
    sheet.update(
        f"H{row}",
        [["Chủ nhật"]]
    )


# ======================================
# NHẬN ẢNH CHECK-IN
# ======================================

async def save_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.first_name

    if user not in EMPLOYEES:
        return

    if update.message.photo:
        last_photo[user] = True

        await update.message.reply_text(
            "📸 Đã nhận ảnh.\n"
            "Bạn có thể check-in."
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

    checkin = checkin_time[key]
    checkout = datetime.now()

    total_hours = round(
        (checkout - checkin).total_seconds() / 3600,
        2
    )

    row, full_date = get_row_by_day()
    sheet = get_sheet(user)

    # luôn ghi ngày vào cột A
    sheet.update(
        f"A{row}",
        [[full_date]]
    )

    # Sáng -> cột B
    if shift == "Sáng":
        sheet.update(
            f"B{row}",
            [[total_hours]]
        )

    # Chiều -> cột E
    elif shift == "Chiều":
        sheet.update(
            f"E{row}",
            [[total_hours]]
        )

    # nếu là Chủ nhật -> tô đỏ + ghi chú
    if is_sunday():
        mark_sunday(sheet, row)

    await update.message.reply_text(
        f"💰 {user}\n"
        f"Ca: {shift}\n"
        f"Số giờ làm: {total_hours} giờ\n"
        f"Đã lưu vào bảng lương."
    )

    del checkin_time[key]


# ======================================
# LỆNH CHECK-IN / CHECK-OUT
# ======================================

# /cis = check-in sáng
async def cis(update, context):
    await handle_checkin(update, context, "Sáng")


# /cos = check-out sáng
async def cos(update, context):
    await handle_checkout(update, context, "Sáng")


# /cic = check-in chiều
async def cic(update, context):
    await handle_checkin(update, context, "Chiều")


# /coc = check-out chiều
async def coc(update, context):
    await handle_checkout(update, context, "Chiều")


# ======================================
# CHỞ HÀNG
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
            "Ví dụ:\n/tch 5000000"
        )
        return

    try:
        amount = int(context.args[0])

        row, full_date = get_row_by_day()
        sheet = get_sheet(user)

        # cột A = ngày
        sheet.update(
            f"A{row}",
            [[full_date]]
        )

        # cột F = chở hàng
        sheet.update(
            f"F{row}",
            [[amount]]
        )

        # nếu là Chủ nhật
        if is_sunday():
            mark_sunday(sheet, row)

        await update.message.reply_text(
            f"🚚 Đã ghi chở hàng: {amount:,}đ"
        )

    except:
        await update.message.reply_text(
            "❌ Sai cú pháp.\n"
            "Ví dụ: /tch 5000000"
        )


# ======================================
# ỨNG LƯƠNG
#
# Ví dụ:
# /ung hieu 500000
# /ung le 1000000
# ======================================

async def ung(update, context):

    # chỉ quản lý được dùng
    if update.effective_user.id != 8632857133:
        await update.message.reply_text(
            "❌ Chỉ quản lý mới dùng được lệnh này."
        )
        return

    # kiểm tra cú pháp
    if len(context.args) < 2:
        await update.message.reply_text(
            "Ví dụ:\n/ung hieu 500000"
        )
        return

    try:
        employee_input = context.args[0].lower()
        amount = int(context.args[1])

        # kiểm tra tên nhân viên
        if employee_input not in EMPLOYEE_ALIAS:
            await update.message.reply_text(
                "❌ Nhân viên không hợp lệ."
            )
            return

        target = EMPLOYEE_ALIAS[employee_input]

        row, full_date = get_row_by_day()
        sheet = get_sheet(target)

        # ghi ngày
        sheet.update(
            f"A{row}",
            [[full_date]]
        )

        # ghi ứng lương cột I
        sheet.update(
            f"I{row}",
            [[amount]]
        )

        await update.message.reply_text(
            f"💸 Đã ghi ứng lương\n"
            f"👤 Nhân viên: {target}\n"
            f"💰 Số tiền: {amount:,}đ"
        )

    except Exception as e:
        await update.message.reply_text(
            f"❌ Lỗi:\n{e}"
        )

# ======================================
# XUẤT EXCEL CUỐI THÁNG
# ======================================

async def export_salary(context):
    for user, file_name in EMPLOYEES.items():
        sheet = client.open(file_name).sheet1

        # lấy toàn bộ dữ liệu
        data = sheet.get_all_values()

        # xuất Excel
        df = pd.DataFrame(data)

        file_excel = (
            f"{file_name}_"
            f"{datetime.now().strftime('%m_%Y')}.xlsx"
        )

        df.to_excel(
            file_excel,
            index=False
        )

        # gửi file cho quản lý
        await context.bot.send_document(
            chat_id=MANAGER_CHAT_ID,
            document=open(file_excel, "rb"),
            caption=f"📄 Bảng lương tháng của {user}"
        )

        # reset dữ liệu tháng cũ
        # giữ nguyên công thức ngoài vùng này
        sheet.batch_clear([
            "A2:I32"
        ])

        os.remove(file_excel)


# ======================================
# RUN BOT
# ======================================

app = ApplicationBuilder().token(
    BOT_TOKEN
).build()

# nhận ảnh check-in
app.add_handler(
    MessageHandler(
        filters.PHOTO,
        save_photo
    )
)

# commands
app.add_handler(CommandHandler("cis", cis))
app.add_handler(CommandHandler("cos", cos))
app.add_handler(CommandHandler("cic", cic))
app.add_handler(CommandHandler("coc", coc))
app.add_handler(CommandHandler("tch", tch))
app.add_handler(CommandHandler("ung", ung))

print("🔥 Bot đang chạy...")

app.run_polling()
