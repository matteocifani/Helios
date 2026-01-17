# 📊 INTEGRAZIONE MODULO NBO - PROGETTO HELIOS

**Autore Modulo NBO:** [Collega del team]  
**Integrazione Helios:** Matteo Cifani  
**Data:** 15 Gennaio 2026

---

## 🎯 OBIETTIVO MODULO NBO

Il modulo **Next Best Offer (NBO)** fornisce un sistema di scoring intelligente per identificare le migliori opportunità di cross-selling/up-selling nel portafoglio clienti di Vita Sicura.

**Output Principale:**
Una classifica dinamica di coppie `(cliente, prodotto)` ordinata per **score NBO**, che rappresenta la probabilità di successo e il valore della vendita.

---

## 🧮 FORMULA SCORING

```
Score(cliente, prodotto) = 
  w₁ · Compatibilità_Cluster +
  w₂ · Redditività +
  w₃ · Retention_Gain +
  w₄ · Prob_Conversione
```

### Pesi Default (Configurabili)
- `w₁ = 0.40` → Affinità anagrafica (clustering)
- `w₂ = 0.30` → Margine economico prodotto
- `w₃ = 0.20` → Impatto su retention (anti-churn)
- `w₄ = 0.10` → Probabilità conversione

### Range Valori
- **Score NBO**: 0-100 (target vendite: score > 70)
- **Compatibilità**: 0-100 (da clustering + penetrazione prodotto)
- **Redditività**: 0-100 (normalizzata su margine medio)
- **Retention Gain**: 0-100 (delta churn probability)
- **Prob Conversione**: 0-100 (da modello predittivo o euristica)

---

## 🗄️ ARCHITETTURA DATABASE

### Schema Tabelle NBO

#### 1. Tabella Principale: `nba_scores_master`
```sql
CREATE TABLE nba_scores_master (
  id SERIAL PRIMARY KEY,
  codice_cliente INTEGER NOT NULL REFERENCES clienti(codice_cliente),
  prodotto TEXT NOT NULL,
  area_bisogno TEXT,
  
  -- Score Finale
  score_nbo NUMERIC(5,2) NOT NULL CHECK (score_nbo BETWEEN 0 AND 100),
  
  -- Componenti Score (per trasparenza)
  compatibilita_cluster NUMERIC(5,2),
  redditivita NUMERIC(5,2),
  retention_gain NUMERIC(5,2),
  prob_conversione NUMERIC(5,2),
  
  -- Metadata Clustering
  cluster_id INTEGER,
  cluster_penetration NUMERIC(5,4), -- % clienti cluster con questo prodotto
  
  -- Metadata Churn
  churn_prima NUMERIC(5,4),  -- Churn prob attuale
  churn_dopo NUMERIC(5,4),   -- Churn prob stimata post-vendita
  delta_churn NUMERIC(5,4),  -- Differenza (retention gain)
  
  -- Tracking
  calculated_at TIMESTAMP DEFAULT NOW(),
  data_version TEXT, -- Es: "2026-01-15_v1.2"
  
  -- Constraint
  CONSTRAINT unique_client_product UNIQUE (codice_cliente, prodotto)
);

-- Indici per performance
CREATE INDEX idx_nba_score_desc ON nba_scores_master(score_nbo DESC);
CREATE INDEX idx_nba_cliente ON nba_scores_master(codice_cliente);
CREATE INDEX idx_nba_prodotto ON nba_scores_master(prodotto);
CREATE INDEX idx_nba_cluster ON nba_scores_master(cluster_id);
CREATE INDEX idx_nba_calculated ON nba_scores_master(calculated_at DESC);
```

