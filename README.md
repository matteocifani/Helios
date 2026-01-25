# HELIOS

**Piattaforma di Consulenza Assicurativa Aumentata dall'AI**

Generali AI Challenge 2026

---

## Panoramica

**Helios** trasforma il modo in cui gli agenti assicurativi analizzano clienti, valutano rischi e generano raccomandazioni commerciali. La piattaforma centralizza dati geospaziali, analytics avanzate e intelligenza artificiale generativa in un'unica interfaccia intelligente.

---

## Funzionalita Principali

### 1. Mappa Geo-Rischio Interattiva

Visualizzazione 3D di oltre 11.000 proprieta sul territorio italiano:

- **Heatmap del rischio** con colori intuitivi (verde=basso, rosso=critico)
- **Overlay zone sismiche INGV** (Zone 1-4)
- **Risk score composito** che combina:
  - Rischio sismico (classificazione INGV)
  - Rischio idrogeologico (frane, instabilita)
  - Rischio alluvionale (esondazioni)
- Filtri per citta, livello di rischio e zona sismica

### 2. Analytics Dashboard

Cruscotto analitico del portafoglio:

- Distribuzione del rischio nel portafoglio clienti
- Breakdown geo-rischio per tipologia
- Correlazione CLV vs Risk Score
- Probabilita di churn per prioritizzare la retention
- Top 10 citta per concentrazione di rischio

### 3. Ricerca e Profilo Cliente

Scheda cliente completa con:

- Dati anagrafici e demografici
- Customer Lifetime Value (CLV) e probabilita di abbandono
- Profilo di rischio della proprieta con score dettagliato
- Polizze attive con premi, scadenze e coperture
- Potenziale solare della proprieta (kWh/anno, risparmio, ROI)

### 4. Policy Advisor - Sistema NBO

Algoritmo di raccomandazione Next Best Offer:

- **Score ponderato**: Retention (50%) + Redditivita (30%) + Propensione (20%)
- **Top 20 opportunita** di cross-selling filtrate per eleggibilita
- **Top 5 clienti premium** per CLV
- Prodotti: NatCat, CasaSerena, FuturoSicuro, SaluteProtetta, GreenHome, Multiramo

---

## Iris: L'Assistente AI

**Iris** e il cuore intelligente di Helios - un assistente AI conversazionale sempre visibile nella sidebar, alimentato da Claude 3.5 Sonnet.

### Capabilities

| Funzione | Descrizione |
|----------|-------------|
| **Profilo Cliente** | Recupera dati demografici, eta, professione, reddito, CLV |
| **Stato Polizze** | Mostra polizze attive con dettagli su premi e scadenze |
| **Analisi Rischio** | Fornisce breakdown: sismico, idrogeologico, alluvionale |
| **Potenziale Solare** | Stima produzione kWh/anno, risparmio economico e ROI |
| **Preventivi** | Calcola premi mensili e annuali basati sul risk score |
| **Ricerca Storico** | Cerca nelle interazioni passate con semantic search |
| **Email Commerciali** | Genera comunicazioni personalizzate pronte all'uso |

### Esempio di Interazione

```
Utente: "Analizza il rischio per il cliente 9501 e dammi un preventivo NatCat"

Iris automaticamente:
1. Recupera il profilo del cliente
2. Calcola il risk assessment completo
3. Genera il preventivo personalizzato
4. Risponde con tutti i dati in formato chiaro
```

---

## Architettura

```
+---------------------------------------------------------------+
|                    FRONTEND (Streamlit)                       |
|  +----------+  +----------+  +----------+  +----------+       |
|  |  Mappa   |  |Analytics |  | Ricerca  |  |  Policy  |       |
|  | Pydeck   |  | Plotly   |  | Cliente  |  | Advisor  |       |
|  +----------+  +----------+  +----------+  +----------+       |
|                       +----------+                            |
|                       |   IRIS   | <- Sempre visibile         |
|                       |  Chat AI |                            |
|                       +----------+                            |
+---------------------------------------------------------------+
                            |
                            v
+---------------------------------------------------------------+
|                    BACKEND (Python)                           |
|  +------------------+  +------------------+                   |
|  |   Iris Engine    |  |   Data Utils     |                   |
|  |  Claude 3.5 API  |  |  Parallel Fetch  |                   |
|  |  7 Tools         |  |  Smart Caching   |                   |
|  +------------------+  +------------------+                   |
+---------------------------------------------------------------+
                            |
                            v
+---------------------------------------------------------------+
|                    DATABASE (Supabase)                        |
|  clienti | abitazioni | polizze | sinistri | interactions     |
+---------------------------------------------------------------+
```

---

## Stack Tecnologico

| Layer | Tecnologie |
|-------|------------|
| **Frontend** | Streamlit, Plotly, Pydeck, Mapbox |
| **AI** | Claude 3.5 Sonnet (OpenRouter), OpenAI Embeddings |
| **Database** | Supabase (PostgreSQL) con vector search |
| **Design** | Tema "Vita Sicura Light", palette Aurora Borealis |

---

## Struttura del Progetto

```
helios/
├── app.py                  # Entry point principale
├── src/
│   ├── config/
│   │   └── constants.py    # Costanti centralizzate
│   ├── data/
│   │   └── db_utils.py     # Gestione Supabase + caching
│   ├── iris/
│   │   ├── engine.py       # Core AI engine con tool calling
│   │   └── chat.py         # UI chat Streamlit
│   └── utils/
│       ├── ui.py           # Componenti UI custom
│       └── vision_analysis.py  # Analisi immagini satellitari
├── Data/
│   └── nbo_master.json     # Dataset raccomandazioni NBO
├── scripts/                # Script di utility
├── tests/                  # Test suite
├── docs/                   # Documentazione
└── Logo/                   # Asset branding
```

---

## Quick Start

### Requisiti

- Python 3.9+
- Chiavi API: Supabase, OpenRouter

### Installazione

```bash
# 1. Clona il repository
git clone https://github.com/tuo-username/helios.git
cd helios

# 2. Crea ambiente virtuale
python -m venv .venv
source .venv/bin/activate  # Mac/Linux
# .venv\Scripts\activate   # Windows

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

## Design System

**Tema**: Aurora Borealis meets Data Visualization

| Elemento | Colore |
|----------|--------|
| Primary | Aurora Teal `#00A0B0` |
| Accent | Electric Cyan `#00C9D4` |
| Secondary | Deep Navy `#1B3A5F` |
| Risk Critico | `#FF453A` |
| Risk Alto | `#FF9F0A` |
| Risk Medio | `#F59E0B` |
| Risk Basso | `#10B981` |

---

## Dati

| Dataset | Contenuto | Volume |
|---------|-----------|--------|
| **Clienti** | Anagrafica, CLV, churn, professione, reddito | 11.000+ |
| **Abitazioni** | Coordinate GPS, risk scores, zona sismica | 11.000+ |
| **Polizze** | Prodotto, premio, copertura, scadenza | Multipla |
| **NBO** | Raccomandazioni con componenti di score | 33MB |
| **Interactions** | Storico contatti con embeddings | Vector indexed |

---

## Licenza

Progetto sviluppato per Generali AI Challenge 2026.
