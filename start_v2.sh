#!/bin/bash

# Start Streamlit with V2 engine - FRESH START

cd "/Users/matteocifani/Documents/AI Challenge Generali/Streamlit App"

echo "🛑 Killing ALL processes..."
pkill -9 streamlit 2>/dev/null
pkill -9 -f "streamlit run" 2>/dev/null
pkill -9 -f "Python.*app.py" 2>/dev/null
sleep 2

echo "🧹 Deep cleaning..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete 2>/dev/null
rm -rf ~/.streamlit 2>/dev/null
rm -rf .streamlit 2>/dev/null

echo "✅ Clean complete"
echo ""
echo "🚀 Starting Streamlit with V2 engine..."
echo "   Engine: ada_engine_v2.py"
echo "   Python: .venv/bin/python3"
echo ""

# Launch with venv Python
.venv/bin/python3 -m streamlit run app.py

