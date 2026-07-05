# HIKMAH HUB — Islamic Encyclopedia Telegram Bot

## Project overview
A Telegram bot ([@hikmah_hub_bot](https://t.me/)) powered by Groq Llama 3.1 that acts as an Islamic encyclopedia. Users can browse 50 Islamic topics, all 114 Quran surahs, hadith books, and duas. The bot answers questions in Russian with Arabic text included.

## Stack
- **Python** — main language
- **python-telegram-bot 20.7** — Telegram Bot framework (async)
- **Groq API (Llama 3.1 8b-instant)** — AI responses
- **httpx** — async HTTP client for Groq calls

## How to run
```bash
python bot.py
```
The `Start application` workflow runs this automatically.

## Required secrets
| Secret | Where to get it |
|--------|----------------|
| `TELEGRAM_TOKEN` | @BotFather on Telegram → `/newbot` |
| `GROQ_API_KEY` | console.groq.com → API Keys |

## Project structure
| File | Purpose |
|------|---------|
| `bot.py` | All bot logic — handlers, menus, Groq integration |
| `requirements.txt` | Python dependencies |
| `README.md` | Russian-language project docs |

## User preferences
- Keep the existing project structure and language (Russian UI)
