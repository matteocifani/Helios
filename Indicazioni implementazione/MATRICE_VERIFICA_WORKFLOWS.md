# 🔍 MATRICE VERIFICA WORKFLOW N8N - PROGETTO HELIOS

**Data Audit:** 15 Gennaio 2026  
**Istanza n8n:** https://cifani.ddns.net  
**Versione n8n:** 2.33.2

---

## 📊 RIEPILOGO STATISTICO

| Categoria | Totale | Attivi | Archiviati | Completati | Da Fare |
|-----------|--------|--------|-----------|------------|---------|
| **ETL & Data Loading** | 8 | 0 | 3 | 5 | 0 |
| **SkyGuard - Risk Assessment** | 12 | 0 | 5 | 7 | 2 |
| **SkyGuard - Solar** | 2 | 0 | 0 | 1 | 1 |
| **A.D.A. - AI Agent** | 1 | 0 | 0 | 0 | 1 |
| **NBO - Next Best Offer** | 0 | 0 | 0 | 0 | 5 |
| **Debug/Diagnostics** | 10 | 0 | 8 | 2 | - |
| **Altri/Template** | 32 | 0 | 32 | - | - |
| **TOTALE** | 65 | 0 | 48 | 15 | 9 |

**Note:**
- ⚠️ Nessun workflow attualmente attivo (tutti stopped)
- ✅ 15 workflow production-ready (testati e funzionanti)
- 🚧 9 workflow da implementare per completare il progetto
- 🗑️ 48 workflow archiviati (template, debug, test)

---

## 🗂️ DETTAGLIO PER MODULO

### MODULE 1: ETL & DATA LOADING

#### ✅ COMPLETATI

| ID | Nome Workflow | Descrizione | Status | Note |
|----|--------------|-------------|--------|------|
| `u3WbiQR9MMsYu0qO` | **MM - AI Challenge Generali** | ETL principale per caricamento CSV iniziali | 🟢 Funzionante | Workflow base per clienti/polizze/sinistri |
| `eGZNaIRnIUW6sXSK` | **MM - Interazioni RAG (Embeddings)** | Vettorizzazione interactions con OpenRouter | 🟢 Funzionante | **41,176 embeddings creati** ✅ |
| `czVazVuYgFjVpxD4` | **MM - Load Abitazioni CSV** | Caricamento abitazioni.csv | 🟢 Funzionante | 5,190 records caricati |
| `c69N9TNMtZLpBCGm` | **MM - Setup Database Schema** | Creazione schema iniziale Supabase | 🟢 Completato | Schema production OK |
| `vzUsWbRtTCwMiFAW` | **MM - Setup Abitazioni Table** | Setup tabella abitazioni con colonne risk | 🟢 Completato | Include solar/risk columns |

#### ❌ DA IMPLEMENTARE
Nessuno - ETL base completato ✅

---

### MODULE 2: SKYGUARD - RISK ASSESSMENT

#### ✅ COMPLETATI

| ID | Nome Workflow | Descrizione | Status | Note |
|----|--------------|-------------|--------|------|
| `LioqruwV7cDxUnKC` | **MM - Load Seismic Zones** | Import zone sismiche INGV | 🟢 Funzionante | 7,896 comuni caricati ✅ |
| `PjbB4H04VCOZmuGO` | **MM - Load Hydrogeological Zones** | Import zone idrogeologiche ISPRA | 🟢 Funzionante | 7,899 comuni caricati ✅ |
| `WPANYdTCKiLLSOGa` | **MM - Enrich Seismic Risk** | Arricchimento rischio sismico | 🟢 Funzionante | Join abitazioni ↔ ref_seismic_zones |
| `UDNEsY3hCXh7966R` | **MM - Enrich Hydrogeological Risk** | Arricchimento rischio idrogeologico | 🟢 Funzionante | Join abitazioni ↔ ref_hydrogeological_zones |
| `JyBHTbvak1Yip0Z5` | **MM - Calculate Risk Score** | Calcolo risk_score finale | 🟢 Funzionante | Formula: sismica + idro + flood |
| `Aqb92fRvYkot2Mlg` | **MM - Complete Risk Assessment Pipeline** | Pipeline completa orchestrata | 🟢 Funzionante | Esegue enrichment → calc score |
| `h6kpCZNpisSd6ilV` | **MM - Setup Seismic Zones Table** | Setup schema ref_seismic_zones | 🟢 Completato | DDL eseguito |

#### 🚧 IN PROGRESS / ISSUES

