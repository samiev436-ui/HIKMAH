import httpx
from telegram import ReplyKeyboardMarkup

# -----------------------------
# СТРОГИЕ ПРАВИЛА БОТА
# -----------------------------

ALLOWED_TOPICS = {
    "История Пророка",
    "Фикх",
    "Исламские термины"
}

CACHE = {}  # один вопрос → один ответ

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


# -----------------------------
# СТИЛЬ: БОЛЬШАЯ ИСЛАМСКАЯ КНИГА
# -----------------------------

def format_answer(title, options, content):
    block = (
        f"📚 *{title}*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"﴿ بسم الله الرحمن الرحيم ﴾\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    )

    if options:
        block += (
            "🔸 *Оглавление раздела:* 🔸\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
        )
        for opt in options:
            block += f"▫️ {opt}\n"
        block += "\n"

    ayat = content.split("[AYAT]")[-1].split("[HADITH]")[0].strip()
    hadith = content.split("[HADITH]")[-1].split("[TAFSIR]")[0].strip()
    tafsir = content.split("[TAFSIR]")[-1].split("[HISTORY]")[0].strip()
    history = content.split("[HISTORY]")[-1].split("[PRACTICE]")[0].strip()
    practice = content.split("[PRACTICE]")[-1].strip()

    block += (
        "📖 *Аят:* \n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"{ayat}\n\n"
        "📖 *Хадис:* \n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"{hadith}\n\n"
        "📖 *Толкование учёных:* \n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"{tafsir}\n\n"
        "📖 *Исторический контекст:* \n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"{history}\n\n"
        "📖 *Практическое применение:* \n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"{practice}\n\n"
    )

    block += (
        "🔙 *Назад*\n"
        "📘 *HIKMAH HUB — Исламская энциклопедия*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )

    return block


# -----------------------------
# GROQ — async исламский режим
# -----------------------------

async def ask_groq_designer(prompt, api_key, model):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    data = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Ты — исламская энциклопедия. "
                    "Отвечай строго по исламским темам: история Пророка, фикх, дуа, хадисы, исламские термины. "
                    "Если вопрос вне этих тем — кратко объясни, что бот отвечает только по исламским знаниям. "
                    "Не фантазируй. Не придумывай. Пиши строго по факту.\n\n"
                    "Структура ответа:\n"
                    "[AYAT] — аят (арабский текст + русский)\n"
                    "[HADITH] — хадис (арабский текст + русский)\n"
                    "[TAFSIR] — толкование учёных\n"
                    "[HISTORY] — исторический контекст\n"
                    "[PRACTICE] — практическое применение"
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.2,
        "max_tokens": 2000
    }

    try:
        async with httpx.AsyncClient(timeout=40) as client:
            resp = await client.post(GROQ_URL, headers=headers, json=data)
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]
    except Exception:
        return "Ошибка при обращении к исламской энциклопедии."


# -----------------------------
# ОСНОВНАЯ ФУНКЦИЯ МОДУЛЯ
# -----------------------------

async def handle_designer_message(update, context, api_key, model):
    text = (update.message.text or "").strip()
    main_menu = context.bot_data.get("main_menu")

    # Назад — всегда работает
    if text in ("Назад", "🔙 Назад", "🏠 Главное меню"):
        context.user_data.clear()
        await update.message.reply_text(
            "🔙 Вы вернулись в главное меню.",
            reply_markup=main_menu
        )
        return

    # Кэш — ключ включает активную тему, чтобы не перепутать ответы
    cache_key = f"{context.user_data.get('designer_topic', '')}:{text}"
    if cache_key in CACHE:
        await update.message.reply_text(CACHE[cache_key], parse_mode="Markdown")
        return

    # Если пишет что-то не из меню и нет активной темы
    if text not in ALLOWED_TOPICS and not context.user_data.get("designer_topic"):
        await update.message.reply_text(
            "❗ Этот бот — исламская энциклопедия.\n"
            "Он отвечает только по темам из меню: история Пророка, фикх, дуа, хадисы, исламские термины.\n"
            "Пожалуйста, выберите тему из меню."
        )
        return

    # История Пророка
    if text == "История Пророка":
        options = ["1. Рождение и ранние годы", "2. Мекканский период", "3. Мединский период"]
        answer = await ask_groq_designer("История Пророка: дай краткое описание трёх периодов.", api_key, model)
        formatted = format_answer("История Пророка", options, answer)
        CACHE[cache_key] = formatted
        await update.message.reply_text(formatted, parse_mode="Markdown")
        context.user_data["designer_topic"] = "seerah"
        return

    if context.user_data.get("designer_topic") == "seerah":
        mapping = {
            "1": ("Рождение и ранние годы", "Подробно объясни рождение и ранние годы Пророка."),
            "2": ("Мекканский период", "Подробно объясни мекканский период."),
            "3": ("Мединский период", "Подробно объясни мединский период.")
        }
        if text in mapping:
            title, prompt = mapping[text]
            answer = await ask_groq_designer(prompt, api_key, model)
            formatted = format_answer(title, None, answer)
            CACHE[cache_key] = formatted
            await update.message.reply_text(formatted, parse_mode="Markdown")
            return

    # Фикх
    if text == "Фикх":
        options = ["1. Тахарат", "2. Намаз", "3. Пост"]
        answer = await ask_groq_designer("Фикх: дай краткое описание тахарата, намаза, поста.", api_key, model)
        formatted = format_answer("Фикх", options, answer)
        CACHE[cache_key] = formatted
        await update.message.reply_text(formatted, parse_mode="Markdown")
        context.user_data["designer_topic"] = "fiqh"
        return

    if context.user_data.get("designer_topic") == "fiqh":
        mapping = {
            "1": ("Тахарат", "Подробно объясни тахарат."),
            "2": ("Намаз", "Подробно объясни намаз."),
            "3": ("Пост", "Подробно объясни пост.")
        }
        if text in mapping:
            title, prompt = mapping[text]
            answer = await ask_groq_designer(prompt, api_key, model)
            formatted = format_answer(title, None, answer)
            CACHE[cache_key] = formatted
            await update.message.reply_text(formatted, parse_mode="Markdown")
            return

    # Исламские термины
    if text == "Исламские термины":
        await update.message.reply_text("Введите исламский термин.")
        context.user_data["designer_topic"] = "terms"
        return

    if context.user_data.get("designer_topic") == "terms":
        prompt = (
            f"Исламский термин: {text}. "
            f"Дай определение: арабский, русский, пример применения."
        )
        answer = await ask_groq_designer(prompt, api_key, model)
        formatted = format_answer(f"Термин: {text}", None, answer)
        CACHE[cache_key] = formatted
        await update.message.reply_text(formatted, parse_mode="Markdown")
        return
