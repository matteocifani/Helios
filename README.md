# ☀️ Progetto Helios - FluidView Dashboard

**Ecosistema Assicurativo Geo-Cognitivo** | Generali AI Challenge 2024

---

## 🌟 Overview

**FluidView** è la dashboard interattiva del Progetto Helios, un ecosistema assicurativo geo-cognitivo che integra:

- 🛰️ **SkyGuard**: Intelligence geospaziale con dati INGV/ISPRA
- 🤖 **Iris**: Intelligent Advisor powered by AI
- 📊 **Analytics**: Visualizzazioni avanzate del portafoglio rischio

---

## ✨ Features

| Feature | Descrizione |
|---------|-------------|
| 🗺️ **Mappa Geo-Rischio** | Visualizzazione 3D con PyDeck, heatmap, tooltip interattivi |
| 📊 **Analytics** | Distribuzione rischio, zone sismiche, idrogeologico, CLV vs Risk |
| 🔍 **Ricerca Clienti** | Full-text search, filtri avanzati, card dettaglio |
| 🤖 **Iris Chat** | Interfaccia conversazionale AI per analisi e preventivi |

---

## 🚀 Quick Start

### Installazione Locale

```bash
# Installa dipendenze
pip install -r requirements.txt

# Configura ambiente
cp .env.template .env
# Modifica .env con le tue credenziali Supabase e OpenRouter

# Avvia dashboard
streamlit run app.py
```

### Docker Deployment

```bash
docker compose up -d --build
```

---

## ⚙️ Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `SUPABASE_URL` | URL progetto Supabase | ✅ |
| `SUPABASE_KEY` | Chiave anon Supabase | ✅ |
| `OPENROUTER_API_KEY` | API Key per Iris AI | ✅ |
| `MAPBOX_TOKEN` | Token Mapbox (mappe avanzate) | ❌ |

---

## 🎨 Design System

**Palette "Aurora Borealis":**
- Helios Sun: `#FF6B35`
- Aurora Cyan: `#00E5CC`
- Deep Space: `#0D1117`

**Risk Colors:**
- 🔴 Critico: `#FF453A`
- 🟠 Alto: `#FF9F0A`
- 🟡 Medio: `#FFD60A`
- 🟢 Basso: `#30D158`

---

## 📁 Structure

```
helios_dashboard/
├── app.py              # Main Streamlit app
├── src/
│   ├── iris/           # Iris AI module
│   ├── config/         # Constants
│   └── data/           # Data utilities
├── requirements.txt    # Dependencies
├── Dockerfile          
├── docker-compose.yml  
└── .env.template       
```

---

**Built with ❤️ for Generali AI Challenge 2024**

