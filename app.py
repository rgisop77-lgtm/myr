
from flask import Flask
import threading
from bot import Bot

app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Bot is running fine on Render!"

def run_bot():
    Bot().run()

# Start bot in background
threading.Thread(target=run_bot, daemon=True).start()

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
