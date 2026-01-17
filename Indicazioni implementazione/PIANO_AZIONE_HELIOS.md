# 🌞 PIANO D'AZIONE COMPLETO - PROGETTO HELIOS
## Completamento Ecosistema Assicurativo Geo-Cognitivo

**Versione:** 2.0 - 15 Gennaio 2026  
**Deadline Demo:** [DA DEFINIRE]  
**Budget:** €10 crediti OpenRouter + risorse hardware esistenti

---

## 📊 STATO ATTUALE - AUDIT COMPLETO

### ✅ COMPLETATO (70% Core Infrastructure)

#### Database & ETL
- ✅ Schema Supabase completo e operativo
- ✅ Tabelle popolate:
  - `clienti`: Record completi
  - `polizze`: Dati storici
  - `sinistri`: Storia sinistri
  - `abitazioni`: 5,190 record (solo 70% con indirizzo GPS valido)
  - `interactions`: 41,176 record con embeddings OpenAI ✅
  - `ref_seismic_zones`: 7,896 comuni INGV ✅
  - `ref_hydrogeological_zones`: 7,899 comuni ISPRA ✅

#### SkyGuard (Intelligence Geospaziale)
- ✅ Workflow ingestione dati CSV con UPSERT idempotente
- ✅ Workflow embeddings RAG per interactions
- ✅ Caricamento reference tables (INGV/ISPRA)
- ✅ Calcolo risk score: **3,634/5,190 abitazioni (70% copertura)**
- ⚠️ Gap: 1,556 abitazioni senza risk score (problema matching geografico)

#### Frontend Streamlit
- ✅ Struttura base app (`app.py`, `db_utils.py`, `ada_chat.py`)
- ✅ Connessione Supabase funzionante
- ✅ Docker setup con `docker-compose.yml`
- ⚠️ Estetica da migliorare completamente
- ⚠️ Funzionalità limitate (nessuna mappa interattiva ancora)

---

## ❌ DA IMPLEMENTARE

### PRIORITÀ 1 - CORE A.D.A. (Settimana 1-2)
#### Modulo A.D.A. - AI Agent con RAG
- ❌ Workflow n8n A.D.A. AI Agent con Tool-Use
- ❌ Sistema RAG completo (attualmente solo embeddings creati)
- ❌ Tools A.D.A.:
  - ❌ `client_profile_lookup`
  - ❌ `policy_status_check`
  - ❌ `risk_assessment`
  - ❌ `solar_potential_calc`
  - ❌ `doc_retriever_rag`
  - ❌ `premium_calculator`
- ❌ Webhook n8n per chat Streamlit
- ❌ Gestione conversazione multi-turn con memoria

### PRIORITÀ 2 - SOLAR DETECTION (Settimana 2)
#### Riconoscimento Pannelli Solari da Satellite
- ❌ Workflow detection pannelli solari
- ❌ Integrazione Google Maps Static API o Mapbox Satellite
- ❌ Modello Computer Vision (YOLO pre-trained o API detection)
- ❌ Campo `has_solar_panels` in tabella abitazioni
- ❌ Logica cross-selling automatica prodotti Green

### PRIORITÀ 3 - NBO MODULE (Settimana 3)
#### Next Best Offer Scoring System
- ❌ Tabella `nba_scores_master` (da creare)
- ❌ Modelli ML (da confermare con collega):
  - ❌ Clustering clienti (K-Means/HDBSCAN)
  - ❌ Modello Churn GLM
  - ❌ Calcolo penetrazione cluster
- ❌ Workflow scoring NBO:
  - ❌ Batch notturno (2 AM)
  - ❌ Trigger on-demand su vendita
- ❌ Tool A.D.A. per NBO: `get_next_best_offer`
- ❌ Dashboard NBO in Streamlit (tab dedicata)

### PRIORITÀ 4 - FRONTEND OVERHAUL (Settimana 3-4)
#### FluidView Dashboard Completo
- ❌ Redesign completo UI/UX (palette Aurora Borealis)
- ❌ Mappa geospaziale 3D con PyDeck:
  - ❌ Heatmap rischio
  - ❌ Scatterplot clienti (color-coded by CLV/risk)
  - ❌ Tooltip interattivi
  - ❌ Layer toggleable (sismica/idro/solar)
- ❌ Dashboard Analytics:
  - ❌ KPI cards (portfolio risk distribution)
  - ❌ Grafici Plotly interattivi
  - ❌ Filtri geografici dinamici
- ❌ Tab Ricerca Clienti:
  - ❌ Full-text search
  - ❌ Filtri avanzati (risk, CLV, churn, area)
  - ❌ Card dettaglio cliente espandibile
