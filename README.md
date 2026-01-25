# HELIOS

**Piattaforma di Consulenza Assicurativa Aumentata dall'AI**

Generali AI Challenge 2026

---

## Indice

- [Panoramica](#panoramica)
- [Architettura](#architettura)
- [Funzionalita](#funzionalita)
- [Iris AI Assistant](#iris-ai-assistant)
- [Database Schema](#database-schema)
- [Installazione](#installazione)
- [Configurazione](#configurazione)
- [Struttura Progetto](#struttura-progetto)
- [Scripts Disponibili](#scripts-disponibili)
- [Guida Sviluppatore](#guida-sviluppatore)
- [Troubleshooting](#troubleshooting)

---

## Panoramica

Helios trasforma il modo in cui gli agenti assicurativi analizzano clienti, valutano rischi geografici e generano raccomandazioni commerciali. La piattaforma integra:

- **Geo-cognitive analytics**: rischi sismici, idrogeologici e alluvionali su mappa 3D
- **Next Best Offer (NBO)**: algoritmo di raccomandazione con scoring pesato
- **Iris**: assistente AI conversazionale con accesso real-time ai dati
- **Vision AI**: analisi satellitare delle proprieta

### Stack Tecnologico

| Layer | Tecnologia |
|-------|------------|
| Frontend | Streamlit |
| Database | Supabase (PostgreSQL) |
| AI Engine | Claude 3.5 Sonnet via OpenRouter |
| Maps | Pydeck + Mapbox |
| Charts | Plotly |
| Container | Docker |

### Dati

- **11.200 clienti** con anagrafica, CLV, churn probability
- **11.200 abitazioni** con coordinate, risk score, zona sismica
- **Polizze** con premi, scadenze, coperture
- **Interazioni** con embeddings per semantic search

---

## Architettura

```
+-----------------------------------------------------------------------+
|                         FRONTEND (Streamlit)                          |
+-----------------------------------------------------------------------+
|  +-------------+  +-------------+  +---------------+  +-------------+ |
|  |   Geo-Map   |  |  Analytics  |  | Client Detail |  |   Policy    | |
|  |   Pydeck    |  |   Plotly    |  |     HTML      |  |   Advisor   | |
|  +-------------+  +-------------+  +---------------+  +-------------+ |
|                                                                       |
|  +-------------------------------------------------------------------+|
|  |                    IRIS SIDEBAR (sempre visibile)                 ||
|  |  7 Tools: Profile | Policies | Risk | Solar | RAG | Premium | DB  ||
|  +-------------------------------------------------------------------+|
+-----------------------------------------------------------------------+
                                  |
                                  v
                    +---------------------------+
                    |      OpenRouter API       |
                    |   Claude 3.5 Sonnet       |
                    |   + OpenAI Embeddings     |
                    +---------------------------+
                                  |
                                  v
                    +---------------------------+
                    |    Supabase PostgreSQL    |
                    |  - clienti (11,200)       |
                    |  - abitazioni (11,200)    |
                    |  - polizze                |
                    |  - sinistri               |
                    |  - interactions (RAG)     |
                    +---------------------------+
```

### Flusso Dati

1. **Caricamento**: fetch parallelo di abitazioni e clienti con chunking
2. **Merge**: unione su `codice_cliente` per dataset unificato
3. **Caching**: TTL 30 minuti per dati principali
4. **Visualizzazione**: rendering asincrono di mappa e grafici
5. **NBO**: scoring da file JSON locale (33MB)

---

## Funzionalita

### 1. Policy Advisor (NBO Engine)

Dashboard principale per l'attivita commerciale quotidiana.

**Algoritmo di Scoring:**
```
Score = (Retention × 0.50) + (Redditivita × 0.30) + (Propensione × 0.20)
```

**Output:**
- Top 5 clienti premium (cards dettagliate)
- Leaderboard posizioni 6-25 (tabella compatta)
- Filtro automatico clienti gia contattati negli ultimi 5-30 giorni

**Prodotti Raccomandati:**
- NatCat (terremoti + alluvioni)
- CasaSerena (casa + contenuto)
- FuturoSicuro (vita + investimento)
- SaluteProtetta (salute)
- GreenHome (tecnologia green)
- Multiramo

### 2. Geo-Risk Map

Mappa 3D interattiva con Pydeck:

- **Scatter layer**: proprieta colorate per risk category
- **Heatmap layer**: concentrazione rischi
- **Zone sismiche**: overlay INGV (Zone 1-4)
- **Tooltip**: dettagli al hover

**Colori Risk:**
| Categoria | Colore | Score |
|-----------|--------|-------|
| Critico | Rosso #FF453A | >= 80 |
| Alto | Arancione #FF9F0A | 60-79 |
| Medio | Giallo #F59E0B | 40-59 |
| Basso | Verde #10B981 | < 40 |

### 3. Analytics Dashboard

- Distribuzione rischio (donut chart)
- Breakdown geo-rischio per tipologia
- CLV vs Risk Score (scatter plot)
- Churn probability distribution
- Top 10 citta per concentrazione rischio

### 4. Client Detail

Scheda cliente completa:

- Dati anagrafici (nome, eta, professione, reddito)
- Metriche (CLV, churn probability, num polizze)
- Risk profile della proprieta
- Lista polizze attive con dettagli
- Potenziale solare (kWh/anno, risparmio, ROI)
- Analisi satellitare (se disponibile)

---

## Iris AI Assistant

Assistente conversazionale sempre visibile nella sidebar, alimentato da Claude 3.5 Sonnet.

### 7 Tools Disponibili

| Tool | Parametri | Descrizione |
|------|-----------|-------------|
| `client_profile_lookup` | client_id | Profilo completo: anagrafica, CLV, polizze |
| `policy_status_check` | client_id | Lista polizze attive con premi e scadenze |
| `risk_assessment` | client_id | Risk score con breakdown sismico/idro/alluvioni |
| `solar_potential_calc` | client_id | Produzione kWh/anno, risparmio euro, ROI |
| `doc_retriever_rag` | client_id, query | Semantic search storico interazioni |
| `premium_calculator` | risk_score, product, coverage | Preventivo mensile/annuale |
| `database_explorer` | table, client_id, limit | Query generica su qualsiasi tabella |

### Esempio Conversazione

```
Utente: "Analizza il rischio per il cliente 9501"

Iris:
1. Chiama tool risk_assessment(client_id=9501)
2. Riceve: {risk_score: 72, category: "Alto", seismic: 70, hydro: 15, flood: 8}
3. Risponde con analisi formattata

Utente: "Dammi un preventivo NatCat"

Iris:
1. Chiama tool premium_calculator(risk_score=72, product="NatCat")
2. Riceve: {annual: 845, monthly: 70.42, breakdown: {...}}
3. Risponde con preventivo dettagliato
```

### Generazione Email Commerciali

Iris genera email personalizzate basate sui dati del cliente:

```
Utente: "Scrivi un'email per proporre NatCat al cliente 9501"

Output:
**Oggetto:** Protezione su misura per la Sua abitazione

Gentile Sig. Rossi,

[Corpo personalizzato con riferimento a:
 - Risk score della zona
 - Polizze attuali
 - Benefici specifici del prodotto
 - Call to action]

Cordiali saluti,
[Nome Agente]
```

### RAG (Retrieval Augmented Generation)

Per lo storico interazioni:

1. Query viene convertita in embedding (OpenAI text-embedding-3-small)
2. Vector search su tabella `interactions` via RPC Supabase
3. Top 5 risultati con similarity > 0.3
4. Fallback: ultimi 3 contatti se nessun match semantico

---

## Database Schema

### Tabella: clienti

```sql
codice_cliente    INTEGER PRIMARY KEY
nome              VARCHAR
cognome           VARCHAR
eta               INTEGER
professione       VARCHAR
reddito           NUMERIC
clv_stimato       NUMERIC      -- Customer Lifetime Value
churn_probability NUMERIC      -- 0-1
num_polizze       INTEGER
latitudine        NUMERIC
longitudine       NUMERIC
citta             VARCHAR
```

### Tabella: abitazioni

```sql
id                UUID PRIMARY KEY
codice_cliente    INTEGER REFERENCES clienti
citta             VARCHAR
latitudine        NUMERIC
longitudine       NUMERIC
zona_sismica      INTEGER      -- 1-4 (INGV)
risk_score        NUMERIC      -- 0-100
risk_category     VARCHAR      -- Basso/Medio/Alto/Critico
hydro_risk_p3     NUMERIC      -- % rischio idrogeologico P3
hydro_risk_p2     NUMERIC
flood_risk_p4     NUMERIC      -- % rischio alluvioni P4
flood_risk_p3     NUMERIC
solar_potential_kwh    NUMERIC
solar_savings_euro     NUMERIC
solar_coverage_percent NUMERIC
```

### Tabella: polizze

```sql
id                UUID PRIMARY KEY
codice_cliente    INTEGER REFERENCES clienti
prodotto          VARCHAR      -- NatCat, CasaSerena, etc.
area_bisogno      VARCHAR      -- Protezione, Risparmio, Previdenza
stato_polizza     VARCHAR      -- Attiva, Scaduta
data_emissione    TIMESTAMP
data_scadenza     TIMESTAMP
premio_totale_annuo NUMERIC
massimale         NUMERIC
```

### Tabella: interactions

```sql
id                UUID PRIMARY KEY
codice_cliente    INTEGER REFERENCES clienti
data_interazione  TIMESTAMP
tipo_interazione  VARCHAR      -- email, telefonata, reclamo
motivo            VARCHAR
esito             VARCHAR      -- positivo, neutro, negativo
note              TEXT
embedding         VECTOR       -- per RAG semantic search
dedup_key         VARCHAR UNIQUE
```

### RPC Functions

- `get_risk_distribution()`: statistiche aggregate rischi
- `match_interactions(query_embedding, threshold, count, filter_client_id)`: vector search

---

## Installazione

### Prerequisiti

- Python 3.11+
- Account Supabase con database popolato
- API key OpenRouter
- (Opzionale) Token Mapbox per mappe

### Setup Locale

```bash
# 1. Clona repository
git clone https://github.com/matteocifani/Helios.git
cd Helios

# 2. Crea virtual environment
python -m venv .venv
source .venv/bin/activate      # macOS/Linux
# .venv\Scripts\activate       # Windows

# 3. Installa dipendenze
pip install -r requirements.txt

# 4. Configura environment
cp .env.example .env
# Modifica .env con le tue credenziali

# 5. Avvia applicazione
streamlit run app.py
# Apri http://localhost:8501
```

### Deploy con Docker

```bash
# Build e avvio
docker compose up -d --build

# Logs
docker compose logs -f helios_dashboard

# Stop
docker compose down
```

---

## Configurazione

### Variabili d'Ambiente (.env)

```bash
# OBBLIGATORIO: Database
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIs...

# OBBLIGATORIO: AI Engine
OPENROUTER_API_KEY=sk-or-v1-...

# OPZIONALE: Mappe
MAPBOX_TOKEN=pk.eyJ1Ijoi...

# OPZIONALE: Timezone
TZ=Europe/Rome
```

### Costanti Configurabili (src/config/constants.py)

```python
# Risk Thresholds
RISK_LOW_THRESHOLD = 40
RISK_MEDIUM_THRESHOLD = 60
RISK_HIGH_THRESHOLD = 80

# Zone Sismiche INGV
SEISMIC_ZONES = {
    1: {"level": "Molto Alto", "score": 90},
    2: {"level": "Alto", "score": 70},
    3: {"level": "Medio", "score": 40},
    4: {"level": "Basso", "score": 15}
}

# Premi Base (euro/anno)
BASE_PREMIUMS = {
    "NatCat": 650,
    "CasaSerena": 380,
    "FuturoSicuro": 1200,
    "SaluteProtetta": 950,
    "GreenHome": 520,
    "Multiramo": 850
}

# Cache TTL
CACHE_TTL_SHORT = 1800   # 30 min
CACHE_TTL_MEDIUM = 600   # 10 min
CACHE_TTL_LONG = 3600    # 1 ora
```

---

## Struttura Progetto

```
Helios/
├── app.py                      # Entry point (3,889 righe)
├── requirements.txt            # Dipendenze Python
├── Dockerfile
├── docker-compose.yml
├── .env                        # Credenziali (non versionato)
│
├── src/
│   ├── config/
│   │   └── constants.py        # Costanti centralizzate (372 righe)
│   │
│   ├── data/
│   │   └── db_utils.py         # Supabase client + queries (936 righe)
│   │
│   ├── iris/
│   │   ├── engine.py           # AI engine con tools (757 righe)
│   │   └── chat.py             # UI chat Streamlit (481 righe)
│   │
│   └── utils/
│       ├── ui.py               # Componenti custom (137 righe)
│       └── vision_analysis.py  # Analisi satellitare (214 righe)
│
├── Data/
│   └── nbo_master.json         # Raccomandazioni NBO (33MB, 11,200 clienti)
│
├── scripts/                    # Utility scripts
├── tests/                      # Test suite
├── docs/                       # Documentazione aggiuntiva
└── Logo/                       # Asset grafici
```

---

## Scripts Disponibili

### Generazione Dati

```bash
# Genera file NBO master
python scripts/python/generate_nbo_master.py

# Upload dati su Supabase
python scripts/python/upload_to_supabase.py

# Esporta schema database
python scripts/python/export_supabase_schema.py
```

### Utility

```bash
# Verifica connessione Supabase
python scripts/check_schema.py

# Lista tabelle disponibili
python scripts/list_tables.py

# Test query RAG
python scripts/test_rag_query.py

# Benchmark performance fetch
python scripts/benchmark_lite.py

# Geocoding indirizzi
python scripts/geocode_addresses.py
```

### Testing

```bash
# Tutti i test
pytest tests/

# Test specifico
pytest tests/test_supabase_connection.py -v

# Con coverage
pytest --cov=src tests/
```

---

## Guida Sviluppatore

### Aggiungere Nuovo Tool a Iris

1. Implementa la funzione in `src/iris/engine.py`:

```python
def tool_my_function(self, param1: int) -> Dict:
    """Descrizione per Claude."""
    try:
        result = self.supabase.table("my_table").select("*").execute()
        return {"success": True, "data": result.data}
    except Exception as e:
        return {"error": str(e)}
```

2. Registra il tool in `__init__`:

```python
self.tools["my_function"] = self.tool_my_function
```

3. Aggiungi la definizione per Claude:

```python
self.tool_definitions.append({
    "type": "function",
    "function": {
        "name": "my_function",
        "description": "Cosa fa questo tool",
        "parameters": {
            "type": "object",
            "properties": {
                "param1": {"type": "integer", "description": "..."}
            },
            "required": ["param1"]
        }
    }
})
```

### Modificare NBO Weights

In `app.py`, sezione session state:

```python
st.session_state.nbo_weights = {
    'retention': 0.50,    # Cambia questi valori
    'redditivita': 0.30,
    'propensione': 0.20
}
```

### Aggiungere Nuova Sezione UI

1. Aggiungi state in session:

```python
if 'new_section_state' not in st.session_state:
    st.session_state.new_section_state = 'default'
```

2. Aggiungi tab nel layout principale:

```python
tab1, tab2, tab_new = st.tabs(["Analytics", "Policy", "Nuova Sezione"])

with tab_new:
    st.title("Nuova Sezione")
    # ... contenuto
```

### Pattern Performance

```python
# Cache dati statici
@st.cache_data(ttl=3600)
def expensive_computation():
    return result

# Fetch parallelo
from concurrent.futures import ThreadPoolExecutor
with ThreadPoolExecutor(max_workers=4) as executor:
    futures = [executor.submit(fn) for fn in functions]
    results = [f.result() for f in futures]

# Batch queries (evita N+1)
# NO: for id in ids: fetch_one(id)
# SI: fetch_batch(ids)
```

---

## Troubleshooting

| Problema | Causa Probabile | Soluzione |
|----------|-----------------|-----------|
| Connessione Supabase fallisce | Credenziali errate o scadute | Verifica SUPABASE_URL e SUPABASE_KEY in .env |
| Iris non risponde | API key OpenRouter scaduta | Genera nuova key su openrouter.ai |
| Mappa vuota | Fetch abitazioni fallito | Controlla logs, verifica tabella abitazioni |
| NBO non carica | File JSON mancante | Esegui `python scripts/python/generate_nbo_master.py` |
| Top 20 lento | Troppe query individuali | Il batch check e gia implementato, verifica `check_all_clients_interactions_batch()` |
| Docker build fallisce | Dipendenze mancanti | `pip install -r requirements.txt` e rebuild |
| RAG non trova risultati | Embeddings mancanti | Verifica colonna `embedding` in tabella `interactions` |

### Logs Utili

```bash
# Streamlit logs
streamlit run app.py --logger.level=debug

# Docker logs
docker compose logs -f --tail=100

# Python verbose
python -v scripts/check_schema.py
```

---

## Note Finali

### Limitazioni Note

- Chat history limitata a 5 messaggi per performance
- RAG threshold 0.3 puo dare falsi positivi su query generiche
- Potenziale solare stimato senza dati meteo reali
- Nessun sistema di autenticazione implementato

### Possibili Evoluzioni

- Sistema login per agenti
- Notifiche real-time (WebSocket)
- Export report PDF/Excel
- App mobile
- A/B testing su NBO weights
- Integrazione CRM

---

**Versione**: 2.0 - Vita Sicura Edition
**Ultimo Aggiornamento**: Gennaio 2026
**Sviluppato per**: Generali AI Challenge 2026
