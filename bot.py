import os
import sys
import logging
import httpx
from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# ========= НАСТРОЙКИ =========
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not TELEGRAM_TOKEN:
    sys.exit("FATAL: TELEGRAM_TOKEN environment variable is not set.")
if not GROQ_API_KEY:
    sys.exit("FATAL: GROQ_API_KEY environment variable is not set.")

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"
HISTORY_LIMIT = 6  # максимум сообщений в истории разговора (3 хода)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ========= ГЛАВНОЕ МЕНЮ =========
main_menu = ReplyKeyboardMarkup(
    [
        ["📚 Исламские темы", "📖 Коран (114 сур)"],
        ["📜 Хадисы (книги)", "🤲 Дуа"],
        ["❓ Вопросы", "ℹ️ Помощь"]
    ],
    resize_keyboard=True
)

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
    [islam_topics[i:i+3] for i in range(0, len(islam_topics), 3)] + [["🏠 Главное меню"]],
    resize_keyboard=True
)

# ========= ПОДКАТЕГОРИИ ВСЕХ 50 ТЕМ =========
subtopics = {
    "Таухид":               ["Единство в господстве", "Единство в поклонении", "Единство в именах и атрибутах", "Виды ширка"],
    "Ширк":                 ["Большой ширк", "Малый ширк", "Скрытый ширк", "Как избежать ширка"],
    "Иман":                 ["Столпы имана", "Признаки имана", "Что укрепляет иман", "Что ослабляет иман"],
    "Ислам":                ["Пять столпов ислама", "История ислама", "Исламский образ жизни", "Ислам и наука"],
    "Ихсан":                ["Определение ихсана", "Ихсан в поклонении", "Ихсан в отношениях", "Ихсан в труде"],
    "Намаз":                ["Фард намаз", "Сунна намаз", "Ошибки в намазе", "Ночной намаз (Тахаджуд)"],
    "Пост":                 ["Обязательный пост", "Сунна пост", "Ошибки в посте", "Рамадан"],
    "Закят":                ["Условия закята", "Нисаб", "Кому платить закят", "Закят аль-Фитр"],
    "Хадж":                 ["Условия хаджа", "Обряды хаджа", "Умра", "История хаджа"],
    "Ду'а":                 ["Правила дуа", "Лучшее время для дуа", "Дуа из Корана", "Дуа из Сунны"],
    "Акида":                ["Основы акиды", "Ахлю Сунна валь Джамаа", "Заблуждения в акиде", "Книги по акиде"],
    "Судный день":          ["Признаки Судного дня", "Малые признаки", "Большие признаки", "События Судного дня"],
    "Ангелы":               ["Сотворение ангелов", "Имена ангелов", "Функции ангелов", "Ангелы и люди"],
    "Пророки":              ["Первый пророк Адам", "Качества пророков", "История пророков", "Печать пророков ﷺ"],
    "Коран":                ["Откровение Корана", "Структура Корана", "Таджвид (чтение)", "Тафсир (толкование)"],
    "Сунна":                ["Виды сунны", "Хранение сунны", "Сунна и Коран", "Следование сунне"],
    "Хадисы":               ["Классификация хадисов", "Сахих хадисы", "Слабые хадисы", "Учёные хадисов"],
    "Фикх":                 ["Четыре мазхаба", "Источники фикха", "Фикх ибадата", "Фикх муамалат"],
    "Нравственность":       ["Основы ахляка", "Качества мусульманина", "Отношение к людям", "Самовоспитание"],
    "Чистота":              ["Тахарат", "Вуду (омовение)", "Гусль", "Таяммум"],
    "Брак":                 ["Условия брака", "Обязанности супругов", "Права жены", "Права мужа"],
    "Семья":                ["Права родителей", "Воспитание детей", "Родственные связи", "Исламская семья"],
    "Дети":                 ["Права детей", "Воспитание в исламе", "Образование детей", "Дуа за детей"],
    "Одежда":               ["Одежда мужчины", "Одежда женщины", "Хиджаб", "Украшения в исламе"],
    "Халяль":               ["Халяль пища", "Халяль заработок", "Халяль развлечения", "Критерии халяль"],
    "Харам":                ["Запрещённая пища", "Запрещённые действия", "Последствия харама", "Путь к избеганию"],
    "Торговля":             ["Условия торговли", "Запрещённые сделки", "Риба (ростовщичество)", "Этика торговца"],
    "Джума":                ["Хутба пятницы", "Намаз Джума", "Адабы пятницы", "Сунны пятницы"],
    "Джаназа":              ["Уход за умершим", "Намаз Джаназа", "Похороны", "Дуа за умерших"],
    "Мечеть":               ["Этика мечети", "История мечети", "Мечеть аль-Харам", "Мечеть Пророка ﷺ"],
    "Имена Аллаха":         ["99 имён Аллаха", "Аль-Асма аль-Хусна", "Имена и качества", "Как взывать к Аллаху"],
    "Сира":                 ["Рождение Пророка ﷺ", "Мекканский период", "Мединский период", "Кончина Пророка ﷺ"],
    "Сподвижники":          ["Четыре праведных халифа", "10 обрадованных раем", "Женщины-сподвижницы", "Выдающиеся сподвижники"],
    "Табиины":              ["Кто такие табиины", "Выдающиеся табиины", "Их вклад в ислам", "Период табиинов"],
    "Учёные":               ["Имам аль-Бухари", "Имам Муслим", "Имам Малик", "Великие учёные ислама"],
    "Истории из Корана":    ["История Адама", "История Мусы", "История Юсуфа", "История Ибрахима"],
    "Истории из Сунны":     ["Истории сподвижников", "Истории пророков в хадисах", "Назидательные истории", "Чудеса Пророка ﷺ"],
    "Джихад":               ["Виды джихада", "Джихад нафса", "Джихад знанием", "Условия джихада"],
    "Рамадан":              ["Достоинства Рамадана", "Сухур и ифтар", "Лайлатуль-Кадр", "Итикаф"],
    "Ночь предопределения": ["Когда Лайлатуль-Кадр", "Достоинства ночи", "Ибадат ночи", "Дуа ночи"],
    "Шавваль":              ["Пост 6 дней Шавваля", "Ид аль-Фитр", "Дела Шавваля", "Достоинства Шавваля"],
    "Зуль-хиджа":           ["Первые 10 дней", "День Арафа", "Жертвоприношение", "Такбир Ташрик"],
    "Ид аль-Фитр":          ["Намаз Ида", "Закят аль-Фитр", "Адабы Ида", "Поздравления в Ид"],
    "Ид аль-Адха":          ["Жертвоприношение (Курбан)", "Намаз Ида", "Распределение мяса", "Дни ташрика"],
    "Умма":                 ["Единство уммы", "Права мусульманина", "Служение умме", "Будущее уммы"],
    "Адабы":                ["Адабы приветствия", "Адабы застолья", "Адабы в мечети", "Адабы со старшими"],
    "Сердечные болезни":    ["Зависть (Хасад)", "Гордыня (Кибр)", "Показуха (Рия)", "Злоба (Хикд)"],
    "Покаяние":             ["Условия покаяния", "Как делать тауба", "Покаяние в Коране", "Принятие покаяния"],
    "Терпение":             ["Виды терпения", "Сабр в испытаниях", "Награда за терпение", "Примеры терпения"],
    "Благодарность":        ["Шукр Аллаху", "Как выражать благодарность", "Благодарность людям", "Плоды благодарности"],
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
    [quran_suras[i:i+2] for i in range(0, len(quran_suras), 2)] + [["🏠 Главное меню"]],
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
    [dua_quran[i:i+2] for i in range(0, len(dua_quran), 2)] + [["🔙 Назад", "🏠 Главное меню"]],
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
    [dua_hisnul[i:i+2] for i in range(0, len(dua_hisnul), 2)] + [["🔙 Назад", "🏠 Главное меню"]],
    resize_keyboard=True
)

