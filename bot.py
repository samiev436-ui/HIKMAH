import os
import logging
import requests
from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from designer_bot import handle_designer_message

# ========= НАСТРОЙКИ =========
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.1-8b-instant"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ========= ГЛАВНОЕ МЕНЮ =========
main_menu = ReplyKeyboardMarkup(
    [
        ["Исламские темы", "Коран (114 сур)"],
        ["Хадисы (книги)", "Дуа"],
        ["Вопросы", "Помощь"]
    ],
    resize_keyboard=True
)
context.bot_data["main_menu"] = main_menu

# ========= ИСЛАМСКИЕ ТЕМЫ (50) =========
islam_topics = [
    "Таухид", "Ширк", "Иман", "Ислам", "Ихсан",
    "Намаз", "Пост", "Закят", "Хадж", "Ду'а",
    "Акида", "Судный день", "Ангелы", "Пророки", "Коран",
    "Сунна", "Хадисы", "Фикх", "Нравственность", "Чистота",
    "Брак", "Семья", "Дети", "Одежда", "Халяль",
    "Харам", "Торговля", "Джума", "Джаназа", "Мечеть",
    "Имена Аллаха", "Сира", "Сподвижники", "Табиины", "Учёные",
    "Истории из Корана", "Истории из Сунны", "Джихад", "Рамадан", "Ночь предопределения",
    "Шавваль", "Зуль-хиджа", "Ид аль-Фитр", "Ид аль-Адха", "Умма",
    "Адабы", "Сердечные болезни", "Покаяние", "Терпение", "Благодарность"
]

islam_topics_keyboard = ReplyKeyboardMarkup(
    [islam_topics[i:i+3] for i in range(0, len(islam_topics), 3)],
    resize_keyboard=True
)

# ========= ПОДКАТЕГОРИИ =========
subtopics = {
    "Намаз": ["Фард намаз", "Сунна намаз", "Ошибки в намазе", "Ночной намаз"],
    "Пост": ["Фард пост", "Сунна пост", "Ошибки в посте", "Рамадан"],
    "Таухид": ["Единство в господстве", "Единство в поклонении", "Единство в именах и атрибутах"],
}

# ========= СПИСОК 114 СУР =========
quran_suras = [
    "Аль-Фатиха", "Аль-Бакара", "Али-Имран", "Ан-Ниса", "Аль-Маида",
    "Аль-Анам", "Аль-Араф", "Аль-Анфаль", "Ат-Тауба", "Юнус",
    "Худ", "Юсуф", "Ар-Ра'д", "Ибрахим", "Аль-Хиджр",
    "Ан-Нахль", "Аль-Исра", "Аль-Кахф", "Марьям", "Та Ха",
    "Аль-Анбия", "Аль-Хадж", "Аль-Муминун", "Ан-Нур", "Аль-Фуркан",
    "Аш-Шуара", "Ан-Намль", "Аль-Касас", "Аль-Анкабут", "Ар-Рум",
    "Лукман", "Ас-Саджда", "Аль-Ахзаб", "Саба", "Фатыр",
    "Ясин", "Ас-Саффат", "Сад", "Аз-Зумар", "Гафир",
    "Фуссилат", "Аш-Шура", "Аз-Зухруф", "Ад-Духан", "Аль-Джасия",
    "Аль-Ахкаф", "Мухаммад", "Аль-Фатх", "Аль-Худжурат", "Каф",
    "Аз-Зарият", "Ат-Тур", "Ан-Наджм", "Аль-Камар", "Ар-Рахман",
    "Аль-Вакиа", "Аль-Хадид", "Аль-Муджадала", "Аль-Хашр", "Аль-Мумтахина",
    "Ас-Сафф", "Аль-Джумуа", "Аль-Мунафикун", "Ат-Тагабун", "Ат-Талак",
    "Ат-Тахрим", "Аль-Мульк", "Аль-Калям", "Аль-Хакка", "Аль-Мааридж",
    "Нух", "Аль-Джинн", "Аль-Муззаммил", "Аль-Муддассир", "Аль-Кияма",
    "Аль-Инсан", "Аль-Мурсалат", "Ан-Наба", "Ан-Назиат", "Абаса",
    "Ат-Таквир", "Аль-Инфитар", "Аль-Мутаффифин", "Аль-Иншикак", "Аль-Бурудж",
    "Ат-Тарик", "Аль-А'ля", "Аль-Гашия", "Аль-Фаджр", "Аль-Балад",
    "Аш-Шамс", "Аль-Лейл", "Ад-Духа", "Аш-Шарх", "Ат-Тин",
    "Аль-Алак", "Аль-Кадр", "Аль-Баййина", "Аз-Залзала", "Аль-Адият",
    "Аль-Кариа", "Ат-Такатур", "Аль-Аср", "Аль-Хумаза", "Аль-Филь",
    "Курайш", "Аль-Маун", "Аль-Каусар", "Аль-Кафирун", "Ан-Наср",
    "Аль-Масад", "Аль-Ихлас", "Аль-Фалак", "Ан-Нас"
]

