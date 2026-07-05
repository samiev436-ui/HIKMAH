import logging
import requests
from telegram import ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

# 🔑 Вставь свои ключи
TELEGRAM_TOKEN = "8065909527:AAFxbnUlsg8TEy2Dt4RcUI2zit5jn_0Ffh8"
GEMINI_API_KEY = "Ab8RN6IltBO76btjqabEpPR6yF2por8gGRe5mg62pJPhnbuVBQ"

logging.basicConfig(level=logging.INFO)

# 🧠 Функция обращения к Gemini API
def ask_gemini(prompt):
    try:
        response = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}",
            json={"contents":[{"parts":[{"text": prompt}]}]}
        )
        return response.json()["candidates"][0]["content"]["parts"][0]["text"]
    except Exception:
        return "Ошибка при обращении к Gemini."

# 📌 Главное меню
main_menu = ReplyKeyboardMarkup(
    [
        ["Исламские темы", "Аят"],
        ["Хадис", "Задать вопрос"],
        ["Помощь"]
    ],
    resize_keyboard=True
)

# 🕌 Команда /start
def start(update, context):
    update.message.reply_text(
        "Ассаляму алейкум!\n\n"
        "Я бот с Gemini API. Выбери действие:",
        reply_markup=main_menu
    )

# 🔘 Обработка кнопок
def buttons(update, context):
    text = update.message.text.lower()

    if text == "исламские темы":
        update.message.reply_text("Напиши тему, например: Таухид, Молитва, Пост.")
        return

    if text == "аят":
        update.message.reply_text("Напиши номер аята, например: 2:183")
        return

    if text == "хадис":
        update.message.reply_text("Напиши ключевое слово хадиса, например: намерение")
        return

    if text == "задать вопрос":
        update.message.reply_text("Напиши свой вопрос:")
        return

    if text == "помощь":
        update.message.reply_text(
            "Команды:\n"
            "/start — главное меню\n"
            "Исламские темы — объяснение тем\n"
            "Аят — объяснение аята\n"
            "Хадис — объяснение хадиса\n"
            "Задать вопрос — любой вопрос\n"
        )
        return

    answer = ask_gemini(text)
    update.message.reply_text(answer)

def main():
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, buttons))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
