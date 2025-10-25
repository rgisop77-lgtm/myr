from flask import Flask
import threading
import os
import time
import logging
from bot import Bot  # import your bot class

app = Flask(__name__)

@app.route('/')
def home():
    return "✅ VJ Link Changer Bot is Running on Render!"

# Function to run the bot in a separate thread
def run_bot():
    try:
        Bot().run()
    except Exception as e:
        logging.error(f"Bot crashed: {e}")
        time.sleep(10)
        run_bot()  # auto-restart if bot crashes

# Start bot thread when app starts
bot_thread = threading.Thread(target=run_bot)
bot_thread.daemon = True
bot_thread.start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)


# 🌐 Flask App
flask_app = Flask(__name__)

@flask_app.route("/")
def home():
    return "❤️ Lovely Bot is Live!"

# Run Flask in background
def run():
    flask_app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

threading.Thread(target=run).start()

# 📁 Load conversation categories
with open("conversation.json", "r", encoding="utf-8") as f:
    categories = json.load(f)
all_replies = sum(categories.values(), [])