#### 2. Tabella Supporto: `ml_models`
```sql
CREATE TABLE ml_models (
  id SERIAL PRIMARY KEY,
  model_name TEXT UNIQUE NOT NULL, -- Es: "clustering_v1", "churn_glm_v2"
  model_type TEXT, -- "clustering", "regression", "classifier"
  
  -- Coefficienti/Parametri
  coefficients JSONB, -- Struttura flessibile per salvare params
  
  -- Metadata
  trained_at TIMESTAMP DEFAULT NOW(),
  accuracy_metrics JSONB, -- Es: {"r2": 0.85, "mae": 0.12}
  training_data_version TEXT,
  
  -- Lifecycle
  is_active BOOLEAN DEFAULT TRUE,
  replaced_by INTEGER REFERENCES ml_models(id)
);

-- Esempio record clustering
INSERT INTO ml_models (model_name, model_type, coefficients) VALUES (
  'clustering_kmeans_v1',
  'clustering',
  '{
    "n_clusters": 5,
    "centroids": [...],
    "feature_columns": ["eta", "reddito", "num_polizze", "zona_residenza_encoded"]
  }'::jsonb
);

-- Esempio record churn GLM
INSERT INTO ml_models (model_name, model_type, coefficients) VALUES (
  'churn_glm_v1',
  'regression',
  '{
    "intercept": 0.35,
    "coefficients": {
      "num_polizze": -0.082,
      "satisfaction_score": -0.045,
      "reclami_totali": 0.031,
      "engagement_score": -0.028
    }
  }'::jsonb
);
```

#### 3. Tabella Supporto: `cluster_product_penetration`
```sql
CREATE TABLE cluster_product_penetration (
  cluster_id INTEGER NOT NULL,
  prodotto TEXT NOT NULL,
  
  -- Statistiche
  total_clients INTEGER, -- Clienti totali nel cluster
  clients_with_product INTEGER, -- Clienti che hanno il prodotto
  penetration_rate NUMERIC(5,4), -- % = clients_with_product / total_clients
  
  -- Metadata
  calculated_at TIMESTAMP DEFAULT NOW(),
  
  PRIMARY KEY (cluster_id, prodotto)
);

-- Esempio calcolo penetrazione
INSERT INTO cluster_product_penetration 
SELECT 
  c.cluster_risposta::INTEGER as cluster_id,
  p.prodotto,
  COUNT(DISTINCT c.codice_cliente) as total_clients,
  COUNT(DISTINCT p.codice_cliente) as clients_with_product,
  ROUND(COUNT(DISTINCT p.codice_cliente)::NUMERIC / 
        NULLIF(COUNT(DISTINCT c.codice_cliente), 0), 4) as penetration_rate,
  NOW() as calculated_at
FROM clienti c
LEFT JOIN polizze p ON c.codice_cliente = p.codice_cliente 
  AND p.stato_polizza = 'Attiva'
GROUP BY c.cluster_risposta, p.prodotto;
```

---

## 🔄 FREQUENZA AGGIORNAMENTI

### Layer 1: Modelli ML (Batch Schedulato)

| Processo | Frequenza | Trigger | Tempo Esecuzione |
|----------|-----------|---------|------------------|
| **Clustering Clienti** | Mensile | 1° giorno del mese, 3:00 AM | ~30 min |
| **Modello Churn GLM** | Mensile | 1° giorno del mese, 4:00 AM | ~20 min |
| **Penetrazione Cluster** | Mensile | 1° giorno del mese, 5:00 AM | ~5 min |
| **Redditività Prodotti** | Trimestrale | Fine trimestre | ~10 min |

### Layer 2: Scoring NBO

| Processo | Frequenza | Trigger | Volume |
|----------|-----------|---------|---------|
| **Batch Notturno** | Giornaliero | 2:00 AM | Solo clienti modificati (stima: 50-200/giorno) |
| **On-Demand Trigger** | Real-time | Vendita polizza, modifica cliente | 1 cliente |
| **Full Recalculation** | Mensile | Post-training modelli | Tutti i clienti (~11,000) |

**Workflow Batch Notturno:**
```sql
-- Identifica clienti da ricalcolare
WITH modified_clients AS (
  SELECT DISTINCT codice_cliente 
  FROM clienti 
  WHERE updated_at > NOW() - INTERVAL '24 hours'
  
  UNION
  
  SELECT DISTINCT codice_cliente
  FROM polizze
  WHERE updated_at > NOW() - INTERVAL '24 hours'
)
SELECT * FROM modified_clients;
-- → Passa a scoring workflow
```

