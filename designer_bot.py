import requests
from telegram import ReplyKeyboardMarkup

# -----------------------------
# ДИЗАЙНЕРСКИЙ ФОРМАТ ОТВЕТА
# -----------------------------

def format_answer(title, options, content):
    block = f"📘 *{title}*\n\n"

    if options:
        block += "Выберите один из вариантов ниже:\n\n"
        for opt in options:
            block += f"▫️ {opt}\n"
        block += "\n"

    block += "━━━━━━━━━━━━━━━━━━━━\n"
    block += f"{content}\n"
    block += "━━━━━━━━━━━━━━━━━━━━\n\n"
    block += "🔁 Чтобы вернуться назад — нажмите *Назад*."

    return block


# -----------------------------
# GROQ — строгий режим
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
                    "Ты — строгая исламская энциклопедия. "
                    "Отвечай как книга. Не фантазируй. "
                    "Пиши грамотно, без ошибок. "
                    "Каждый ответ должен содержать:\n"
                    "- арабский текст\n"
                    "- русский тафсир\n"
                    "- таджикский тафсир\n"
                    "- арабский хадис\n"
                    "- русское объяснение\n"
                    "- таджикское объяснение\n"
                    "- практику на русском\n"
                    "- практику на таджикском"
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.2,
        "max_tokens": 1500
    }

    try:
        resp = requests.post(url, headers=headers, json=data, timeout=30)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
    except Exception:
        return "Ошибка при обращении к энциклопедии."


# -----------------------------
# ОСНОВНАЯ ФУНКЦИЯ МОДУЛЯ
# -----------------------------

async def handle_designer_message(update, context, api_key, model):
    text = (update.message.text or "").strip()

    # Назад
    if text == "Назад":
        await update.message.reply_text("Главное меню:", reply_markup=context.bot_data["main_menu"])
        context.user_data.clear()
        return

    # История Пророка — главный выбор
    if text == "История Пророка":
        options = [
            "1. Рождение и ранние годы",
            "2. Мекканский период",
            "3. Мединский период"
        ]

        answer = ask_groq(
            "Дай краткое описание трёх периодов жизни Пророка "
            "на русском и таджикском.",
            api_key,
            model
        )

        formatted = format_answer("История Пророка", options, answer)
        await update.message.reply_text(formatted, parse_mode="Markdown")

        context.user_data["designer_topic"] = "seerah"
        return

    # Подтемы Истории Пророка
    if context.user_data.get("designer_topic") == "seerah":
        if text == "1":
            title = "Рождение и ранние годы"
            prompt = "Подробно объясни: Рождение и ранние годы Пророка."
        elif text == "2":
            title = "Мекканский период"
            prompt = "Подробно объясни: Мекканский период."
        elif text == "3":
            title = "Мединский период"
            prompt = "Подробно объясни: Мединский период."
        else:
            return

        answer = ask_groq(prompt, api_key, model)
        formatted = format_answer(title, None, answer)
        await update.message.reply_text(formatted, parse_mode="Markdown")
        return

    # Если текст не относится к модулю — игнорируем
    return