quran_keyboard = ReplyKeyboardMarkup(
    [quran_suras[i:i+2] for i in range(0, len(quran_suras), 2)],
    resize_keyboard=True
)

# ========= ДУА ИЗ КОРАНА =========
dua_quran = [
    "ربنا آتنا في الدنيا حسنة",
    "ربنا تقبل منا",
    "ربنا ظلمنا أنفسنا",
    "ربنا لا تؤاخذنا",
    "ربنا اغفر لنا",
    "ربنا هب لنا من أزواجنا",
    "رب اشرح لي صدري",
    "رب زدني علما",
    "ربنا عليك توكلنا",
    "ربنا لا تزغ قلوبنا"
]

dua_quran_keyboard = ReplyKeyboardMarkup(
    [dua_quran[i:i+2] for i in range(0, len(dua_quran), 2)],
    resize_keyboard=True
)

# ========= ДУА ИЗ КРЕПОСТЬ МУСУЛЬМАНИНА =========
dua_hisnul = [
    "Дуа перед сном",
    "Дуа при пробуждении",
    "Дуа при входе в дом",
    "Дуа при выходе из дома",
    "Дуа перед едой",
    "Дуа после еды",
    "Дуа при страхе",
    "Дуа при болезни",
    "Дуа при трудности",
    "Дуа при радости"
]

dua_hisnul_keyboard = ReplyKeyboardMarkup(
    [dua_hisnul[i:i+2] for i in range(0, len(dua_hisnul), 2)],
    resize_keyboard=True
)

# ========= МЕНЮ ДУА =========
dua_menu = ReplyKeyboardMarkup(
    [
        ["Дуа из Корана"],
        ["Дуа из Крепость мусульманина"],
        ["Назад"]
    ],
    resize_keyboard=True
)

# ========= ХАДИС-КНИГИ =========
hadith_books = [
    "Сахих аль-Бухари",
    "Сахих Муслим",
    "Сунан Тирмизи",
    "Сунан Ибн Маджа",
    "Сунан Ан-Насаи",
    "Муснад Ахмад"
]

hadith_books_keyboard = ReplyKeyboardMarkup(
    [hadith_books[i:i+2] for i in range(0, len(hadith_books), 2)],
    resize_keyboard=True
)

# ========= КАТЕГОРИИ ВОПРОСОВ =========
question_categories = [
    "Вопросы по вере",
    "Вопросы по намазу",
    "Вопросы по посту",
    "Вопросы по закяту",
    "Вопросы по хаджу",
    "Вопросы по семье",
    "Вопросы по браку",
    "Вопросы по халяль/харам",
    "Вопросы по торговле",
    "Вопросы по одежде",
    "Вопросы по чистоте",
    "Вопросы по Корану",
    "Вопросы по хадисам",
    "Вопросы по истории",
    "Вопросы по Судному дню"
]

questions_keyboard = ReplyKeyboardMarkup(
    [question_categories[i:i+2] for i in range(0, len(question_categories), 2)],
    resize_keyboard=True
)

# ========= ask_groq() =========
def ask_groq(prompt: str) -> str:
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": GROQ_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Ты — исламская энциклопедия HIKMAH HUB. "
                    "Отвечай строго в формате исламской книги. "
                    "ВСЕГДА включай арабский текст аята и арабский текст хадиса. "
                    "Тафсир и объяснение хадиса — только на русском."
                )
            },
            {"role": "user", "content": prompt}
        ]
    }

    try:
        r = requests.post(GROQ_URL, json=data, headers=headers, timeout=30)
        r.raise_for_status()
        resp = r.json()
        return resp["choices"][0]["message"]["content"]

    except Exception as e:
        logger.error(f"GROQ error: {e}")
        return "Произошла ошибка при обращении к энциклопедии. Попробуйте ещё раз."

