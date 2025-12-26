#!/usr/bin/env python3
import os
import logging
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# === Настройки ===
CHANNEL_URL = "https://t.me/fun_cultura_com"
FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSdiMo_-N0q7pCbXi1gqp_EJb8iXSlntfG3ctiyp0JFD32Z5ew/viewform"

# Положи файл рядом с bot.py
CAMP_DOC_PATH = "camp_details.pdf"  # можно .docx, но PDF лучше

# Напоминание: 1 час
REMINDER_DELAY_SEC = 60 * 60  # 1 hour
REMINDER_TEXT = (
    "⏱ Прошёл час 🙂\n\n"
    "Ты уже заполнил(а) анкету на предзапись?\n"
    "Если нет — это займёт 1–2 минуты 👇"
)

# === Тексты ===
START_TEXT = (
    "Привет! 👋 Ты в боте про беговой кемп в Iten, Кения (2400 м) 🇰🇪\n\n"
    "Мы были там месяц, тренировались и собираем русскую группу в кемп.\n"
    "Здесь:\n"
    "✅ что входит\n"
    "✅ ориентир по стоимости (честно)\n"
    "✅ предзапись — чтобы первым получить даты, финальную цену и ТОЧНУЮ смету\n\n"
    "Что тебе важно сейчас?"
)

INCLUDED_TEXT = (
    "✅ Что входит в наш основной пакет:\n\n"
    "— проживание (двухместный номер)\n"
    "— 4-разовое питание\n"
    "— беговые тренировки с кенийскими тренерами (по программе/расписанию)\n"
    "— доступ к стадиону\n"
    "— доступ к тренажёрному залу\n"
    "— бассейн\n"
    "— 2 core-тренировки с тренером (по расписанию)\n\n"
    "Дополнительно потребуется:\n"
    "— перелёт\n"
    "— виза в Кению\n"
    "— страховка\n"
    "— массаж (1200 ₽/сеанс)\n"
    "— личные покупки/экипировка"
)

PRICE_INTRO_TEXT = (
    "Сразу честно: точные даты и финальная стоимость будут после согласования сезона и длительности.\n"
    "Но чтобы ты понимал(а) порядок — вот реальные ориентиры по Iten 👇"
)

PRICE_TEXT = (
    "Формат 1 (как было у нас): лонгстей без питания\n"
    "— проживание: 1500 ₽/день (при проживании меньше месяца обычно дороже)\n"
    "— питание отдельно: 500–1300 ₽/день\n"
    "— массаж: 1200 ₽/сеанс\n\n"
    "Формат 2 (наш основной продукт): полный пакет\n"
    "— проживание + 4-разовое питание\n"
    "— беговые тренировки с кенийскими тренерами\n"
    "— инфраструктура: бассейн / стадион / зал\n"
    "— + 2 core-тренировки по расписанию\n"
    "Ориентир: ~42 € / день (финал зависит от длительности и курса)\n\n"
    "Отдельно: перелёт, виза, страховка, личные траты."
)

PRICE_SOFT_SCANDAL_TEXT = (
    "Почему многим кажется, что Кения “только для элиты”?\n"
    "Обычно в одну кучу смешивают жизнь в кемпе и “дорогие сценарии” (перелёт, экипа, лишние траты).\n\n"
    "Я за прозрачность: как только утвердим формат — будет ТОЧНАЯ смета:\n"
    "что входит, что не входит и какая итоговая сумма."
)

CHANNEL_TEXT = (
    "В канале я выкладываю:\n"
    "— быт кемпа (как выглядит день “бег–еда–сон”)\n"
    "— новости по набору русской группы\n\n"
    "Нажми кнопку ниже, чтобы открыть канал 👇"
)

PRESIGN_TEXT = (
    "Предзапись = ты первым получишь:\n"
    "✅ даты, как только они появятся\n"
    "✅ финальную цену и ТОЧНУЮ смету (что входит и итоговая сумма)\n"
    "✅ приоритет на место в русской группе\n\n"
    "Нажми кнопку ниже и заполни анкету 👇"
)

ITEN_TRIGGER_TEXT = (
    "Ты написал(а) «ИТЕН» — держи главное 👇\n\n"
    "Есть два формата:\n"
    "1) лонгстей без питания: проживание 1500 ₽/день (при проживании меньше месяца обычно дороже), "
    "питание отдельно 500–1300 ₽/день\n"
    "2) наш основной пакет: 4-разовое питание + беговые тренировки с кенийскими тренерами + "
    "инфраструктура (бассейн/стадион/зал) + 2 core\n"
    "Ориентир: ~42 € / день\n\n"
    "Чтобы первым получить даты, финальную цену и ТОЧНУЮ смету + приоритет на место — оставь предзапись 👇"
)

DOC_CAPTION = "📄 Подробности кемпа (документ)"

# === Клавиатуры ===
def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Что входит", callback_data="menu_included")],
        [InlineKeyboardButton("Сколько стоит", callback_data="menu_price")],
        [InlineKeyboardButton("📄 Документ о кемпе", callback_data="send_doc")],
        [InlineKeyboardButton("Предзапись", callback_data="menu_presign")],
        [InlineKeyboardButton("Перейти в канал", callback_data="menu_channel")],
    ])

def back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Назад в меню", callback_data="menu_start")]
    ])

def channel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Открыть канал", url=CHANNEL_URL)],
        [InlineKeyboardButton("⬅️ Назад в меню", callback_data="menu_start")],
    ])

