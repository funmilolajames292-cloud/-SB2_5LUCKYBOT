import os
import logging
import random
import requests
from flask import Flask, request

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
RAILWAY_URL = os.environ.get("RAILWAY_PUBLIC_DOMAIN")
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "sb2luckysecret")

if not BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN is missing!")

API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)


def send_message(chat_id, text, reply_markup=None):
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    try:
        requests.post(f"{API_URL}/sendMessage", json=payload, timeout=10)
    except Exception as e:
        logger.error(f"send_message error: {e}")


def menu():
    return {
        "inline_keyboard": [
            [{"text": "🎲 Roll Lucky Number", "callback_data": "lucky"}],
            [{"text": "🎁 Daily Bonus", "callback_data": "bonus"}],
            [{"text": "📊 My Stats", "callback_data": "stats"}],
            [{"text": "ℹ️ About", "callback_data": "about"}],
        ]
    }


def handle_start(chat_id, name):
    send_message(chat_id,
        f"👋 <b>Welcome, {name}!</b>\n\nI'm <b>SB2_5LUCKYBOT</b> 🍀\nWhat do you want to do?",
        menu())


def handle_lucky(chat_id):
    n = random.randint(1, 100)
    luck = random.choice(["🍀 Very Lucky!", "✨ Lucky!", "😐 Neutral", "💀 Not lucky today..."])
    send_message(chat_id, f"🎲 <b>Your lucky number:</b> <code>{n}</code>\n{luck}", menu())


def handle_bonus(chat_id):
    pts = random.randint(5, 50)
    send_message(chat_id, f"🎁 <b>Daily Bonus!</b>\n\nYou earned <b>{pts}</b> lucky points!", menu())


def handle_stats(chat_id):
    send_message(chat_id, "📊 <b>Your Stats</b>\n\nRolls: —\nPoints: —\nStreak: —", menu())


def handle_about(chat_id):
    send_message(chat_id, "ℹ️ <b>SB2_5LUCKYBOT</b>\n\nA fun lucky-number bot built with Python + Flask on Railway.")


def handle_update(update):
    try:
        if "message" in update:
            msg = update["message"]
            chat_id = msg["chat"]["id"]
            text = msg.get("text", "")
            name = msg.get("from", {}).get("first_name", "friend")

            if text.startswith("/start"): handle_start(chat_id, name)
            elif text.startswith("/lucky"): handle_lucky(chat_id)
            elif text.startswith("/bonus"): handle_bonus(chat_id)
            elif text.startswith("/stats"): handle_stats(chat_id)
            elif text.startswith("/about"): handle_about(chat_id)
            elif text.startswith("/help"):
                send_message(chat_id, "/start /lucky /bonus /stats /about", menu())
            else:
                send_message(chat_id, "🤔 Unknown. Try /help", menu())

        elif "callback_query" in update:
            cb = update["callback_query"]
            chat_id = cb["message"]["chat"]["id"]
            data = cb["data"]
            requests.post(f"{API_URL}/answerCallbackQuery",
                          json={"callback_query_id": cb["id"]}, timeout=5)
            if data == "lucky": handle_lucky(chat_id)
            elif data == "bonus": handle_bonus(chat_id)
            elif data == "stats": handle_stats(chat_id)
            elif data == "about": handle_about(chat_id)
    except Exception as e:
        logger.exception(f"Error: {e}")


@app.route(f"/webhook/{WEBHOOK_SECRET}", methods=["POST"])
def webhook():
    handle_update(request.get_json(force=True))
    return "OK", 200


@app.route("/", methods=["GET"])
def index():
    return "SB2_5LUCKYBOT is running ✅", 200


def set_webhook():
    if not RAILWAY_URL:
        logger.warning("RAILWAY_PUBLIC_DOMAIN not set")
        return
    url = f"https://{RAILWAY_URL}/webhook/{WEBHOOK_SECRET}"
    try:
        r = requests.post(f"{API_URL}/setWebhook",
                          json={"url": url, "drop_pending_updates": True}, timeout=10)
        logger.info(f"Webhook: {r.json()}")
    except Exception as e:
        logger.error(f"Webhook failed: {e}")


set_webhook()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
