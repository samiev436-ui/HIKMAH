import logging
import os
from groq import Groq
from telegram import ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

logging.basicConfig(level=logging.INFO)

client = Groq(api_key=GROQ_API_KEY)

def check_groq_key():
    if not GROQ_API_KEY:
        logging.error("GROQ_API_KEY не задан!")
        return False
    try:
        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "user", "content": "test"}],
            max_tokens=5
        )
        logging.info("Groq API ключ рабочий.")
        return True
    except Exception as e:
        logging.error(f"Groq ключ недействителен: {e}")
        return False

def ask_groq(prompt):
    try:
        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {
                    "role": "system",
                    "content": "Ты исламский помощник. Отвечай на вопросы об исламе, Коране, хадисах и исламской практике на русском языке. Будь точным и уважительным."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=1024
        )
        return response.choices[0].message.content
    except Exception as e:
        logging.error(f"Groq error: {e}")
        return "Ошибка при обращении к Groq."

main_menu = ReplyKeyboardMarkup(
    [
        ["Исламские темы", "Аят"],
        ["Хадис", "Задать вопрос"],
        ["Помощь"]
    ],
    resize_keyboard=True
)

def start(update, context):
    update.message.reply_text(
        "Ассаляму алейкум!\n\n"
        "Я исламский бот на базе Groq AI. Выбери действие:",
        reply_markup=main_menu
    )

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

    answer = ask_groq(text)
    update.message.reply_text(answer)

def main():
    check_groq_key()
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, buttons))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