---

## 🔧 IMPLEMENTAZIONE N8N

### Workflow 1: "NBO - Monthly Model Training"

**Trigger:** Schedule - 1st day of month, 3:00 AM

**Nodes:**
```
[1. Manual/Schedule Trigger]
    ↓
[2. Execute Python: Clustering]
    • Script: clustering_kmeans.py
    • Input: clienti table export
    • Output: cluster_assignments.json + centroids
    ↓
[3. Update Clienti Table]
    • UPDATE clienti SET cluster_risposta = $1
    ↓
[4. Execute Python: Churn GLM]
    • Script: churn_glm_training.py
    • Input: clienti + polizze + sinistri
    • Output: glm_coefficients.json
    ↓
[5. Update ml_models Table]
    • UPSERT coefficients
    ↓
[6. Calculate Penetration]
    • SQL Query → cluster_product_penetration
    ↓
[7. Trigger Full Scoring]
    • Execute Workflow: "NBO - Batch Scoring"
```

**Note Python Execution:**
- **Opzione A:** n8n Code node con `numpy`, `scikit-learn` pre-installati
- **Opzione B:** HTTP Request a Python API Flask/FastAPI separata
- **Opzione C:** Execute Command (`python3 /scripts/clustering.py`)

### Workflow 2: "NBO - Batch Scoring"

**Trigger:** 
- Schedule Daily 2:00 AM
- Manual trigger
- Called by Workflow 1

**Nodes:**
```
[1. Trigger]
    ↓
[2. Get Modified Clients]
    • Query SQL (vedi sopra)
    ↓
[3. Get ML Model Coefficients]
    • Query ml_models table (latest active)
    ↓
[4. Loop Clients] (Split in Batches: 100)
    ↓
    [5. Get Client Full Profile]
        • Query clienti + polizze + abitazioni
        ↓
    [6. Get Available Products]
        • ALL_PRODUCTS - polizze_attuali
        ↓
    [7. For Each Product: Calculate Score]
        • Code Node (JavaScript/Python)
        • Input: client data, product, model coefficients
        • Logic:
          a. compatibilita = getPenetration(cluster, product)
          b. redditivita = getProductMargin(product)
          c. retention_gain = calculateChurnDelta(client, product, glm_coeffs)
          d. prob_conversione = heuristic or ML model
          e. score_nbo = weighted_sum(a, b, c, d)
        • Output: JSON score object
        ↓
    [8. UPSERT nba_scores_master]
        • ON CONFLICT (codice_cliente, prodotto) DO UPDATE
    ↓
[9. Log Completion]
    • Insert into log_nbo_batch
```

**Calcolo Dettagliato Retention Gain (JavaScript):**
```javascript
function calculateRetentionGain(clientData, productData, glmCoeffs) {
  // Churn attuale del cliente
  const churnPrima = clientData.churn_probability || 0.35; // default 35%
  
  // Simula impatto nuovo prodotto
  const numPolizzeAttuali = clientData.num_polizze || 1;
  const numPolizzeDopo = numPolizzeAttuali + 1;
  
  // Applica coefficienti GLM
  const deltaChurn = glmCoeffs.coefficients.num_polizze * 1; // +1 polizza
  const churnDopo = Math.max(0, Math.min(1, churnPrima + deltaChurn));
  
  // Normalizza retention gain a 0-100
  const retentionGain = ((churnPrima - churnDopo) / churnPrima) * 100;
  
  return {
    churn_prima: churnPrima,
    churn_dopo: churnDopo,
    delta_churn: churnPrima - churnDopo,
    retention_gain: Math.max(0, Math.min(100, retentionGain))
  };
}
```

### Workflow 3: "NBO - On-Demand Trigger"

**Trigger:** Webhook `/webhook/nbo-recalc`