- ❌ Tab A.D.A. Chat:
  - ❌ UI conversazionale pulita
  - ❌ Visualizzazione tool-use in real-time
  - ❌ Export conversazioni
- ❌ Tab NBO Dashboard:
  - ❌ Top 50 raccomandazioni
  - ❌ Filtri per agente/area/prodotto
  - ❌ Export CSV per CRM

---

## 🎯 MILESTONE DETTAGLIATE

### 🚀 FASE 1: A.D.A. CORE ENGINE (Giorni 1-7)

#### Obiettivo
Creare un AI Agent funzionante in n8n che possa:
- Rispondere a domande sui clienti usando RAG
- Calcolare risk assessment
- Generare preventivi
- Stimare potenziale solare

#### Deliverable
1. **Workflow n8n: "A.D.A. Main Agent"**
   - Webhook trigger (`/webhook/ada-chat`)
   - AI Agent node (n8n v2.0+)
   - 6 Tools implementati
   - Gestione errori e timeout
   - Logging strutturato

2. **Tool 1: `client_profile_lookup`**
   ```sql
   SELECT c.*, a.risk_score, a.solar_potential_kwh
   FROM clienti c
   LEFT JOIN abitazioni a ON c.codice_cliente = a.codice_cliente
   WHERE c.codice_cliente = $1
   ```

3. **Tool 2: `policy_status_check`**
   ```sql
   SELECT prodotto, stato_polizza, data_scadenza, premio_totale_annuo
   FROM polizze
   WHERE codice_cliente = $1 AND stato_polizza = 'Attiva'
   ```

4. **Tool 3: `risk_assessment`**
   - Input: codice_cliente o coordinate
   - Logic: Query abitazioni + ref tables
   - Output: JSON con risk breakdown

5. **Tool 4: `solar_potential_calc`**
   - Workflow separato chiamato via n8n "Execute Workflow"
   - Input: lat, lon
   - API: PVGIS
   - Output: kWh annui, ROI, savings €

6. **Tool 5: `doc_retriever_rag`**
   ```sql
   SELECT text_embedded, 1 - (embedding <=> $1::vector) AS similarity
   FROM interactions
   WHERE codice_cliente = $2
   ORDER BY similarity DESC
   LIMIT 5
   ```
   - Nota: $1 è l'embedding della query utente (da generare in real-time)

7. **Tool 6: `premium_calculator`**
   - Nodo Code (JavaScript)
   - Input: risk_score, product_type, coverage_amount
   - Formula: `base_premium * risk_multiplier * coverage_factor`
   - Output: preventivo JSON

#### Test Scenario
```
User: "Analizza il rischio del cliente CLI1234"
A.D.A. → Chiama client_profile_lookup → Ottiene risk_score=75
      → Chiama risk_assessment → Ottiene breakdown sismica/idro
      → Genera risposta: "Il cliente CLI1234 ha un rischio ALTO (75/100)..."
```

#### Tempo Stimato: 5-7 giorni
- Giorno 1-2: Setup Agent + Tool 1-2
- Giorno 3-4: Tool 3-4 (complessi)
- Giorno 5-6: Tool 5-6 + RAG integration
- Giorno 7: Testing end-to-end

---

### 🛰️ FASE 2: SOLAR PANEL DETECTION (Giorni 8-10)

#### Obiettivo
Riconoscere automaticamente la presenza di pannelli solari sugli immobili usando immagini satellitari.

#### Approccio Consigliato: Modello Pre-trained
**Opzione A: Roboflow Solar Panel Detection** (CONSIGLIATA)
- Modello: https://universe.roboflow.com/solar-panels-detection/solar-panels-detection-ysz8k
- API inference: ~$0.0005 per immagine
- Accuracy: ~85-90%
- Workflow:
  1. Ottieni coordinate abitazione
  2. Chiama Google Maps Static API → immagine satellite
  3. POST a Roboflow API → JSON con bounding boxes
  4. Se confidence > 0.7 → `has_solar_panels = true`

**Opzione B: Google Cloud Vision + Custom Labels**
- Usa Vision API con label detection
- Cerca label "solar panel" o "photovoltaic"
- Meno accurato ma più semplice (~70% accuracy)

#### Workflow n8n: "Solar Detection Pipeline"
```
[Manual Trigger]
    ↓
[Get Abitazioni without solar_detected]
    ↓
[Loop Batches: 50 at time]
    ↓
[Google Static Maps API] → Download satellite image
    ↓
[Roboflow Inference API] → Detection
    ↓
[Parse Results] → has_solar = detections.length > 0 && confidence > 0.7
    ↓
[Update Supabase] → UPDATE abitazioni SET has_solar_panels = $1
```

