import os
import requests
from flask import Flask, request

BOT_TOKEN = os.environ.get("BOT_TOKEN")
API_BASE_URL = os.environ.get("DATA_API_URL")  # শুধু base URL
WEBHOOK_URL = f"https://nid-server-bot.onrender.com/{BOT_TOKEN}"
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/"

app = Flask(__name__)
user_state = {}

def send_message(chat_id, text, buttons=None):
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    if buttons:
        payload["reply_markup"] = {"inline_keyboard": buttons}
    requests.post(TELEGRAM_API_URL + "sendMessage", json=payload)

def fetch_data(nid, dob):
    try:
        params = {"nid": nid, "dob": dob}  # ইউজারের ইনপুট
        res = requests.get(API_BASE_URL, params=params, timeout=10)
        if res.status_code == 200:
            return res.text
        else:
            return "❌ API তে সমস্যা হয়েছে বা ডেটা পাওয়া যায়নি।"
    except Exception as e:
        return f"⚠ Exception: {e}"

@app.route("/")
def home():
    return "🤖 NID Data Bot Running!"

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = request.get_json()
    if "message" in update:
        msg = update["message"]
        chat_id = msg["chat"]["id"]
        text = msg.get("text", "")

        if text == "/start":
            buttons = [[{"text": "📄 Check NID", "callback_data": "check_nid"}]]
            send_message(chat_id, "🌟 *NID Data Bot*\n\nবাটন ক্লিক করে ডেটা চেক করুন:", buttons)

    elif "callback_query" in update:
        query = update["callback_query"]
        chat_id = query["message"]["chat"]["id"]
        data = query["data"]
        if data == "check_nid":
            send_message(chat_id, "📲 দয়া করে আপনার *NID* লিখুন:")
            user_state[chat_id] = {"step": "awaiting_nid"}

    if "message" in update:
        msg = update["message"]
        chat_id = msg["chat"]["id"]
        text = msg.get("text", "")

        if chat_id in user_state:
            step = user_state[chat_id].get("step")
            if step == "awaiting_nid":
                user_state[chat_id]["nid"] = text
                user_state[chat_id]["step"] = "awaiting_dob"
                send_message(chat_id, "📅 এখন আপনার *Date of Birth* লিখুন (YYYY-MM-DD):")
            elif step == "awaiting_dob":
                nid = user_state[chat_id]["nid"]
                dob = text
                result = fetch_data(nid, dob)
                send_message(chat_id, f"📄 *ফলাফল:*\n{result}")
                user_state.pop(chat_id, None)

    return "ok"

def set_webhook():
    res = requests.get(TELEGRAM_API_URL + "setWebhook", params={"url": WEBHOOK_URL})
    print("Webhook setup response:", res.json())

if __name__ == "__main__":
    set_webhook()
    port = int(os.environ.get("PORT", 5000))

    app.run(host="0.0.0.0", port=port)