**Payload:**
```json
{
  "codice_cliente": 12345,
  "reason": "new_policy_sold" // or "client_updated"
}
```

**Nodes:**
```
[1. Webhook Trigger]
    ↓
[2. Validate Client Exists]
    ↓
[3. Execute Same Logic as Batch]
    • But for single client only
    ↓
[4. Return Updated Scores]
    • Query nba_scores_master WHERE codice_cliente = $1
    • Return top 3 offers
```

---

## 🤖 INTEGRAZIONE A.D.A.

### Tool A.D.A.: `get_next_best_offer`

**Workflow:** "A.D.A. Tool - NBO"

**Input:**
```json
{
  "client_id": 12345,
  "top_n": 3,
  "min_score": 70
}
```

**Query SQL:**
```sql
SELECT 
  prodotto,
  area_bisogno,
  score_nbo,
  compatibilita_cluster,
  redditivita,
  retention_gain,
  prob_conversione,
  churn_prima,
  churn_dopo,
  delta_churn,
  calculated_at
FROM nba_scores_master
WHERE codice_cliente = $1
  AND score_nbo >= $2
ORDER BY score_nbo DESC
LIMIT $3
```

**Output Format (per A.D.A.):**
```json
{
  "codice_cliente": 12345,
  "timestamp": "2026-01-15T10:30:00Z",
  "raccomandazioni": [
    {
      "area_bisogno": "Previdenza",
      "prodotto": "Futuro Sicuro",
      "score_nbo": 78.5,
      "componenti": {
        "retention_gain": 85.2,
        "redditivita": 90.0,
        "propensione": 65.0,
        "affinita_cluster": 52.5
      },
      "dettagli": {
        "delta_churn": 0.0452,
        "churn_prima": 0.3500,
        "churn_dopo": 0.3048
      }
    }
  ],
  "metadata": {
    "churn_attuale": 0.35,
    "num_polizze_attuali": 2,
    "cluster": 2
  }
}
```

**A.D.A. System Prompt Enhancement:**
```
TOOL: get_next_best_offer
Quando l'utente chiede "quale prodotto consigliare", "prossima vendita", 
"opportunità cross-sell", usa questo tool.

COME PRESENTARE RISULTATI:
1. Top 3 prodotti con score
2. Focus su PERCHÉ è adatto (cluster affinity)
3. Beneficio RETENTION: "Riduce rischio churn del X%"
4. Beneficio ECONOMICO: "Margine stimato €Y"

ESEMPIO RISPOSTA:
"Per il cliente Mario Rossi, ecco le 3 migliori opportunità:

🥇 **Futuro Sicuro** (Score: 78.5/100)
   • Molto popolare nel suo cluster (52% penetrazione)
   • Riduce rischio churn del 12.9% (da 35% a 30.5%)
   • Margine stimato: €420/anno

🥈 **Casa Serena** (Score: 76.3/100)
   ...
```

---

## 📊 DASHBOARD STREAMLIT NBO

### Tab: "NBO Dashboard"