#### Budget Impact
- Google Static Maps: $0.002/request
- Roboflow Inference: $0.0005/request
- Totale per 5,190 abitazioni: ~$13 (1 run completo)
- **Decisione:** Esegui solo su High-Value clients first (CLV > 20k) = ~500 clienti = $1.25

#### Test Scenario
```sql
-- Verifica risultati
SELECT 
  citta,
  COUNT(*) as total,
  SUM(CASE WHEN has_solar_panels THEN 1 ELSE 0 END) as with_solar,
  ROUND(AVG(CASE WHEN has_solar_panels THEN 1 ELSE 0 END) * 100, 1) as solar_rate
FROM abitazioni
WHERE solar_detected_at IS NOT NULL
GROUP BY citta
ORDER BY solar_rate DESC
LIMIT 20;
```

#### Tempo Stimato: 3 giorni
- Giorno 1: Setup API + Test su 10 samples
- Giorno 2: Workflow completo + Batch processing
- Giorno 3: Run production + Validation

---

### 📊 FASE 3: NBO MODULE (Giorni 11-14)

#### Prerequisito
⚠️ **ATTENDERE CONFERMA COLLEGA** su stato modelli ML

#### Schema Database
```sql
CREATE TABLE nba_scores_master (
  id SERIAL PRIMARY KEY,
  codice_cliente INTEGER REFERENCES clienti(codice_cliente),
  prodotto TEXT NOT NULL,
  area_bisogno TEXT,
  score_nbo NUMERIC(5,2) NOT NULL,
  
  -- Componenti Score
  compatibilita_cluster NUMERIC(5,2),
  redditivita NUMERIC(5,2),
  retention_gain NUMERIC(5,2),
  prob_conversione NUMERIC(5,2),
  
  -- Metadata
  cluster_id INTEGER,
  churn_prima NUMERIC(5,4),
  churn_dopo NUMERIC(5,4),
  delta_churn NUMERIC(5,4),
  
  calculated_at TIMESTAMP DEFAULT NOW(),
  data_sources JSONB, -- Tracciabilità
  
  CONSTRAINT unique_client_product UNIQUE (codice_cliente, prodotto)
);

CREATE INDEX idx_nba_score_desc ON nba_scores_master(score_nbo DESC);
CREATE INDEX idx_nba_cliente ON nba_scores_master(codice_cliente);
CREATE INDEX idx_nba_calculated ON nba_scores_master(calculated_at DESC);
```

#### Se Modelli NON Pronti → Piano B: Scoring Euristico
```javascript
// Nodo Code: Calcolo NBO Score semplificato
const cliente = $input.item.json;
const polizze_attuali = cliente.polizze || [];
const prodotti_non_posseduti = ALL_PRODUCTS.filter(p => 
  !polizze_attuali.includes(p.nome)
);

return prodotti_non_posseduti.map(prodotto => {
  // Euristica semplice basata su dati disponibili
  const compatibilita = calcolaCompatibilita(cliente, prodotto); // 0-100
  const redditivita = prodotto.margine_medio || 50; // 0-100
  const retention = cliente.num_polizze >= 3 ? 80 : 50; // Multi-holding bonus
  
  const score = (compatibilita * 0.4) + (redditivita * 0.3) + (retention * 0.3);
  
  return {
    codice_cliente: cliente.codice_cliente,
    prodotto: prodotto.nome,
    area_bisogno: prodotto.area,
    score_nbo: score.toFixed(2),
    compatibilita_cluster: compatibilita,
    redditivita: redditivita,
    retention_gain: retention,
    prob_conversione: 50 // Default
  };
});
```

#### Workflow: "NBO Batch Scoring"
- Trigger: Schedule (Daily 2 AM)
- Input: Clienti modificati nelle ultime 24h
- Process: Calcolo score per ogni prodotto non posseduto
- Output: UPSERT in `nba_scores_master`

#### Tool A.D.A.: `get_next_best_offer`
```sql
SELECT prodotto, area_bisogno, score_nbo, 
       compatibilita_cluster, redditivita, retention_gain
FROM nba_scores_master
WHERE codice_cliente = $1
ORDER BY score_nbo DESC
LIMIT 3
```

#### Dashboard Streamlit: Tab NBO
- **Top 50 Opportunities**: DataTable con score_nbo > 70
- **Filtri**: Area geografica, Agente, Prodotto
- **Export CSV**: Per import in CRM
- **Drill-down**: Click su cliente → Mostra dettagli + trigger A.D.A. analysis

