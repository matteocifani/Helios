#!/bin/bash
set -e

echo "=================================================="
echo "  🏠 HOUSE ANALYSIS PIPELINE - Setup"
echo "=================================================="

if ! command -v python3 &> /dev/null; then
    echo "❌ Errore: Python3 non trovato!"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python trovato: $PYTHON_VERSION"

echo ""
echo "1️⃣  Creazione ambiente virtuale..."
if [ -d ".venv" ]; then
    echo "   ℹ️  Ambiente virtuale esiste già"
else
    python3 -m venv .venv
    echo "   ✓ Ambiente creato"
fi

echo ""
echo "2️⃣  Attivazione ambiente virtuale..."
source .venv/bin/activate
echo "   ✓ Ambiente attivo"

echo ""
echo "3️⃣  Upgrade pip..."
pip install --upgrade pip setuptools wheel > /dev/null 2>&1
echo "   ✓ pip aggiornato"

echo ""
echo "4️⃣  Installazione dipendenze..."
pip install -r requirements.txt
echo "   ✓ Dipendenze installate"

echo ""
echo "5️⃣  Installazione browser Playwright..."
playwright install chromium
echo "   ✓ Chromium installato"

echo ""
echo "6️⃣  Verifica modello YOLOv8..."
if [ -f "Python/solar_panel_yolov8s.pt" ]; then
    echo "   ✓ Modello trovato"
else
    echo "   ⚠️  Modello sarà scaricato al primo utilizzo"
fi

echo ""
echo "7️⃣  Verifica .env..."
if [ -f ".env" ]; then
    echo "   ✓ File .env trovato"
else
    echo "   ⚠️  File .env non trovato - creare prima di eseguire"
fi

echo ""
echo "=================================================="
echo "  ✅ Setup Completato!"
echo "=================================================="
echo ""
echo "Esegui: python Python/house_analysis_pipeline.py \"Indirizzo\""
echo ""