| ID | Nome Workflow | Status | Issue | Soluzione Proposta |
|----|--------------|--------|-------|-------------------|
| `6niFc2w79qisXb91` | **MM - SkyGuard Reverse Geocoding** | 🟡 Archiviato | Coordinate sintetiche nel CSV → geocoding inutile | **SKIP** - Usare solo indirizzi verified |
| Vari debug workflows | 15+ workflows debug | 🟡 Archiviati | Diagnostic per matching geografico | Gap matching: 30% abitazioni senza risk score |

**Root Cause Gap Matching (30% abitazioni):**
Le abitazioni senza risk_score sono localizzate in **frazioni/località non autonome** che non esistono come comuni autonomi nei dataset ISPRA/INGV.

Esempi:
- "San Martino" → Frazione di 50+ comuni diversi
- "Collemeto" → Frazione di Galatina (LE)

**Decisione Strategica:**
✅ **Accettare 70% coverage** come ottimale per demo  
❌ NON sprecare tempo in geocoding forward (dati sintetici)

#### ❌ DA IMPLEMENTARE

| Workflow | Descrizione | Priorità | Tempo Stimato |
|----------|-------------|----------|---------------|
| **SkyGuard - Risk Alert Generator** | Trigger automatico per nuovi rischi HIGH/CRITICAL | 🔴 Alta | 2 ore |
| **SkyGuard - Bulk Recalculation** | Recalcolo batch per aggiornamenti dataset INGV/ISPRA | 🟡 Media | 3 ore |

---

### MODULE 3: SKYGUARD - SOLAR POTENTIAL

#### ✅ COMPLETATI

| ID | Nome Workflow | Descrizione | Status | Note |
|----|--------------|-------------|--------|------|
| `krojXjGuwGidd0c9` | **MM - Solar Potential PVGIS** | Workflow base per chiamata PVGIS API | 🟢 Funzionante | Calcola kWh teorico per coordinate |

**Funzionamento Attuale:**
- Input: latitudine, longitudine
- API: PVGIS (EU Joint Research Centre)
- Output: Produzione annua stimata (kWh/anno) per impianto 3kW

**Limitazioni:**
- ⚠️ Non verifica presenza effettiva pannelli
- ⚠️ Calcolo teorico (non considera ombreggiature, orientamento reale)

#### ❌ DA IMPLEMENTARE

| Workflow | Descrizione | Priorità | Tempo Stimato |
|----------|-------------|----------|---------------|
| **🛰️ Solar Panel Detection (CV)** | Riconoscimento pannelli da satellite | 🔴 Alta | 1-2 giorni |

**Spec Tecnico "Solar Panel Detection":**

```
[Trigger: Manual / Schedule Weekly]
    ↓
[Query Supabase] → SELECT abitazioni WHERE solar_detected_at IS NULL AND clv_stimato > 20000
    ↓
[Loop Batches: 50] → Rate limit Google/Roboflow APIs
    ↓
[Google Static Maps API]
    • URL: https://maps.googleapis.com/maps/api/staticmap
    • Params: center={lat},{lon}&zoom=20&size=640x640&maptype=satellite
    • Output: Image (base64)
    ↓
[Roboflow Inference API]
    • Endpoint: https://detect.roboflow.com/solar-panels-detection-ysz8k/1
    • Input: Image base64
    • Output: JSON { predictions: [{ class, confidence, bbox }] }
    ↓
[Parse Detection]
    • has_solar = predictions.length > 0 && confidence > 0.7
    • panel_count = predictions.length
    • detection_confidence = avg(predictions.map(p => p.confidence))
    ↓
[Update Database]
    UPDATE abitazioni SET
      has_solar_panels = $1,
      solar_panel_count = $2,
      solar_detection_confidence = $3,
      solar_detected_at = NOW()
    WHERE codice_cliente = $4
    ↓
[Trigger Cross-Sell Logic]
    IF has_solar_panels = true AND prodotto_green NOT IN polizze
      → Aggiungi a NBO queue con boost score
```

**API Costs Estimate:**
- Google Static Maps: $0.002/request
- Roboflow Inference: $0.0005/request
- **Total per 500 high-value clients:** $1.25 ✅ Budget OK

**Alternative (Free/Low-Cost):**
1. Mapbox Satellite API (14 days free trial, poi $0.25/1000 requests)
2. OpenStreetMap Overpass API (free, ma no satellite imagery quality)
3. Manual labeling via Streamlit UI (fallback per validazione)

---

### MODULE 4: A.D.A. - AI AGENT

#### ❌ COMPLETAMENTE DA IMPLEMENTARE

