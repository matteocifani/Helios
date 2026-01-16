#!/bin/bash

# Script per riavviare Streamlit con reload forzato dei moduli

echo "🛑 Stopping all Streamlit processes..."
pkill -9 streamlit 2>/dev/null

echo "🧹 Cleaning Python cache..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete 2>/dev/null

# Clear Streamlit cache
echo "🗑️  Clearing Streamlit cache..."
rm -rf ~/.streamlit/cache 2>/dev/null

echo "🔄 Running force reload script..."
python3 force_reload.py

echo "⏳ Waiting 2 seconds..."
sleep 2

echo "🚀 Starting Streamlit..."
streamlit run app.py

