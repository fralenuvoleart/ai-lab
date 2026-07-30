#!/usr/bin/env python3
"""Telegram ↔ Open WebUI bridge — calls Pipe agent for tool execution."""
import logging
import os
from collections import defaultdict
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from openai import OpenAI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OWUI_API_KEY = os.getenv("OWUI_API_KEY")
if not TELEGRAM_TOKEN:
    raise SystemExit("TELEGRAM_BOT_TOKEN not set. Check your .env file.")
if not OWUI_API_KEY:
    raise SystemExit("OWUI_API_KEY not set. Check your .env file.")
PIPE_MODEL = "telegram_agent_pipe"

OWUI_BASE_URL = os.getenv("OWUI_BASE_URL", "http://127.0.0.1:3000/api")
client = OpenAI(base_url=OWUI_BASE_URL, api_key=OWUI_API_KEY)
history: dict[int, list[dict]] = defaultdict(list)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    history[update.effective_chat.id] = []
    await update.message.reply_text("AI Lab bot ready.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_msg = update.message.text
    chat_id = update.effective_chat.id
    if chat_id not in history:
        history[chat_id] = []
    history[chat_id].append({"role": "user", "content": user_msg})
    if len(history[chat_id]) > 20:
        history[chat_id] = history[chat_id][-20:]
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")
    try:
        response = client.chat.completions.create(
            model=PIPE_MODEL, messages=list(history[chat_id]), stream=False,
            timeout=120.0,
        )
        reply = response.choices[0].message.content or ""
        history[chat_id].append({"role": "assistant", "content": reply})
        await update.message.reply_text(reply[:4000])
    except Exception as e:
        logger.error("Bot error for chat %s: %s", chat_id, e, exc_info=True)
        await update.message.reply_text("Sorry, something went wrong. Please try again.")

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()