| Workflow | Descrizione | Priorità | Tempo Stimato |
|----------|-------------|----------|---------------|
| **🤖 A.D.A. Main Agent** | Workflow AI Agent principale con Tool-Use | 🔴 Critica | 5-7 giorni |

**Spec Dettagliato "A.D.A. Main Agent":**

```yaml
Workflow ID: [NEW]
Nome: "A.D.A. - Main Agent"
Trigger: Webhook
  - URL: /webhook/ada-chat
  - Method: POST
  - Auth: None (protetto da n8n CORS)

Nodes:
  1. Webhook Trigger
     - Capture: message, client_id, history[], session_id
  
  2. Validate Input
     - Code Node: Check message non empty, sanitize
  
  3. Get Client Context (if client_id presente)
     - Postgres Query:
       SELECT c.*, a.risk_score, a.solar_potential_kwh, a.zona_sismica
       FROM clienti c
       LEFT JOIN abitazioni a ON c.codice_cliente = a.codice_cliente
       WHERE c.codice_cliente = {{ $json.client_id }}
  
  4. AI Agent Node (n8n v2.0+)
     - Model: OpenRouter - anthropic/claude-3.5-sonnet
     - System Prompt: [Vedi sotto]
     - Chat History: Gestita da n8n
     - Tools: 6 tools (vedi mapping sotto)
  
  5. Format Response
     - Code Node: Sanitize output, format JSON
  
  6. Log Interaction
     - Postgres Insert: log_ada_interactions table
  
  7. Webhook Response
     - Return: { success: true, response: ..., tools_used: [...] }

Tools Mapping:
  - Tool 1: client_profile_lookup → Sub-workflow "A.D.A. Tool - Client Profile"
  - Tool 2: policy_status_check → Sub-workflow "A.D.A. Tool - Policies"
  - Tool 3: risk_assessment → Sub-workflow "A.D.A. Tool - Risk"
  - Tool 4: solar_potential_calc → Execute existing "MM - Solar Potential PVGIS"
  - Tool 5: doc_retriever_rag → Sub-workflow "A.D.A. Tool - RAG Search"
  - Tool 6: premium_calculator → Sub-workflow "A.D.A. Tool - Premium Calc"
```

**System Prompt per A.D.A.:**
```
Sei A.D.A. (Augmented Digital Advisor), assistente AI specializzato in:
- Analisi rischio assicurativo (sismico, idrogeologico, alluvioni)
- Valutazione potenziale fotovoltaico
- Consulenza polizze personalizzate
- Calcolo preventivi NatCat

REGOLE:
1. Usa SEMPRE i tools per ottenere dati recenti - non inventare numeri
2. Se chiedi dati su un cliente, usa client_profile_lookup PRIMA di rispondere
3. Per domande su rischio, usa risk_assessment
4. Per polizze attive, usa policy_status_check
5. Rispondi in italiano professionale ma friendly
6. Sii conciso: max 3-4 paragrafi per risposta
7. Usa emoji strategici (🏠 🌊 ☀️ 📊) per readability
8. Se non hai dati sufficienti, chiedi chiarimenti invece di speculare

FORMATO NUMERI:
- Risk score: 0-100 (Basso <40, Medio 40-59, Alto 60-79, Critico ≥80)
- Importi €: sempre con separatore migliaia (€15.000 non €15000)
- Percentuali: 1 decimale (85.3% non 85.293847%)
```

**Sub-Workflows da Creare (6 Tools):**

1. **A.D.A. Tool - Client Profile**
```sql
-- Nodo Postgres
SELECT 
  c.codice_cliente,
  c.nome || ' ' || c.cognome as nome_completo,
  c.eta,
  c.professione,
  c.reddito,
  c.clv_stimato,
  c.churn_probability,
  c.num_polizze,
  a.risk_score,
  a.risk_category,
  a.zona_sismica,
  a.solar_potential_kwh,
  a.citta
FROM clienti c
LEFT JOIN abitazioni a ON c.codice_cliente = a.codice_cliente
WHERE c.codice_cliente = {{ $json.client_id }}
```

2. **A.D.A. Tool - Policies**
```sql
SELECT 
  prodotto,
  area_bisogno,
  stato_polizza,
  data_emissione,
  data_scadenza,
  premio_totale_annuo,
  massimale
FROM polizze
WHERE codice_cliente = {{ $json.client_id }}
  AND stato_polizza = 'Attiva'
ORDER BY data_emissione DESC
```