# ========= МЕНЮ ДУА =========
dua_menu = ReplyKeyboardMarkup(
    [
        ["🤲 Дуа из Корана"],
        ["📗 Дуа из Крепость мусульманина"],
        ["🏠 Главное меню"]
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
    [hadith_books[i:i+2] for i in range(0, len(hadith_books), 2)] + [["🏠 Главное меню"]],
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
    [question_categories[i:i+2] for i in range(0, len(question_categories), 2)] + [["🏠 Главное меню"]],
    resize_keyboard=True
)

# ========= ask_groq() С ИСТОРИЕЙ =========
async def ask_groq(prompt: str, history: list | None = None) -> str:
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    system_message = {
        "role": "system",
        "content": (
            "Ты — исламская энциклопедия HIKMAH HUB. "
            "Отвечай строго в формате исламской книги. "
            "ВСЕГДА включай арабский текст аята и арабский текст хадиса. "
            "Тафсир и объяснение хадиса — только на русском. "
            "Помни контекст предыдущих сообщений разговора."
        )
    }

    messages = [system_message]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": prompt})

    data = {
        "model": GROQ_MODEL,
        "messages": messages,
        "temperature": 0.3,
        "max_tokens": 2000,
    }

    try:
        async with httpx.AsyncClient(timeout=40) as client:
            r = await client.post(GROQ_URL, json=data, headers=headers)
            r.raise_for_status()
            resp = r.json()
            return resp["choices"][0]["message"]["content"]

    except Exception as e:
        logger.error(f"GROQ error: {e}")
        return "⚠️ Произошла ошибка при обращении к энциклопедии. Попробуйте ещё раз."


def add_to_history(context: ContextTypes.DEFAULT_TYPE, user_text: str, bot_reply: str) -> None:
    """Добавляет пару сообщений в историю разговора, ограничивая HISTORY_LIMIT."""
    history = context.user_data.setdefault("history", [])
    history.append({"role": "user", "content": user_text})
    history.append({"role": "assistant", "content": bot_reply})
    # Обрезаем до последних HISTORY_LIMIT сообщений
    if len(history) > HISTORY_LIMIT:
        context.user_data["history"] = history[-HISTORY_LIMIT:]


# ========= /start =========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "🕌 *Ассаляму алейкум! Добро пожаловать в HIKMAH HUB*\n\n"
        "Я — исламская энциклопедия на базе ИИ.\n\n"
        "📚 *Что я умею:*\n"
        "• 50 исламских тем с подкатегориями\n"
        "• Все 114 сур Корана с тафсиром\n"
        "• Хадисы из 6 книг\n"
        "• Дуа из Корана и Крепости мусульманина\n"
        "• Ответы на ваши вопросы\n\n"
        "Выберите раздел в меню ниже ⬇️",
        parse_mode="Markdown",
        reply_markup=main_menu
    )


