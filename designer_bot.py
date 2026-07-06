import requests
from telegram import ReplyKeyboardMarkup

# -----------------------------
# СТРОГИЕ ПРАВИЛА БОТА
# -----------------------------

ALLOWED_TOPICS = {
    "История Пророка",
    "Фикх",
    "Дуа",
    "Хадисы",
    "Исламские термины"
}

CACHE = {}  # один вопрос → один ответ


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

    # Разделы из Groq
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
# GROQ — строгий исламский режим
# -----------------------------

def ask_groq(prompt, api_key, model):
    url = "https://api.groq.com/openai/v1/chat/completions"

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
                    "[AYAT] — аят (арабский текст + русский + таджикский)\n"
                    "[HADITH] — хадис (арабский текст + русский + таджикский)\n"
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
        resp = requests.post(url, headers=headers, json=data, timeout=30)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
    except Exception:
        return "Ошибка при обращении к исламской энциклопедии."


# -----------------------------
# ОСНОВНАЯ ФУНКЦИЯ МОДУЛЯ
# -----------------------------

async def handle_designer_message(update, context, api_key, model):
    text = (update.message.text or "").strip()

    # Назад — всегда работает
    if text == "Назад":
        context.user_data.clear()
        await update.message.reply_text(
            "🔙 Вы вернулись в главное меню.",
            reply_markup=context.bot_data["main_menu"]
        )
        return

    # Один и тот же вопрос → один и тот же ответ
    if text in CACHE:
        await update.message.reply_text(CACHE[text], parse_mode="Markdown")
        return

    # Если человек пишет что-то своё (не кнопка меню)
    if text not in ALLOWED_TOPICS and not context.user_data.get("designer_topic"):
        await update.message.reply_text(
            "❗ Этот бот — исламская энциклопедия.\n"
            "Он отвечает только по темам из меню: история Пророка, фикх, дуа, хадисы, исламские термины.\n"
            "Пожалуйста, выберите тему из меню."
        )
        return

    # -----------------------------
    # ИСТОРИЯ ПРОРОКА
    # -----------------------------
    if text == "История Пророка":
        options = ["1. Рождение и ранние годы", "2. Мекканский период", "3. Мединский период"]

        answer = ask_groq(
            "История Пророка: дай краткое описание трёх периодов.",
            api_key, model
        )

        formatted = format_answer("История Пророка", options, answer)
        CACHE[text] = formatted
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
            answer = ask_groq(prompt, api_key, model)
            formatted = format_answer(title, None, answer)
            CACHE[text] = formatted
            await update.message.reply_text(formatted, parse_mode="Markdown")
            return

    # -----------------------------
    # ФИКХ
    # -----------------------------
    if text == "Фикх":
        options = ["1. Тахарат", "2. Намаз", "3. Пост"]

        answer = ask_groq("Фикх: дай краткое описание тахарата, намаза, поста.", api_key, model)
        formatted = format_answer("Фикх", options, answer)
        CACHE[text] = formatted
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
            answer = ask_groq(prompt, api_key, model)
            formatted = format_answer(title, None, answer)
            CACHE[text] = formatted
            await update.message.reply_text(formatted, parse_mode="Markdown")
            return

    # -----------------------------
    # ДУА
    # -----------------------------
    if text == "Дуа":
        options = ["1. Утренние", "2. Вечерние", "3. Перед намазом", "4. После намаза"]

        answer = ask_groq("Дуа: дай краткое описание категорий дуа.", api_key, model)
        formatted = format_answer("Дуа", options, answer)
        CACHE[text] = formatted
        await update.message.reply_text(formatted, parse_mode="Markdown")

        context.user_data["designer_topic"] = "dua"
        return

    if context.user_data.get("designer_topic") == "dua":
        mapping = {
            "1": ("Утренние дуа", "Подробно объясни утренние дуа."),
            "2": ("Вечерние дуа", "Подробно объясни вечерние дуа."),
            "3": ("Дуа перед намазом", "Подробно объясни дуа перед намазом."),
            "4": ("Дуа после намаза", "Подробно объясни дуа после намаза.")
        }

        if text in mapping:
            title, prompt = mapping[text]
            answer = ask_groq(prompt, api_key, model)
            formatted = format_answer(title, None, answer)
            CACHE[text] = formatted
            await update.message.reply_text(formatted, parse_mode="Markdown")
            return

    # -----------------------------
    # ХАДИСЫ
    # -----------------------------
    if text == "Хадисы":
        options = ["1. О намазе", "2. О ду‘а", "3. О нраве"]

        answer = ask_groq("Хадисы: дай краткое описание категорий хадисов.", api_key, model)
        formatted = format_answer("Хадисы", options, answer)
        CACHE[text] = formatted
        await update.message.reply_text(formatted, parse_mode="Markdown")

        context.user_data["designer_topic"] = "hadith"
        return

    if context.user_data.get("designer_topic") == "hadith":
        mapping = {
            "1": ("Хадисы о намазе", "Подробно объясни хадисы о намазе."),
            "2": ("Хадисы о ду‘а", "Подробно объясни хадисы о ду‘а."),
            "3": ("Хадисы о нраве", "Подробно объясни хадисы о нраве.")
        }

        if text in mapping:
            title, prompt = mapping[text]
            answer = ask_groq(prompt, api_key, model)
            formatted = format_answer(title, None, answer)
            CACHE[text] = formatted
            await update.message.reply_text(formatted, parse_mode="Markdown")
            return

    # -----------------------------
    # ИСЛАМСКИЕ ТЕРМИНЫ
    # -----------------------------
    if text == "Исламские термины":
        await update.message.reply_text("Введите исламский термин.")
        context.user_data["designer_topic"] = "terms"
        return

    if context.user_data.get("designer_topic") == "terms":
        prompt = (
            f"Исламский термин: {text}. "
            f"Дай определение: арабский, русский, таджикский, пример применения."
        )
        answer = ask_groq(prompt, api_key, model)
        formatted = format_answer(f"Термин: {text}", None, answer)
        CACHE[text] = formatted
        await update.message.reply_text(formatted, parse_mode="Markdown")
        return

    return