3. **A.D.A. Tool - Risk Assessment**
```javascript
// Nodo Code
const clientData = $input.item.json;

// Calcolo breakdown rischio
const seismic = getSeismicRiskLevel(clientData.zona_sismica); // 1-4 → score
const hydro = clientData.hydro_risk_p3 || 0;
const flood = clientData.flood_risk_p4 || 0;

return {
  risk_score: clientData.risk_score || 0,
  risk_category: clientData.risk_category || 'Non valutato',
  breakdown: {
    seismic: { level: clientData.zona_sismica, score: seismic },
    hydrogeological: { p3: hydro, level: hydro > 5 ? 'Alto' : 'Basso' },
    flood: { p4: flood, level: flood > 10 ? 'Alto' : 'Basso' }
  },
  recommended_coverage: getRiskBasedCoverage(clientData.risk_score)
};
```

4. **A.D.A. Tool - Solar Calc**
→ Execute Workflow "MM - Solar Potential PVGIS"

5. **A.D.A. Tool - RAG Search**
```sql
-- Query vettoriale
WITH query_embedding AS (
  -- Genera embedding della query con OpenRouter
  SELECT embedding FROM generate_embedding({{ $json.query }})
)
SELECT 
  i.text_embedded,
  i.data_interazione,
  i.tipo_interazione,
  i.esito,
  1 - (i.embedding <=> (SELECT embedding FROM query_embedding)) AS similarity
FROM interactions i
WHERE i.codice_cliente = {{ $json.client_id }}
ORDER BY similarity DESC
LIMIT 5
```

6. **A.D.A. Tool - Premium Calculator**
```javascript
// Nodo Code
const { risk_score, product_type, coverage_amount } = $input.item.json;

// Formule base pricing
const basePremiums = {
  'NatCat': 450,
  'CasaSerena': 380,
  'GreenHome': 520,
  'Multiramo': 650
};

const base = basePremiums[product_type] || 500;
const riskMultiplier = 1 + (risk_score / 100); // Risk 0-100 → 1.0-2.0x
const coverageFactor = (coverage_amount / 100000) || 1; // Base 100k

const premium = Math.round(base * riskMultiplier * coverageFactor);

return {
  product: product_type,
  base_premium: base,
  risk_multiplier: riskMultiplier.toFixed(2),
  coverage_amount: coverage_amount,
  total_premium_annual: premium,
  monthly_payment: Math.round(premium / 12)
};
```

**Testing Checklist A.D.A.:**
- [ ] Webhook risponde in < 5 secondi
- [ ] Tutti 6 tools eseguono senza errori
- [ ] RAG retrieval restituisce documenti pertinenti
- [ ] Premium calculator genera valori sensati
- [ ] Response format JSON valido
- [ ] Error handling per client_id inesistente
- [ ] Log interactions salvato correttamente

---

### MODULE 5: NBO - NEXT BEST OFFER

#### ❌ COMPLETAMENTE DA IMPLEMENTARE

**⚠️ BLOCCO DIPENDENZE: Attendere conferma modelli ML dal collega**

| Workflow | Descrizione | Priorità | Tempo Stimato |
|----------|-------------|----------|---------------|
| **NBO - Setup Database** | Creazione schema nba_scores_master | 🟡 Media | 30 min |
| **NBO - Batch Scoring (Euristico)** | Calcolo score semplificato senza ML | 🟢 Bassa | 4 ore |
| **NBO - Batch Scoring (ML)** | Integrazione modelli clustering + GLM | 🔴 Alta | 2 giorni |
| **NBO - On-Demand Trigger** | Trigger scoring su vendita polizza | 🟡 Media | 2 ore |
| **A.D.A. Tool - NBO** | Tool per query top offers | 🟡 Media | 1 ora |

**Dipendenze Esterne:**
1. Modello clustering clienti (K-Means) → **Verificare con collega**
2. Modello churn GLM coefficienti → **Verificare con collega**
3. Tabella penetrazione prodotti per cluster → **Calcolare da polizze**

**Piano B (Se modelli non pronti):**
Implementare scoring euristico basato su:
- Compatibilità: Match professione/reddito con prodotto target
- Redditività: Margine medio prodotto (da rendiconto_2024)
- Retention: Bonus multi-holding (num_polizze >= 3)
- Conversione: Euristica età/prodotto

