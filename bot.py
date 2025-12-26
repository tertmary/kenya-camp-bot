#!/usr/bin/env python3
import os
import logging
import threading
import time

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

REMINDER_DELAY = 60 * 60  # 1 час

# ================== ТЕКСТЫ ==================
START_TEXT = (
    "Привет! 👋 Ты в боте про беговой кемп в Iten, Кения 🇰🇪\n\n"
    "Мы были там месяц и собираем русскую группу.\n\n"
    "Что тебе важно сейчас?"
)

PRICE_TEXT = (
    "💰 Стоимость:\n\n"
    "1️⃣ Лонгстей без питания:\n"
    "— проживание: 1500 ₽/день\n"
    "— еда: 500–1300 ₽/день\n\n"
    "2️⃣ Основной пакет:\n"
    "— проживание + 4-разовое питание\n"
    "— беговые тренировки с кенийскими тренерами\n\n"
    "Ориентир: ~42 € / день"
)

REMINDER_TEXT = (
    "⏱ Прошёл час 🙂\n\n"
    "Ты уже заполнил(а) анкету на предзапись?\n"
    "Если нет — это займёт 1–2 минуты 👇"
)

# ================== КЛАВИАТУРЫ ==================
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Сколько стоит", callback_data="price")],
        [InlineKeyboardButton("Предзапись", callback_data="presign")],
        [InlineKeyboardButton("Перейти в канал", url=CHANNEL_URL)],
    ])

def reminder_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Заполнить анкету", url=FORM_URL)],
        [InlineKeyboardButton("Уже заполнил(а) ✅", callback_data="done")],
    ])

# ================== FASTAPI ==================
app_api = FastAPI()

@app_api.get("/")
def health():
    return {"status": "ok"}

def run_api():
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app_api, host="0.0.0.0", port=port)

# ================== НАПОМИНАНИЕ ==================
def schedule_reminder(bot, chat_id, user_id, storage):
    if storage.get(user_id):
        return

    def task():
        time.sleep(REMINDER_DELAY)
        if not storage.get(user_id):
            bot.send_message(
                chat_id=chat_id,
                text=REMINDER_TEXT,
                reply_markup=reminder_keyboard()
            )

    threading.Thread(target=task, daemon=True).start()

# ================== ХЕНДЛЕРЫ ==================
user_done = {}

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(START_TEXT, reply_markup=main_menu())

async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    chat_id = query.message.chat_id

    if query.data == "price":
        await query.edit_message_text(PRICE_TEXT, reply_markup=main_menu())
        schedule_reminder(context.bot, chat_id, user_id, user_done)

    elif query.data == "presign":
        await query.edit_message_text(
            "Заполни анкету 👇",
            reply_markup=reminder_keyboard()
        )
        schedule_reminder(context.bot, chat_id, user_id, user_done)

    elif query.data == "done":
        user_done[user_id] = True
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