def presign_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Заполнить анкету", url=FORM_URL)],
        [InlineKeyboardButton("📄 Документ о кемпе", callback_data="send_doc")],
        [InlineKeyboardButton("Открыть канал", url=CHANNEL_URL)],
        [InlineKeyboardButton("⬅️ Назад в меню", callback_data="menu_start")],
    ])

def iten_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Предзапись (анкета)", url=FORM_URL)],
        [InlineKeyboardButton("📄 Документ о кемпе", callback_data="send_doc")],
        [InlineKeyboardButton("Открыть канал", url=CHANNEL_URL)],
        [InlineKeyboardButton("Что входит", callback_data="menu_included")],
    ])

def price_intro_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Показать ориентиры", callback_data="menu_price_more")],
        [InlineKeyboardButton("📄 Документ о кемпе", callback_data="send_doc")],
        [InlineKeyboardButton("⬅️ Назад в меню", callback_data="menu_start")],
    ])

def price_more_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📄 Документ о кемпе", callback_data="send_doc")],
        [InlineKeyboardButton("Предзапись", callback_data="menu_presign")],
        [InlineKeyboardButton("⬅️ Назад в меню", callback_data="menu_start")],
    ])

def reminder_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Заполнить анкету", url=FORM_URL)],
        [InlineKeyboardButton("Уже заполнил(а) ✅", callback_data="presign_done")],
        [InlineKeyboardButton("Перейти в канал", url=CHANNEL_URL)],
    ])

# === Напоминание через 1 час (только тем, кто нажал “Сколько стоит” или “Предзапись”) ===
async def reminder_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    job_data = context.job.data or {}
    chat_id = job_data.get("chat_id")
    user_id = job_data.get("user_id")

    if user_id is not None:
        if context.application.bot_data.get(f"presigned_{user_id}", False):
            return

    if chat_id:
        await context.bot.send_message(
            chat_id=chat_id,
            text=REMINDER_TEXT,
            reply_markup=reminder_keyboard()
        )

def schedule_reminder_once(chat_id: int, user_id: int, context: ContextTypes.DEFAULT_TYPE) -> None:
    key = f"reminder_scheduled_{user_id}"
    if context.application.bot_data.get(key):
        return  # уже запланировано

    context.application.bot_data[key] = True
    context.job_queue.run_once(
        reminder_job,
        when=REMINDER_DELAY_SEC,
        data={"chat_id": chat_id, "user_id": user_id},
        name=f"reminder_{user_id}"
    )

# === Отправка документа ===
async def send_camp_doc(chat_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if not os.path.exists(CAMP_DOC_PATH):
        await context.bot.send_message(
            chat_id=chat_id,
            text=(
                "Пока не вижу файл документа 😅\n"
                "Положи файл рядом с bot.py и назови его camp_details.pdf.\n"
                "Если хочешь — могу вместо файла отправлять ссылку на документ."
            )
        )
        return False

    with open(CAMP_DOC_PATH, "rb") as f:
        await context.bot.send_document(
            chat_id=chat_id,
            document=f,
            caption=DOC_CAPTION
        )
    return True

# === Хендлеры ===
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(START_TEXT, reply_markup=main_menu_keyboard())

async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data
    chat_id = query.message.chat_id
    user_id = query.from_user.id

    # Кнопка "Уже заполнил(а) ✅" из напоминания
    if data == "presign_done":
        context.application.bot_data[f"presigned_{user_id}"] = True
        await query.edit_message_text(
            "Отлично ✅ Я отметила, что анкета заполнена.\n"
            "Как только появятся даты/точная стоимость — напишу первой волне.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Перейти в канал", url=CHANNEL_URL)],
                [InlineKeyboardButton("⬅️ В меню", callback_data="menu_start")],
            ])
        )
        return

    if data == "send_doc":
        await send_camp_doc(chat_id, context)
        return

    if data == "menu_start":
        await query.edit_message_text(START_TEXT, reply_markup=main_menu_keyboard())
        return

    if data == "menu_included":
        await query.edit_message_text(INCLUDED_TEXT, reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📄 Документ о кемпе", callback_data="send_doc")],
            [InlineKeyboardButton("⬅️ Назад в меню", callback_data="menu_start")],
        ]))
        return

    # Напоминание ставим ТОЛЬКО если нажал “Сколько стоит”
    if data == "menu_price":
        await query.edit_message_text(PRICE_INTRO_TEXT, reply_markup=price_intro_keyboard())
        schedule_reminder_once(chat_id, user_id, context)
        return

    if data == "menu_price_more":
        text = f"{PRICE_TEXT}\n\n{PRICE_SOFT_SCANDAL_TEXT}"
        await query.edit_message_text(text, reply_markup=price_more_keyboard())
        return

    if data == "menu_channel":
        await query.edit_message_text(CHANNEL_TEXT, reply_markup=channel_keyboard())
        return

    # И ТОЛЬКО если нажал “Предзапись”
    if data == "menu_presign":
        await query.edit_message_text(PRESIGN_TEXT, reply_markup=presign_keyboard())
        schedule_reminder_once(chat_id, user_id, context)
        return

    await query.edit_message_text(START_TEXT, reply_markup=main_menu_keyboard())

async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (update.message.text or "").strip().lower()

    if text == "итен":
        await update.message.reply_text(ITEN_TRIGGER_TEXT, reply_markup=iten_keyboard())
        return

    await update.message.reply_text(
        "Я могу подсказать по кемпу 👇 Выбери пункт меню:",
        reply_markup=main_menu_keyboard(),
    )

def main() -> None:
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO
    )

    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("Не найден TELEGRAM_BOT_TOKEN. Экспортируй токен в переменную окружения.")

    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CallbackQueryHandler(on_callback))

if __name__ == "__main__":
    main()
