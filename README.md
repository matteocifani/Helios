# ☀️ HELIOS - Geo-Cognitive Intelligence

**Piattaforma avanzata di consulenza assicurativa aumentata dall'AI**
Generali AI Challenge 2026

---

## 🌟 Overview

**Helios** è l'assistente intelligente per l'agente del futuro. La dashboard integra dati geospaziali, analitica avanzata e intelligenza artificiale generativa per trasformare il modo in cui gli agenti interagiscono con il loro portafoglio clienti.

La piattaforma combina la potenza di **Policy Advisor** con **Iris** (AI Advisor) per offrire raccomandazioni proattive e analisi del rischio iper-localizzate.

---

## ✨ Key Features

### 🤵 Policy Advisor
Il cuore pulsante dell'attività commerciale quotidiana.
- **Clienti Premium**: Identificazione automatica dei Top 5 clienti per valore (CLV) e potenziale di vendita.
- **Top 20 Opportunità**: Lista prioritaria di raccomandazioni "Next Best Offer" basate su algoritmi di propensione, ritenzione e redditività.
- **Schede Cliente Avanzate**: Vista a 360° con icone polizze intuitive, score di opportunità e analisi dei bisogni.

### 🗺️ Analytics & Geo-Rischio
Visualizzazione strategica del territorio emiliano-romagnolo.
- **Mappa Interattiva**: Analisi granulare del rischio (sismico, idrogeologico, alluvioni) su Bologna e provincia.
- **Distribuzione Portafoglio**: Heatmap della concentrazione clienti e premi.
- **Filtri Regionali**: Focus automatico sull'Emilia Romagna per una gestione territoriale efficiente.

### 🤖 Iris AI Assistant
Il copilota virtuale sempre disponibile.
- **Chat Interattiva**: Analisi del portafoglio in linguaggio naturale.
- **Supporto Decisionale**: Suggerimenti in tempo reale basati sui dati del cliente e del territorio.

---

## 🎨 Design System: "Aurora Borealis"

L'interfaccia utilizza un linguaggio visivo moderno e fluido, ispirato ai colori dell'aurora e della tecnologia affidabile.

- **Primary**: `Aurora Teal` (#00A0B0) to `Electric Cyan` (#00C9D4)
- **Secondary**: `Deep Navy` (#1B3A5F)
- **Risk Palette**:
  - 🔴 Critico: `#FF453A`
  - 🟠 Alto: `#FF9F0A`
  - 🟡 Medio: `#F59E0B`
  - 🟢 Basso: `#10B981`

---

## 🚀 Quick Start

### Requisiti
- Python 3.9+
- Chiavi API per Supabase e OpenRouter (LLM)

### Installazione

```bash
# 1. Clona il repository
git clone https://github.com/tuo-username/helios-dashboard.git
cd helios-dashboard

# 2. Crea ambiente virtuale
python -m venv .venv
source .venv/bin/activate  # Mac/Linux
# .venv\Scripts\activate  # Windows

# 3. Installa dipendenze
pip install -r requirements.txt

# 4. Configura variabili d'ambiente
cp .env.template .env
# Edita .env con le tue credenziali
```

### Avvio

```bash
streamlit run app.py
```

---

## 📁 Struttura del Progetto

```
helios/
├── app.py                  # Main Application Entry Point
├── src/
│   ├── config/            # Costanti (Icone, Palette, Mapping)
│   ├── data/              # Gestione Dati e Connessione DB
│   └── iris/              # Modulo AI Assistant
├── Data/                  # Dataset locali (CSV/GeoJSON)
├── .env.template          # Template configurazione
└── requirements.txt       # Dipendenze Python
```

---

**Sviluppato con ❤️ per Generali AI Challenge**
