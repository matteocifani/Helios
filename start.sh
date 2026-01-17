#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# HELIOS START SCRIPT - Consolidated
# ═══════════════════════════════════════════════════════════════════════════════

cd "$(dirname "$0")"

echo "═══════════════════════════════════════════════════════════════════════════════"
echo "                         🌞 PROGETTO HELIOS"
echo "                   Ecosistema Assicurativo Geo-Cognitivo"
echo "═══════════════════════════════════════════════════════════════════════════════"

# Clean Python cache
echo ""
echo "🧹 Cleaning Python caches..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete 2>/dev/null

# Clean Streamlit cache
echo "🧹 Cleaning Streamlit cache..."
rm -rf ~/.streamlit/cache 2>/dev/null

echo ""
echo "🚀 Starting Helios Dashboard..."
echo ""

# Start with virtual environment if available
if [ -d ".venv" ]; then
    echo "📦 Using virtual environment..."
    .venv/bin/python -m streamlit run app.py
else
    echo "📦 Using system Python..."
    streamlit run app.py
fi