**Layout:**
```python
import streamlit as st
import pandas as pd

st.title("🎯 Next Best Offer Dashboard")

# Filtri
col1, col2, col3 = st.columns(3)
with col1:
    min_score = st.slider("Score Minimo", 0, 100, 70)
with col2:
    area_filter = st.multiselect("Area Bisogno", 
                                  ["Previdenza", "Protezione", "Risparmio", "Salute"])
with col3:
    product_filter = st.multiselect("Prodotto", 
                                     ["Futuro Sicuro", "Casa Serena", ...])

# Query
query = f"""
SELECT 
  n.codice_cliente,
  c.nome || ' ' || c.cognome as cliente,
  c.agenzia,
  n.prodotto,
  n.area_bisogno,
  n.score_nbo,
  n.compatibilita_cluster,
  n.redditivita,
  n.retention_gain,
  c.clv_stimato,
  n.calculated_at
FROM nba_scores_master n
JOIN clienti c ON n.codice_cliente = c.codice_cliente
WHERE n.score_nbo >= {min_score}
  {'AND n.area_bisogno IN (' + ','.join(["'" + a + "'" for a in area_filter]) + ')' if area_filter else ''}
  {'AND n.prodotto IN (' + ','.join(["'" + p + "'" for p in product_filter]) + ')' if product_filter else ''}
ORDER BY n.score_nbo DESC
LIMIT 100
"""

df = fetch_data(query)

# KPI Cards
col1, col2, col3, col4 = st.columns(4)
col1.metric("Opportunità Totali", len(df))
col2.metric("Score Medio", f"{df['score_nbo'].mean():.1f}")
col3.metric("Valore Potenziale", f"€{df['clv_stimato'].sum():,.0f}")
col4.metric("Agenti Coinvolti", df['agenzia'].nunique())

# Tabella Interattiva
st.dataframe(
    df,
    column_config={
        "score_nbo": st.column_config.ProgressColumn(
            "Score NBO",
            format="%.1f",
            min_value=0,
            max_value=100
        ),
        "clv_stimato": st.column_config.NumberColumn(
            "CLV Cliente",
            format="€%.0f"
        )
    },
    hide_index=True,
    use_container_width=True
)

# Export
if st.button("📥 Export CSV per CRM"):
    csv = df.to_csv(index=False)
    st.download_button("Download", csv, "nbo_opportunities.csv", "text/csv")

# Drill-down
selected_row = st.selectbox("Approfondisci cliente:", df['cliente'].unique())
if selected_row:
    client_id = df[df['cliente'] == selected_row]['codice_cliente'].iloc[0]
    st.subheader(f"Dettaglio: {selected_row}")
    
    # Trigger A.D.A. analysis
    if st.button("🤖 Chiedi ad A.D.A. analisi completa"):
        # Call A.D.A. webhook
        result = call_ada(f"Analizza opportunità NBO per cliente {client_id}")
        st.write(result)
```

**Visualizzazioni Aggiuntive:**

1. **Heatmap Prodotti per Cluster:**
```python
import plotly.express as px

pivot = df.groupby(['cluster_id', 'prodotto'])['score_nbo'].mean().reset_index()
pivot_table = pivot.pivot(index='cluster_id', columns='prodotto', values='score_nbo')

fig = px.imshow(pivot_table, 
                color_continuous_scale='RdYlGn',
                labels={'color': 'Avg Score'})
st.plotly_chart(fig)
```

2. **Distribuzione Score NBO:**
```python
fig = px.histogram(df, x='score_nbo', nbins=20,
                   title="Distribuzione Score NBO")
st.plotly_chart(fig)
```

---

## 🧪 TESTING & VALIDAZIONE

### Test Cases NBO Scoring

**Test 1: Cliente Multi-Polizza con Basso Churn**
```
Input:
  - Cliente: ID 1234
  - Polizze attuali: Vita + Casa
  - Churn prob: 0.15 (basso)
  - Cluster: 3

Expected:
  - Score NBO per "Salute": 60-70 (ritenzione già alta)
  - Score NBO per "Investimento": 75-85 (affinità cluster alta)
```

**Test 2: Cliente High Churn, Zero Polizze Attive**
```
Input:
  - Cliente: ID 5678
  - Polizze attuali: 0
  - Churn prob: 0.65 (alto)
  - Cluster: 1

Expected:
  - Score NBO per qualsiasi prodotto: 80+ (alta retention urgenza)
  - Top prodotto: Quello con maggiore penetrazione cluster
```

**Test 3: Scoring Consistency**
```
Run batch scoring 2 volte consecutive senza modifiche dati.
Expected: Score identici (idempotenza)
```

### Validation Metrics