# ========= ОБРАБОТЧИК ТЕКСТА =========
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    # ── Навигация ──────────────────────────────────────────────────
    if text in ("🏠 Главное меню", "Главное меню"):
        context.user_data.pop("selected_sura", None)
        context.user_data.pop("selected_hadith_book", None)
        context.user_data.pop("question_category", None)
        context.user_data.pop("selected_topic", None)
        await update.message.reply_text("Главное меню:", reply_markup=main_menu)
        return

    if text in ("🔙 Назад", "Назад"):
        context.user_data.pop("selected_sura", None)
        context.user_data.pop("selected_hadith_book", None)
        context.user_data.pop("question_category", None)
        context.user_data.pop("selected_topic", None)
        await update.message.reply_text("Главное меню:", reply_markup=main_menu)
        return

    # ── Главное меню ───────────────────────────────────────────────
    if text in ("📚 Исламские темы", "Исламские темы"):
        await update.message.reply_text("Выберите тему:", reply_markup=islam_topics_keyboard)
        return

    if text in ("📖 Коран (114 сур)", "Коран (114 сур)"):
        await update.message.reply_text("Выберите суру:", reply_markup=quran_keyboard)
        return

    if text in ("📜 Хадисы (книги)", "Хадисы (книги)"):
        await update.message.reply_text("Выберите книгу хадисов:", reply_markup=hadith_books_keyboard)
        return

    if text in ("🤲 Дуа", "Дуа"):
        await update.message.reply_text("Выберите раздел дуа:", reply_markup=dua_menu)
        return

    if text in ("🤲 Дуа из Корана", "Дуа из Корана"):
        await update.message.reply_text("Выберите дуа из Корана:", reply_markup=dua_quran_keyboard)
        return

    if text in ("📗 Дуа из Крепость мусульманина", "Дуа из Крепость мусульманина"):
        await update.message.reply_text("Выберите дуа:", reply_markup=dua_hisnul_keyboard)
        return

    if text in ("❓ Вопросы", "Вопросы"):
        await update.message.reply_text(
            "Выберите категорию вопроса или напишите свой вопрос:",
            reply_markup=questions_keyboard
        )
        return

    if text in ("ℹ️ Помощь", "Помощь"):
        await update.message.reply_text(
            "📖 *Как пользоваться HIKMAH HUB:*\n\n"
            "• *Исламские темы* — 50 тем с подкатегориями (Таухид, Намаз, Фикх и др.)\n"
            "• *Коран* — выберите суру → укажите номер аята\n"
            "• *Хадисы* — выберите книгу → укажите номер хадиса\n"
            "• *Дуа* — дуа из Корана и Крепости мусульманина\n"
            "• *Вопросы* — выберите категорию и задайте свой вопрос\n\n"
            "💬 Также можно просто написать любой вопрос по исламу.\n\n"
            "🔄 /start — вернуться в начало",
            parse_mode="Markdown",
            reply_markup=main_menu
        )
        return

    # ── Дуа из Корана ──────────────────────────────────────────────
    if text in dua_quran:
        await update.message.reply_text("🔍 Ищу в энциклопедии...")
        history = context.user_data.get("history")
        prompt = f"Дуа из Корана: {text}. Дай арабский текст, тафсир и практическое применение."
        answer = await ask_groq(prompt, history)
        add_to_history(context, text, answer)
        await update.message.reply_text(answer, reply_markup=dua_quran_keyboard)
        return

    # ── Дуа из Крепости мусульманина ──────────────────────────────
    if text in dua_hisnul:
        await update.message.reply_text("🔍 Ищу в энциклопедии...")
        history = context.user_data.get("history")
        prompt = f"Дуа из Крепость мусульманина: {text}. Дай арабский текст, перевод, объяснение и когда читать."
        answer = await ask_groq(prompt, history)
        add_to_history(context, text, answer)
        await update.message.reply_text(answer, reply_markup=dua_hisnul_keyboard)
        return

    # ── Исламские темы → подкатегории ─────────────────────────────
    if text in islam_topics:
        if text in subtopics:
            context.user_data["selected_topic"] = text
            subs = subtopics[text]
            keyboard = ReplyKeyboardMarkup(
                [subs[i:i+2] for i in range(0, len(subs), 2)] + [["🏠 Главное меню"]],
                resize_keyboard=True
            )
            await update.message.reply_text(
                f"📂 Тема: *{text}*\nВыберите подкатегорию:",
                parse_mode="Markdown",
                reply_markup=keyboard
            )
        else:
            await update.message.reply_text("🔍 Ищу в энциклопедии...")
            history = context.user_data.get("history")
            answer = await ask_groq(f"Тема: {text}", history)
            add_to_history(context, text, answer)
            await update.message.reply_text(answer, reply_markup=islam_topics_keyboard)
        return

    # ── Подкатегории тем ───────────────────────────────────────────
    for main_topic, subs in subtopics.items():
        if text in subs:
            await update.message.reply_text("🔍 Ищу в энциклопедии...")
            history = context.user_data.get("history")
            prompt = f"Главная тема: {main_topic}. Подтема: {text}."
            answer = await ask_groq(prompt, history)
            add_to_history(context, text, answer)
            # Возвращаем клавиатуру с подкатегориями той же темы
            subs_list = subtopics[main_topic]
            keyboard = ReplyKeyboardMarkup(
                [subs_list[i:i+2] for i in range(0, len(subs_list), 2)] + [["🏠 Главное меню"]],
                resize_keyboard=True
            )
            await update.message.reply_text(answer, reply_markup=keyboard)
            return

    # ── Суры Корана → запрос номера аята ──────────────────────────
    if text in quran_suras:
        context.user_data["selected_sura"] = text
        await update.message.reply_text(
            f"📖 Сура *{text}*\nНапишите номер аята:",
            parse_mode="Markdown"
        )
        return

    # ── Книги хадисов → запрос номера ─────────────────────────────
    if text in hadith_books:
        context.user_data["selected_hadith_book"] = text
        await update.message.reply_text(
            f"📜 *{text}*\nНапишите номер хадиса:",
            parse_mode="Markdown"
        )
        return

    # ── Аят по номеру ─────────────────────────────────────────────
    if "selected_sura" in context.user_data and text.isdigit():
        sura = context.user_data["selected_sura"]
        ayah = text
        await update.message.reply_text("🔍 Ищу аят...")
        history = context.user_data.get("history")
        prompt = f"Сура: {sura}. Аят: {ayah}. Дай арабский текст и тафсир."
        answer = await ask_groq(prompt, history)
        add_to_history(context, f"Сура {sura}, аят {ayah}", answer)
        context.user_data.pop("selected_sura", None)
        await update.message.reply_text(answer, reply_markup=quran_keyboard)
        return

    # ── Хадис по номеру ───────────────────────────────────────────
    if "selected_hadith_book" in context.user_data and text.isdigit():
        book = context.user_data["selected_hadith_book"]
        number = text
        await update.message.reply_text("🔍 Ищу хадис...")
        history = context.user_data.get("history")
        prompt = f"Книга: {book}. Хадис №{number}. Дай арабский текст и объяснение."
        answer = await ask_groq(prompt, history)
        add_to_history(context, f"{book} №{number}", answer)
        context.user_data.pop("selected_hadith_book", None)
        await update.message.reply_text(answer, reply_markup=hadith_books_keyboard)
        return

    # ── Категории вопросов ────────────────────────────────────────
    if text in question_categories:
        context.user_data["question_category"] = text
        await update.message.reply_text(
            f"✏️ Вы выбрали: *{text}*\nНапишите свой вопрос:",
            parse_mode="Markdown"
        )
        return

    if "question_category" in context.user_data:
        category = context.user_data["question_category"]
        await update.message.reply_text("🔍 Обрабатываю вопрос...")
        history = context.user_data.get("history")
        prompt = f"Категория: {category}. Вопрос: {text}."
        answer = await ask_groq(prompt, history)
        add_to_history(context, text, answer)
        context.user_data.pop("question_category", None)
        await update.message.reply_text(answer, reply_markup=questions_keyboard)
        return

    # ── Свободный вопрос ──────────────────────────────────────────
    await update.message.reply_text("🔍 Ищу ответ...")
    history = context.user_data.get("history")
    answer = await ask_groq(text, history)
    add_to_history(context, text, answer)
    await update.message.reply_text(answer, reply_markup=main_menu)


# ========= ОБРАБОТЧИК ОШИБОК =========
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Exception while handling an update:", exc_info=context.error)


# ========= POST INIT — установка bot_data =========
async def post_init(app):
    app.bot_data["main_menu"] = main_menu


# ========= ЗАПУСК =========
def main():
    app = (
        ApplicationBuilder()
        .token(TELEGRAM_TOKEN)
        .post_init(post_init)
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(error_handler)

    logger.info("Bot started (model: %s)...", GROQ_MODEL)
    app.run_polling()


if __name__ == "__main__":
    main()
