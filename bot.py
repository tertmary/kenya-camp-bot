#!/usr/bin/env python3
import os
import logging

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
DOC_CAPTION = "📄 Подробности кемпа (документ)"

# ================== ТЕКСТЫ ==================
START_TEXT = (
    "Привет! 👋 Ты в боте про беговой кемп в Iten, Кения 🇰🇪\n\n"
    "Мы были там месяц и собираем русскую группу.\n\n"
    "Выбери, что тебе важно 👇"
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
    "💰 Стоимость (ориентиры):\n\n"
    "1️⃣ Лонгстей без питания:\n"
    "— проживание: 1500 ₽/день\n"
    "— питание: 500–1300 ₽/день\n\n"
    "2️⃣ Основной пакет:\n"
    "— проживание + 4-разовое питание\n"
    "— беговые тренировки с кенийскими тренерами\n"
    "— вся инфраструктура\n\n"
    "Ориентир: ~42 € / день"
)

PRESIGN_TEXT = (
    "📝 Предзапись в кемп:\n\n"
    "Ты первым(ой) получишь:\n"
    "— даты\n"
    "— финальную цену\n"
    "— ТОЧНУЮ смету\n\n"
    "Заполни анкету по кнопке ниже 👇"
)

CHANNEL_TEXT = (
    "В канале я выкладываю:\n"
    "— быт кемпа (день “бег–еда–сон”)\n"
    "— новости по набору русской группы\n\n"
    "Переходи 👇"
)

# ================== КЛАВИАТУРЫ ==================
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Что входит", callback_data="included")],
        [InlineKeyboardButton("Сколько стоит", callback_data="price")],
        [InlineKeyboardButton("📄 Документ о кемпе", callback_data="doc")],
        [InlineKeyboardButton("Предзапись", callback_data="presign")],
        [InlineKeyboardButton("Перейти в канал", callback_data="channel")],
    ])

def back_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Назад в меню", callback_data="menu")]
    ])

# ================== ДОКУМЕНТ ==================
async def send_doc(chat_id: int, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not os.path.exists(CAMP_DOC_PATH):
        await context.bot.send_message(
            chat_id=chat_id,
            text=(
                "Документ пока не найден 😅\n"
                "Проверь, что файл называется camp_details.pdf и лежит рядом с bot.py.\n"
                "Если хочешь — могу вместо файла отправлять ссылку."
            )
        )
        return

    with open(CAMP_DOC_PATH, "rb") as f:
        await context.bot.send_document(
            chat_id=chat_id,
            document=f,
            caption=DOC_CAPTION
        )

# ================== ХЕНДЛЕРЫ ==================
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(START_TEXT, reply_markup=main_menu())

async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id

    if query.data == "menu":
        await query.edit_message_text(START_TEXT, reply_markup=main_menu())

    elif query.data == "included":
        await query.edit_message_text(INCLUDED_TEXT, reply_markup=back_menu())

    elif query.data == "price":
        await query.edit_message_text(PRICE_TEXT, reply_markup=back_menu())

    elif query.data == "presign":
        await query.edit_message_text(
            PRESIGN_TEXT,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Заполнить анкету", url=FORM_URL)],
                [InlineKeyboardButton("📄 Документ о кемпе", callback_data="doc")],
                [InlineKeyboardButton("⬅️ Назад в меню", callback_data="menu")],
            ])
        )

    elif query.data == "channel":
        await query.edit_message_text(
            CHANNEL_TEXT,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Открыть канал", url=CHANNEL_URL)],
                [InlineKeyboardButton("⬅️ Назад в меню", callback_data="menu")],
            ])
        )

    elif query.data == "doc":
        await send_doc(chat_id, context)

async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip().lower()

    if text == "итен":
        await update.message.reply_text(PRICE_TEXT, reply_markup=main_menu())
        return

    await update.message.reply_text("Выбери пункт меню 👇", reply_markup=main_menu())

# ================== MAIN ==================
def main():
    logging.basicConfig(level=logging.INFO)

    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("Не найден TELEGRAM_BOT_TOKEN")

    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CallbackQueryHandler(on_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))

    app.run_polling()

if __name__ == "__main__":
    main()