**Spec Workflow "NBO - Batch Scoring Euristico":**
```
[Trigger: Schedule Daily 2:00 AM]
    ↓
[Query Modified Clients]
    SELECT codice_cliente 
    FROM clienti 
    WHERE updated_at > NOW() - INTERVAL '24 hours'
    ↓
[Get Client Data + Polizze]
    ↓
[Loop Clients]
    ↓
    [For Each Product NOT Owned]
        ↓
        [Calculate Score Components]
        - compatibilita = matchProfessione(cliente, prodotto)
        - redditivita = getMargine(prodotto)
        - retention = cliente.num_polizze >= 3 ? 80 : 50
        - conversione = 50 (default)
        ↓
        [Calculate Total Score]
        score = (compatibilita * 0.4) + (redditivita * 0.3) + 
                (retention * 0.2) + (conversione * 0.1)
    ↓
[UPSERT nba_scores_master]
    ON CONFLICT (codice_cliente, prodotto)
    DO UPDATE SET score_nbo = EXCLUDED.score_nbo, ...
```

---

## 🗺️ ROADMAP IMPLEMENTAZIONE WORKFLOWS

### SETTIMANA 1: A.D.A. CORE
- [x] Giorno 1-2: Implementa A.D.A. Main Agent + Tools 1-2
- [ ] Giorno 3-4: Implementa Tools 3-4 (Risk + Solar)
- [ ] Giorno 5-6: Implementa Tools 5-6 (RAG + Premium)
- [ ] Giorno 7: Testing end-to-end + fix bugs

### SETTIMANA 2: SOLAR + POLISH A.D.A.
- [ ] Giorno 8-9: Implementa Solar Panel Detection
- [ ] Giorno 10: Run batch detection su high-value clients
- [ ] Giorno 11: Ottimizzazione A.D.A. (caching, error handling)

### SETTIMANA 3: NBO MODULE
- [ ] Giorno 12: Setup DB + Scoring euristico
- [ ] Giorno 13-14: Batch workflow + Testing
  - [ ] Se modelli ML pronti → Integra
  - [ ] Altrimenti → Deploy euristico

### SETTIMANA 4: POLISH & DEPLOYMENT
- [ ] Giorno 15-17: Frontend Streamlit overhaul
- [ ] Giorno 18-19: Testing integrazione completa
- [ ] Giorno 20-21: Bug fixing + Documentazione

---

## 📋 CHECKLIST FINALE PRE-DEMO

### Workflows n8n
- [ ] A.D.A. Main Agent: Attivo ✅
- [ ] 6 A.D.A. Tools: Tutti funzionanti ✅
- [ ] Solar Detection: Eseguito su 500+ clienti ✅
- [ ] NBO Batch Scoring: Eseguito e aggiornato ✅
- [ ] Tutti workflows production: Non-archived ✅

### Database Supabase
- [ ] Tabelle popolate: clienti, polizze, sinistri, abitazioni ✅
- [ ] Embeddings: 41,176 records in interactions ✅
- [ ] Risk scores: ≥ 4,500 abitazioni con score ✅
- [ ] NBO scores: ≥ 5,000 client-product combinations ✅
- [ ] Solar detection: ≥ 500 abitazioni con has_solar_panels ✅

### Streamlit Dashboard
- [ ] Mappa PyDeck: Rendering 3D con layers ✅
- [ ] A.D.A. Chat: Webhook connesso e funzionante ✅
- [ ] NBO Dashboard: Top 50 visualizzati ✅
- [ ] Performance: Load time < 2 sec ✅

### Testing
- [ ] 10 query A.D.A. testate con successo ✅
- [ ] 3 scenari demo preparati e scriptati ✅
- [ ] Backup database eseguito ✅

---

## 🎯 PROSSIMI STEP IMMEDIATI

### 🔴 OGGI (Giorno 1):
1. ✅ Audit workflows completato (questo documento)
2. 🚀 **INIZIARE:** Implementazione A.D.A. Main Agent
   - Creare workflow base con webhook
   - Implementare Tool 1: client_profile_lookup
   - Implementare Tool 2: policy_status_check
   - Test basico con Postman/Streamlit

### 📅 DOMANI (Giorno 2):
- Implementare Tool 3: risk_assessment
- Implementare Tool 4: solar_potential_calc (usa workflow esistente)
- Testing integrazione tools 1-4

### 📅 DOPODOMANI (Giorno 3):
- Implementare Tool 5: doc_retriever_rag (query vettoriale)
- Implementare Tool 6: premium_calculator
- Testing completo A.D.A. con tutti tools

---

**STATUS REPORT:**
✅ **15/24 workflows production pronti (62.5%)**  
🚧 **9 workflows mancanti per 100% completamento**  
🎯 **Stima completamento: 14-21 giorni**

Vuoi che inizi con l'implementazione del workflow A.D.A. Main Agent?