# ========= /start =========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Ассаляму алейкум! Добро пожаловать в HIKMAH HUB — исламскую энциклопедию.",
        reply_markup=main_menu
    )

# ========= ОБРАБОТЧИК ТЕКСТА =========
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
await handle_designer_message(update, context, GROQ_API_KEY, GROQ_MODEL)

 if text == "Исламские темы":
        await update.message.reply_text("Выберите тему:", reply_markup=islam_topics_keyboard)
        return

    if text == "Коран (114 сур)":
        await update.message.reply_text("Выберите суру:", reply_markup=quran_keyboard)
        return

    if text == "Хадисы (книги)":
        await update.message.reply_text("Выберите книгу хадисов:", reply_markup=hadith_books_keyboard)
        return

    if text == "Дуа":
        await update.message.reply_text("Выберите раздел:", reply_markup=dua_menu)
        return

    if text == "Дуа из Корана":
        await update.message.reply_text("Выберите дуа из Корана:", reply_markup=dua_quran_keyboard)
        return

    if text == "Дуа из Крепость мусульманина":
        await update.message.reply_text("Выберите дуа:", reply_markup=dua_hisnul_keyboard)
        return

    if text == "Назад":
        await update.message.reply_text("Главное меню:", reply_markup=main_menu)
        return

    if text in dua_quran:
        answer = ask_groq(f"Дуа из Корана: {text}. Дай арабский текст, тафсир и практическое применение.")
        await update.message.reply_text(answer)
        return

    if text in dua_hisnul:
        answer = ask_groq(f"Дуа из Крепость мусульманина: {text}. Дай арабский текст, перевод, объяснение и когда читать.")
        await update.message.reply_text(answer)
        return

    if text in islam_topics:
        if text in subtopics:
            keyboard = ReplyKeyboardMarkup([subtopics[text]], resize_keyboard=True)
            await update.message.reply_text(
                f"Выберите подкатегорию темы «{text}»:",
                reply_markup=keyboard
            )
        else:
            answer = ask_groq(f"Тема: {text}")
            await update.message.reply_text(answer)
        return

    for main_topic, subs in subtopics.items():
        if text in subs:
            answer = ask_groq(f"Главная тема: {main_topic}. Подтема: {text}.")
            await update.message.reply_text(answer)
            return

    if text in quran_suras:
        context.user_data["selected_sura"] = text
        await update.message.reply_text(
            f"Вы выбрали суру «{text}». Напишите номер аята."
        )
        return

    if text in hadith_books:
        context.user_data["selected_hadith_book"] = text
        await update.message.reply_text(
            f"Вы выбрали «{text}». Напишите номер хадиса."
        )
        return

    if "selected_sura" in context.user_data and text.isdigit():
        sura = context.user_data["selected_sura"]
        ayah = text
        answer = ask_groq(f"Сура: {sura}. Аят: {ayah}. Дай арабский текст и тафсир.")
        await update.message.reply_text(answer)
        context.user_data.pop("selected_sura", None)
        return

    if "selected_hadith_book" in context.user_data and text.isdigit():
        book = context.user_data["selected_hadith_book"]
        number = text
        answer = ask_groq(f"Книга: {book}. Хадис №{number}. Дай арабский текст и объяснение.")
        await update.message.reply_text(answer)
        context.user_data.pop("selected_hadith_book", None)
        return

    if text in question_categories:
        context.user_data["question_category"] = text
        await update.message.reply_text(
            f"Вы выбрали: {text}. Напишите свой вопрос."
        )
        return

    if "question_category" in context.user_data:
        category = context.user_data["question_category"]
        answer = ask_groq(f"Категория: {category}. Вопрос: {text}.")
        await update.message.reply_text(answer)
        context.user_data.pop("question_category", None)
        return

    answer = ask_groq(text)
    await update.message.reply_text(answer)

# ========= ЗАПУСК =========
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Bot started...")
    app.run_polling()

if __name__ == "__main__":
    main()