```sql
-- Check distribuzione score
SELECT 
  CASE 
    WHEN score_nbo >= 80 THEN 'Eccellente (≥80)'
    WHEN score_nbo >= 70 THEN 'Buono (70-79)'
    WHEN score_nbo >= 60 THEN 'Medio (60-69)'
    ELSE 'Basso (<60)'
  END as categoria,
  COUNT(*) as n_opportunita,
  ROUND(AVG(score_nbo), 1) as avg_score
FROM nba_scores_master
GROUP BY categoria
ORDER BY avg_score DESC;

-- Check prodotti più raccomandati
SELECT 
  prodotto,
  COUNT(*) as n_raccomandazioni,
  ROUND(AVG(score_nbo), 1) as avg_score,
  COUNT(DISTINCT codice_cliente) as clienti_unici
FROM nba_scores_master
WHERE score_nbo >= 70
GROUP BY prodotto
ORDER BY n_raccomandazioni DESC;
```

---

## ⚙️ CONFIGURAZIONE & TUNING

### Config File: `nbo_config.json`
```json
{
  "scoring_weights": {
    "compatibilita": 0.40,
    "redditivita": 0.30,
    "retention": 0.20,
    "conversione": 0.10
  },
  "thresholds": {
    "min_score_display": 70,
    "high_opportunity": 80,
    "min_cluster_penetration": 0.05
  },
  "batch_settings": {
    "schedule": "0 2 * * *",
    "batch_size": 100,
    "timeout_seconds": 3600
  },
  "model_settings": {
    "clustering": {
      "n_clusters": 5,
      "features": ["eta", "reddito", "num_polizze", "zona_residenza"]
    },
    "churn_glm": {
      "retraining_frequency": "monthly",
      "min_samples": 1000
    }
  }
}
```

**Caricamento Config in n8n:**
```javascript
// Nodo Code
const fs = require('fs');
const config = JSON.parse(fs.readFileSync('/data/nbo_config.json'));
return { json: config };
```

---

## 🚀 DEPLOYMENT CHECKLIST

- [ ] **Database:**
  - [ ] Tabella `nba_scores_master` creata
  - [ ] Tabella `ml_models` creata
  - [ ] Tabella `cluster_product_penetration` creata
  - [ ] Indici ottimizzati
  
- [ ] **Modelli ML:**
  - [ ] Clustering eseguito e salvato
  - [ ] Churn GLM addestrato e coefficienti salvati
  - [ ] Penetrazione cluster calcolata
  
- [ ] **Workflows n8n:**
  - [ ] "NBO - Monthly Model Training" implementato e testato
  - [ ] "NBO - Batch Scoring" implementato e testato
  - [ ] "NBO - On-Demand Trigger" implementato
  - [ ] Schedule configurati correttamente
  
- [ ] **Integrazione A.D.A.:**
  - [ ] Tool `get_next_best_offer` implementato
  - [ ] System prompt aggiornato
  - [ ] Testing conversazioni NBO
  
- [ ] **Dashboard Streamlit:**
  - [ ] Tab NBO creata
  - [ ] Filtri funzionanti
  - [ ] Export CSV operativo
  - [ ] Visualizzazioni renderizzate
  
- [ ] **Testing:**
  - [ ] 3 test cases passati
  - [ ] Validation metrics verificate
  - [ ] Performance < 30 sec per batch 100 clienti

---

## 📈 ROADMAP EVOLUTIVA

### Fase 1: MVP (Settimana 3)
✅ Scoring euristico senza ML  
✅ Dashboard base  
✅ Tool A.D.A.

### Fase 2: ML Integration (Post-Demo)
- Integrazione modelli clustering e GLM del collega
- A/B testing scoring euristico vs ML
- Tuning pesi componenti

### Fase 3: Advanced Features (Futuro)
- Modello conversione ML (non euristica)
- Feedback loop: tracking vendite effettive post-raccomandazione
- Personalizzazione pesi per agente/area
- API esterna per CRM integration

---

**Status:** 🟡 PRONTO PER IMPLEMENTAZIONE  
**Blocco:** ⚠️ Attendere conferma modelli ML da collega  
**Fallback:** ✅ Scoring euristico documentato e testabile

Vuoi procedere con l'implementazione del MVP NBO (scoring euristico)?
