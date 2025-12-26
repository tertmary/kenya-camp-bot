#!/usr/bin/env python3
import os
import logging
import threading
from fastapi import FastAPI
import uvicorn

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ================== НАСТРОЙКИ ==================
CHANNEL_URL = "https://t.me/fun_cultura_com"
FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSdiMo_-N0q7pCbXi1gqp_EJb8iXSlntfG3ctiyp0JFD32Z5ew/viewform"
CAMP_DOC_PATH = "camp_details.pdf"

REMINDER_DELAY_SEC = 60 * 60  # 1 час
REMINDER_TEXT = (
    "⏱ Прошёл час 🙂\n\n"
    "Ты уже заполнил(а) анкету на предзапись?\n"
    "Если нет — это займёт 1–2 минуты 👇"
)

# ================== ТЕКСТЫ ==================
START_TEXT = (
    "Привет! 👋 Ты в боте про беговой кемп в Iten, Кения (2400 м) 🇰🇪\n\n"
    "Мы были там месяц и собираем русскую группу.\n\n"
    "Что тебе важно сейчас?"
)

INCLUDED_TEXT = (
    "✅ Что входит в пакет:\n\n"
    "— проживание (2-местный номер)\n"
    "— 4-разовое питание\n"
    "— беговые тренировки с кенийскими тренерами\n"
    "— стадион / зал / бассейн\n"
    "— 2 core-тренировки\n\n"
    "Дополнительно: перелёт, виза, страховка, массаж."
)

PRICE_TEXT = (
    "Форматы:\n\n"
    "1️⃣ Лонгстей без питания:\n"
    "— проживание: 1500 ₽/день (меньше месяца — дороже)\n"
    "— еда: 500–1300 ₽/день\n\n"
    "2️⃣ Основной пакет:\n"
    "— проживание + 4-разовое питание\n"
    "— беговые тренировки с кенийскими тренерами\n"
    "— вся инфраструктура\n\n"
    "Ориентир: ~42 € / день"
)

PRESIGN_TEXT = (
    "Предзапись = ты первым получишь:\n"
    "✅ даты\n"
    "✅ финальную цену\n"
    "✅ ТОЧНУЮ смету\n\n"
    "Заполни анкету 👇"
)

# ================== КЛАВИАТУРЫ ==================
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Что входит", callback_data="included")],
        [InlineKeyboardButton("Сколько стоит", callback_data="price")],
        [InlineKeyboardButton("📄 Документ", callback_data="doc")],
        [InlineKeyboardButton("Предзапись", callback_data="presign")],
        [InlineKeyboardButton("Перейти в канал", url=CHANNEL_URL)],
    ])

def reminder_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Заполнить анкету", url=FORM_URL)],
        [InlineKeyboardButton("Уже заполнил(а) ✅", callback_data="done")],
    ])

# ================== FASTAPI (для Railway) ==================
app_api = FastAPI()

@app_api.get("/")
def health():
    return {"status": "ok"}

def run_api():
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app_api, host="0.0.0.0", port=port)

# ================== НАПОМИНАНИЕ ==================
async def reminder_job(context: ContextTypes.DEFAULT_TYPE):
    data = context.job.data
    user_id = data["user_id"]
    chat_id = data["chat_id"]

    if context.application.bot_data.get(f"done_{user_id}"):
        return

    await context.bot.send_message(
        chat_id=chat_id,
        text=REMINDER_TEXT,
        reply_markup=reminder_keyboard()
    )

def schedule_reminder(context, chat_id, user_id):
    key = f"reminder_{user_id}"
    if context.application.bot_data.get(key):
        return
    context.application.bot_data[key] = True
    context.job_queue.run_once(
        reminder_job,
        REMINDER_DELAY_SEC,
        data={"chat_id": chat_id, "user_id": user_id},
    )

# ================== ХЕНДЛЕРЫ ==================
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(START_TEXT, reply_markup=main_menu())

async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    chat_id = query.message.chat_id

    if query.data == "included":
        await query.edit_message_text(INCLUDED_TEXT, reply_markup=main_menu())

    elif query.data == "price":
        await query.edit_message_text(PRICE_TEXT, reply_markup=main_menu())
        schedule_reminder(context, chat_id, user_id)

    elif query.data == "presign":
        await query.edit_message_text(PRESIGN_TEXT, reply_markup=main_menu())
        schedule_reminder(context, chat_id, user_id)

    elif query.data == "done":
        context.application.bot_data[f"done_{user_id}"] = True
        await query.edit_message_text("Отлично ✅ Я отметила.")

# ================== MAIN ==================
def main():
    logging.basicConfig(level=logging.INFO)

    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("Нет TELEGRAM_BOT_TOKEN")

    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CallbackQueryHandler(on_callback))

    threading.Thread(target=run_api, daemon=True).start()
    app.run_polling()

if __name__ == "__main__":
    main()