#### Tempo Stimato: 4 giorni
- Giorno 1: Schema DB + Scoring euristico
- Giorno 2: Workflow batch + Testing
- Giorno 3: Tool A.D.A. integration
- Giorno 4: Dashboard Streamlit

---

### 🎨 FASE 4: FRONTEND OVERHAUL (Giorni 15-21)

#### Design System: "Aurora Borealis"

**Palette Colori:**
```python
HELIOS_COLORS = {
    'primary': '#FF6B35',      # Helios Sun
    'secondary': '#00E5CC',    # Aurora Cyan
    'background': '#0D1117',   # Deep Space
    'surface': '#161B22',      # Card Background
    'text': '#F0F6FC',         # Text Primary
    'text_dim': '#8B949E',     # Text Secondary
    
    # Risk Scale
    'risk_critical': '#FF453A',
    'risk_high': '#FF9F0A',
    'risk_medium': '#FFD60A',
    'risk_low': '#30D158',
    
    # Status
    'success': '#34D399',
    'warning': '#FBBF24',
    'error': '#EF4444',
    'info': '#3B82F6'
}
```

#### Struttura App Nuova
```
app.py (Main)
├── 🏠 Home / Dashboard Overview
│   ├── KPI Cards (4x): Total Portfolio, Avg Risk, Solar Potential, NBO Opportunities
│   ├── Map: PyDeck 3D Geospatial View
│   └── Quick Stats Charts (Plotly)
│
├── 🗺️ Risk Map
│   ├── Heatmap Layer (rischio aggregato per zona)
│   ├── Scatterplot Layer (clienti individuali)
│   ├── Layer Controls (toggle sismica/idro/solar)
│   └── Click → Sidebar con dettagli cliente
│
├── 🔍 Client Search
│   ├── Search Bar (full-text)
│   ├── Filters (Risk, CLV, Churn, Area)
│   ├── Results Table (sortable, paginated)
│   └── Click → Modal con dettaglio completo
│
├── 🤖 A.D.A. Chat
│   ├── Chat Interface (st.chat_message)
│   ├── Tool Activity Indicator
│   └── Export Conversation
│
├── 📊 NBO Dashboard
│   ├── Top Opportunities (DataTable)
│   ├── Filters (Agent, Product, Area)
│   └── Actions (Export, Trigger Campaign)
│
└── ⚙️ Settings
    ├── Webhook Config
    └── Data Refresh
```

#### Implementazione Mappa PyDeck
```python
import pydeck as pdk

# Layer 1: Heatmap
heatmap_layer = pdk.Layer(
    'HeatmapLayer',
    data=df_abitazioni,
    get_position='[longitudine, latitudine]',
    get_weight='risk_score',
    radius_pixels=50,
    color_range=[
        [30, 209, 88, 100],   # Green
        [255, 214, 10, 100],  # Yellow
        [255, 159, 10, 100],  # Orange
        [255, 69, 58, 100]    # Red
    ]
)

# Layer 2: Scatterplot Clienti
scatter_layer = pdk.Layer(
    'ScatterplotLayer',
    data=df_clienti,
    get_position='[longitudine, latitudine]',
    get_color='[risk_score * 2.5, 255 - risk_score * 2.5, 100, 180]',
    get_radius='clv_stimato / 100',
    pickable=True,
    auto_highlight=True
)

# View State
view_state = pdk.ViewState(
    latitude=42.5,  # Centro Italia
    longitude=12.5,
    zoom=5.5,
    pitch=45,
    bearing=0
)

# Render
deck = pdk.Deck(
    layers=[heatmap_layer, scatter_layer],
    initial_view_state=view_state,
    tooltip={'html': '<b>Cliente:</b> {nome}<br><b>Risk:</b> {risk_score}'}
)

st.pydeck_chart(deck)
```

#### Tempo Stimato: 7 giorni
- Giorno 1-2: Design system + Layout base
- Giorno 3-4: Mappa PyDeck + interazioni
- Giorno 5: Dashboard Analytics + KPI
- Giorno 6: Tab Search + NBO
- Giorno 7: Polish + Responsive

---

## 🔧 IMPLEMENTAZIONE TECNICA

### Setup Environment Variables
```bash
# .env file
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
N8N_WEBHOOK_URL=https://cifani.ddns.net/webhook/ada-chat
OPENROUTER_API_KEY=sk-or-v1-xxxxx
GOOGLE_MAPS_API_KEY=AIzaSyXXXXX  # Per solar detection
ROBOFLOW_API_KEY=xxxxx            # Per solar detection
```

