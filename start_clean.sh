#!/bin/bash

# Ultra clean restart con virtualenv esplicito

cd "/Users/matteocifani/Documents/AI Challenge Generali/Streamlit App"

echo "🛑 Killing ALL Streamlit processes..."
pkill -9 streamlit 2>/dev/null
pkill -9 Python 2>/dev/null
sleep 1

echo "🧹 Cleaning ALL caches..."
# Python cache
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete 2>/dev/null

# Streamlit cache
rm -rf ~/.streamlit 2>/dev/null
rm -rf .streamlit 2>/dev/null

# pip cache
.venv/bin/python3 -m pip cache purge 2>/dev/null

echo "✅ All caches cleared"
echo ""
echo "⏳ Waiting 3 seconds..."
sleep 3

echo "🚀 Starting Streamlit with venv Python..."
echo "   Using: .venv/bin/python3"
echo ""

# Usa ESPLICITAMENTE il Python del venv
.venv/bin/python3 -m streamlit run app.py --server.fileWatcherType none
