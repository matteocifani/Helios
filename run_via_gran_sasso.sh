#!/bin/bash
set -e

# Script per eseguire la pipeline per: Via Gran Sasso 46, Arcore
# Uso: ./run_via_gran_sasso.sh

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

# Attiva virtualenv
if [ -f ".venv/bin/activate" ]; then
  source .venv/bin/activate
else
  echo ".venv non trovato. Esegui ./setup.sh prima di eseguire questo script."
  exit 1
fi

# Verifica .env
if [ ! -f ".env" ] || ! grep -q "OPENROUTER_API_KEY" .env 2>/dev/null; then
  echo "ERROR: .env con OPENROUTER_API_KEY non trovato. Crea .env nella root con la chiave OpenRouter."
  exit 1
fi

# Assicura che il modello YOLO sia presente (scarica se necessario)
python3 Python/ensure_model.py

# Lancia la pipeline
python3 Python/house_analysis_pipeline.py "Via Gran Sasso 46 Arcore"