### Workflow n8n Standards
**Naming Convention:**
- Production workflows: `[Module] - [Function]`
- Examples: `A.D.A. - Main Agent`, `SkyGuard - Solar Detection`
- Debugging: `DEBUG - [Topic]` → sempre archived dopo uso

**Error Handling:**
```javascript
// In ogni nodo Code/HTTP Request
try {
  // Logic
} catch (error) {
  return [{
    json: {
      success: false,
      error: error.message,
      timestamp: new Date().toISOString(),
      workflow: 'A.D.A. - Main Agent'
    }
  }];
}
```

**Logging:**
```sql
-- Tabella log_workflow in Supabase
CREATE TABLE log_workflow (
  id SERIAL PRIMARY KEY,
  workflow_name TEXT,
  execution_id TEXT,
  status TEXT,
  input_data JSONB,
  output_data JSONB,
  error TEXT,
  execution_time_ms INTEGER,
  created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 📈 METRICHE DI SUCCESSO

### KPI Tecnici
- ✅ **Coverage Rate abitazioni**: Target 90% (attuale 70%)
- ✅ **A.D.A. Response Time**: < 5 secondi (p95)
- ✅ **RAG Retrieval Accuracy**: > 85% relevant docs
- ✅ **Solar Detection Accuracy**: > 80%
- ✅ **Dashboard Load Time**: < 2 secondi

### KPI Business (Demo)
- 🎯 Identificare 100+ opportunità NBO con score > 80
- 🎯 Calcolare rischio per 4,500+ abitazioni (90% portfolio)
- 🎯 Dimostrare 3 casi d'uso A.D.A. completi
- 🎯 Visualizzare heatmap rischio Italia con drill-down province

---

## ⚠️ RISCHI E MITIGAZIONI

| Rischio | Probabilità | Impatto | Mitigazione |
|---------|-------------|---------|-------------|
| Modelli ML NBO non pronti | Media | Alto | Piano B: Scoring euristico documentato |
| Budget OpenRouter esaurito | Bassa | Medio | Usare modelli più economici (Sonnet 3.5) |
| Solar detection inaccurata | Media | Basso | Validazione manuale su sample + fallback PVGIS |
| Performance Streamlit lenta | Media | Medio | Cache aggressive + pagination |
| Deadline troppo stretta | Alta | Alto | Priorizzare FASE 1-2, rimandare ottimizzazioni |

---

## 🚀 DEPLOYMENT CHECKLIST

### Pre-Demo (Giorno -1)
- [ ] Tutti workflow n8n testati e attivi
- [ ] Database backup eseguito
- [ ] Streamlit deployed su Streamlit Cloud (o locale con port forwarding stabile)
- [ ] A.D.A. webhook testato con 10+ scenari
- [ ] Screenshot + Video demo preparati
- [ ] Presentazione PowerPoint/Google Slides ready

### Demo Day
- [ ] n8n online e raggiungibile
- [ ] Streamlit accessible via link pubblico
- [ ] Dataset caricato e aggiornato
- [ ] 3 casi d'uso A.D.A. preparati:
  1. "Analizza rischio cliente ad alto valore in Emilia-Romagna"
  2. "Suggerisci prossima polizza per cliente con 2 polizze vita"
  3. "Calcola preventivo NatCat per abitazione in zona sismica 2"

---

## 📚 RISORSE E DOCUMENTAZIONE

### API Documentation
- **n8n Docs**: https://docs.n8n.io
- **Supabase pgvector**: https://supabase.com/docs/guides/ai
- **PyDeck**: https://deckgl.readthedocs.io
- **PVGIS API**: https://joint-research-centre.ec.europa.eu/pvgis
- **Roboflow**: https://docs.roboflow.com

### Repository Utili
- Solar Panel Detection Models: https://universe.roboflow.com/solar
- n8n AI Agent Examples: https://n8n.io/workflows/ai-agent
- Streamlit Gallery: https://streamlit.io/gallery

---

## ✅ ACCEPTANCE CRITERIA

Il progetto è **COMPLETO** quando:

1. ✅ A.D.A. risponde correttamente a 3 query di test con RAG + tools
2. ✅ Dashboard Streamlit mostra mappa interattiva con 4,000+ properties
3. ✅ Almeno 500 abitazioni hanno `has_solar_panels` detected
4. ✅ NBO dashboard mostra top 50 opportunità con score > 70
5. ✅ Sistema è demo-ready con < 5 sec response time
6. ✅ Documentazione completa e presentazione pronta

---

**Next Step Immediato:**  
🎯 **Iniziare FASE 1 - Giorno 1: Setup A.D.A. Agent Base + Tool 1-2**

Vuoi che proceda con l'implementazione del primo workflow A.D.A.?
