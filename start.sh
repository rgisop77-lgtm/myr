#!/usr/bin/env bash
# start.sh
# Run bot + web server together for Render

echo "Starting VJ Link Changer Bot & Web Server..."

# Start the bot (long polling) in background
python3 bot.py &

# Start Flask app via Gunicorn on Render's PORT
exec gunicorn --bind 0.0.0.0:$PORT app:app --workers 1
