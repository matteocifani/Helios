# HELIOS - Redesign Completo UX/UI per Agenti Vita Sicura

## Executive Summary

Questo documento contiene il piano completo per il redesign dell'applicazione HELIOS, trasformandola da uno strumento orientato ai dati a uno strumento orientato all'agente assicurativo.

---

## Problema Principale Identificato

La divisione attuale **Helios View** (Geo-Rischio) vs **Helios NBO** (Next Best Offer) non rispecchia il modo in cui un agente assicurativo pensa e lavora.

**Come pensa l'agente:**
- "Chi devo chiamare oggi?"
- "Come sta questo cliente?"
- "Come va il mio portafoglio?"

**Come è strutturata l'app attualmente:**
- "Analisi geo-rischio" vs "Raccomandazioni prodotto"
- Due mondi separati che l'agente deve navigare mentalmente

---

## Analisi Features Attuali

| Sezione Attuale | Feature | Utilità Reale per Agente |
|-----------------|---------|--------------------------|
| Helios View > Mappa | Heatmap rischio territoriale | **MEDIA** - utile per overview strategica |
| Helios View > Analytics | Grafici distribuzione rischio | **BASSA** - informazioni aggregate poco actionable |
| Helios View > Dettaglio Clienti | Ricerca e scheda cliente | **ALTA** - core dell'attività |
| Helios View > A.D.A. Chat | Assistente AI | **ALTA** - supporto operativo |
| Helios NBO > Top 20 | Lista prioritizzata clienti | **ALTA** - guida l'azione quotidiana |
| Helios NBO > Top 5 | Azioni prioritarie | **ALTA** - focus immediato |
| Helios NBO > Dettaglio | Scheda cliente + form chiamata | **ALTA** - esecuzione operativa |
| Helios NBO > Analytics | Grafici NBO | **BASSA** - poco actionable |

---

## Nuova Architettura: "Agent-Centric"

### Filosofia di Design
**"Ogni schermata deve rispondere a una domanda che l'agente si pone durante la giornata lavorativa"**

### Nuova Navigazione (Sidebar)

```
┌─────────────────────────────┐
│  HELIOS                     │
│  Vita Sicura Intelligence   │
├─────────────────────────────┤
│  📋 AZIONI DEL GIORNO       │  ← Default landing page
├─────────────────────────────┤
│  🔍 CERCA CLIENTE           │
├─────────────────────────────┤
│  📊 IL MIO PORTAFOGLIO      │
├─────────────────────────────┤
│  🗺️ MAPPA TERRITORIALE      │
├─────────────────────────────┤
│  🛰️ ANALISI SATELLITARE     │  ← NUOVA FEATURE
├─────────────────────────────┤
│  🤖 A.D.A. Assistente       │  ← Floating button sempre visibile
└─────────────────────────────┘
```

---

## Sezione 1: AZIONI DEL GIORNO (Home Page)

### Scopo
Guidare l'agente verso le attività più impattanti della giornata

### Layout Proposto

```
┌─────────────────────────────────────────────────────────────┐
│  Buongiorno, [Nome Agente]                    📅 17 Gen 2026│
│  Hai 5 azioni prioritarie per oggi                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  🎯 TOP 5 CLIENTI DA CONTATTARE                             │
│                                                             │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐│
│  │ Mario R.│ │ Laura B.│ │ Franco │ │ Giulia │ │ Andrea │││
│  │ Score 92│ │ Score 87│ │ Score 83│ │ Score 79│ │ Score 76│││
│  │ Risparm.│ │ Protez. │ │ Casa   │ │ Salute │ │ Previd.│││
│  │         │ │         │ │        │ │        │ │        │││
│  │ [CHIAMA]│ │ [CHIAMA]│ │ [CHIAMA]│ │ [CHIAMA]│ │ [CHIAMA]│││
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘│
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  📊 SINTESI RAPIDA                                          │
│                                                             │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│  │ 23 Chiamate  │ │ 5 Polizze    │ │ €45K Raccolta│        │
│  │ questa sett. │ │ chiuse mese  │ │ questo mese  │        │
│  └──────────────┘ └──────────────┘ └──────────────┘        │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ⚠️ ALERT & SCADENZE                                        │
│                                                             │
│  • 3 polizze in scadenza nei prossimi 30 giorni            │
│  • 2 clienti ad alto rischio churn                         │
│  • 1 reclamo aperto da gestire                             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Elementi Chiave
- **Top 5 come card cliccabili** - Un click apre la scheda cliente
- **Bottone "Chiama"** diretto su ogni card
- **KPI personali dell'agente** (non del portafoglio generale)
- **Alert proattivi** su situazioni da gestire

### Sidebar Contestuale
- Slider pesi NBO (retention/redditività/propensione)
- Toggle per escludere clienti già contattati
- Filtro per area bisogno (Risparmio, Protezione, etc.)

### Implementazione
1. Riutilizzare la logica di `get_all_recommendations()` da app.py
2. Creare un componente `TopClientCard` riusabile
3. Aggiungere tracking chiamate per i KPI (nuova tabella o campo in `interactions`)
4. Query per alert: polizze in scadenza, churn > threshold, reclami aperti

---

## Sezione 2: SCHEDA CLIENTE 360°

### Scopo
Tutte le informazioni su un cliente in un unico posto

### Layout Proposto

```
┌─────────────────────────────────────────────────────────────┐
│  ← Torna alle Azioni     MARIO ROSSI (CLI_9500)   [🔔][📧] │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌────────────────────┐  ┌──────────────────────────────┐  │
│  │ 📷 FOTO ABITAZIONE │  │ ANAGRAFICA                   │  │
│  │ (da satellite)     │  │                              │  │
│  │                    │  │ Età: 52 • Professione: Libero│  │
│  │                    │  │ CLV: €12.500 • Cluster: A2   │  │
│  │ [Analizza con AI]  │  │ Churn Risk: 23% 🟢           │  │
│  └────────────────────┘  └──────────────────────────────┘  │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  TABS: [Polizze] [Rischio] [Storico] [Raccomandazioni]     │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  TAB POLIZZE:                                               │
│  • Casa Serena - €380/anno - Scade 15/06/2026              │
│  • Salute Protetta - €950/anno - Attiva                    │
│                                                             │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  TAB RISCHIO (nuova sezione):                              │
│  • Zona Sismica: 2 (Alto) 🟠                               │
│  • Rischio Idrogeologico: P2 (Medio) 🟡                    │
│  • Score Complessivo: 67/100                               │
│  • 🛰️ Analisi Satellitare: [Piscina rilevata] [Alberi]    │
│                                                             │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  TAB RACCOMANDAZIONI:                                       │
│  🎯 Prodotto consigliato: Futuro Sicuro (Investimento)     │
│  Score: 87 | Retention +15% | Redditività €1.200           │
│                                                             │
│  [📧 Genera Email]  [📞 Registra Chiamata]                 │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  🤖 A.D.A. SUGGERISCE:                                     │
│  "Mario ha un'alta propensione per prodotti di risparmio.  │
│   Considera di proporre Futuro Sicuro durante la prossima  │
│   chiamata, evidenziando la stabilità dei rendimenti."     │
│                                                             │
│  [Chiedi ad A.D.A.]                                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Novità Chiave
- **Immagine satellitare dell'abitazione** con preview
- **Bottone "Analizza con AI"** che apre la sezione Analisi Satellitare
- **Tab Rischio** che integra dati sismici, idro, e computer vision
- **A.D.A. contestuale** che offre suggerimenti proattivi
- **Azioni rapide** (Email, Chiamata) sempre visibili

### Implementazione
1. Creare componente `ClientCard360` che aggrega:
   - Dati da `clienti`
   - Dati da `abitazioni`
   - Dati da `polizze`
   - Raccomandazioni da `nbo_master.json`
2. Integrare Google Maps Static API o Mapbox per immagine satellitare
3. Aggiungere suggerimento A.D.A. automatico basato su contesto
4. Link "Analizza con AI" → Sezione Analisi Satellitare con cliente preselezionato

---

## Sezione 3: IL MIO PORTAFOGLIO

### Scopo
Overview aggregata delle performance dell'agente

### Layout Proposto

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  IL MIO PORTAFOGLIO                                         │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  KPI PRINCIPALI:                                            │
│                                                             │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐    │
│  │ 1.247  │ │ €2.3M  │ │ 12%    │ │ 34%    │ │ 8.2    │    │
│  │ Clienti│ │ CLV Tot│ │ Churn  │ │ Multi- │ │ NPS    │    │
│  │ Attivi │ │        │ │ Risk   │ │ Holding│ │        │    │
│  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘    │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  DISTRIBUZIONE PRODOTTI     │  TREND MENSILE               │
│  [Grafico Donut]            │  [Line Chart Raccolta]       │
│                             │                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  CLIENTI A RISCHIO CHURN (Top 10)                          │
│  [Lista con score e azione suggerita]                      │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  OPPORTUNITÀ CROSS-SELLING                                  │
│  [Lista clienti mono-polizza con alto potenziale]          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Elementi
- KPI aggregati sul proprio portafoglio
- Grafici di distribuzione prodotti (riutilizzare da Analytics attuale)
- Lista clienti ad alto churn risk (actionable)
- Lista opportunità cross-selling

### Implementazione
1. Spostare grafici esistenti da Tab Analytics
2. Aggregare dati per singolo agente (se multi-agente) o globali
3. Aggiungere query per:
   - Top 10 churn risk
   - Clienti mono-polizza con CLV alto

---

## Sezione 4: MAPPA TERRITORIALE

### Scopo
Visualizzazione geografica per pianificazione visite

### Modifiche rispetto alla versione attuale

**RIMUOVERE:**
- Heatmap complessa (poco utile per agente singolo)
- Colorazione per rischio tecnico

**MANTENERE:**
- Mappa con punti dei propri clienti
- Tooltip con info cliente

**AGGIUNGERE:**
- Filtri per pianificare itinerari:
  - "Mostra clienti da visitare questa settimana"
  - "Mostra clienti in zona [città selezionata]"
  - "Mostra clienti con polizza in scadenza"
- Click su punto → Apre scheda cliente
- Colorazione per priorità NBO (non per rischio tecnico)

### Layout Semplificato

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  🗺️ MAPPA TERRITORIALE                                     │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Filtri: [Top 20 NBO ▼] [Città: Tutte ▼] [Scadenze 30gg ☐] │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│                    ┌─────────────────┐                      │
│                    │                 │                      │
│                    │     MAPPA       │                      │
│                    │   (semplice)    │                      │
│                    │                 │                      │
│                    │  🟢 �� 🔴       │                      │
│                    │                 │                      │
│                    └─────────────────┘                      │
│                                                             │
│  Legenda: 🟢 Score alto  🟡 Score medio  🔴 Score basso    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Implementazione
1. Semplificare PyDeck layer (solo ScatterplotLayer)
2. Colorare per NBO score, non per rischio
3. Aggiungere filtri sopra la mappa
4. Click handler → navigare a Scheda Cliente

---

## Sezione 5: ANALISI SATELLITARE (NUOVA - Sezione Dedicata)

### Scopo
Sfruttare la computer vision per arricchire i dati - **massima visibilità sulla feature innovativa**

### Layout Proposto

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  🛰️ ANALISI SATELLITARE                                    │
│  Estrai informazioni dalle immagini per migliorare il      │
│  pricing e la valutazione del rischio                      │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  CERCA ABITAZIONE:                                          │
│  [Input: Codice cliente o indirizzo___________] [🔍 Cerca] │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────────┐  ┌──────────────────────────────┐│
│  │                      │  │                              ││
│  │ 📷 IMMAGINE          │  │ FEATURES ESTRATTE            ││
│  │ SATELLITARE          │  │                              ││
│  │                      │  │ ✓ Piscina rilevata           ││
│  │ [Vista dall'alto     │  │ ✓ Pannelli solari            ││
│  │  dell'abitazione]    │  │ ✗ Alberi sul tetto           ││
│  │                      │  │ ✓ Giardino ampio             ││
│  │                      │  │ ✓ Tetto in buone condizioni  ││
│  │                      │  │                              ││
│  │ [Zoom] [Street View] │  │ Confidence: 94%              ││
│  │                      │  │                              ││
│  └──────────────────────┘  └──────────────────────────────┘│
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  IMPATTO SUL PRICING:                                       │
│                                                             │
│  • Premio attuale Casa Serena: €380                        │
│  • Premio suggerito (con features): €425 (+12%)            │
│  • Motivazione: Piscina (+8%), Tetto vecchio (+4%)         │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  📊 ANALISI BATCH (Funzionalità avanzata)                  │
│                                                             │
│  Seleziona più abitazioni per analisi massiva:             │
│  [📋 Seleziona da lista] oppure [📁 Carica CSV indirizzi]  │
│                                                             │
│  [▶️ Avvia Analisi Batch]                                  │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  [💾 Salva Analisi]  [📧 Invia Report]  [🔄 Ricalcola]     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Vantaggi della Sezione Separata
- **Visibilità massima** sulla feature innovativa (punto di forza per la challenge)
- **Analisi batch** su multiple abitazioni (non possibile se integrata in scheda cliente)
- **Focus dedicato** per pricing review e perizie
- **Workflow separato** per team pricing vs team commerciale

### Features da Estrarre dall'Immagine (Computer Vision)
- Presenza piscina
- Pannelli solari
- Alberi che si sovrappongono al tetto
- Dimensione giardino
- Stato del tetto (colore, materiale, condizioni)
- Tipo di edificio (villa, condominio, etc.)
- Presenza garage/posto auto

### Implementazione
1. **Fase 1**: Mostrare immagine satellitare (Google Maps Static API o Mapbox)
2. **Fase 2**: Checklist manuale features (l'agente le compila a mano)
3. **Fase 3**: Integrazione AI per estrazione automatica features
4. **Fase 4**: Calcolo impatto pricing basato su features

### Collegamento con Scheda Cliente
La Scheda Cliente 360° contiene un **link rapido** "🛰️ Analizza abitazione" che apre questa sezione con il cliente preselezionato.

---

## Sezione 6: A.D.A. ASSISTENTE (Floating)

### Scopo
Assistente AI sempre accessibile, con contesto automatico

### Implementazione: Floating Chat Button

```
                                              ┌──────────────────┐
                                              │ 🤖 A.D.A.        │
                                              │                  │
                                              │ Chat history...  │
                                              │                  │
                                              │ [Input message]  │
                                              └──────────────────┘
                                                        ↑
                                              ┌─────────┴─────────┐
                                              │                   │
                                              │   🤖              │ ← Floating button
                                              │                   │
                                              └───────────────────┘
```

### Comportamento
1. **Bottone fisso** in basso a destra (sempre visibile)
2. **Click** espande il pannello chat
3. **Contesto automatico**: se l'utente è sulla Scheda Cliente, A.D.A. ha già il contesto
4. **Suggerimenti proattivi**: A.D.A. può mostrare un badge quando ha suggerimenti

### Implementazione
1. Creare componente `FloatingChat` con CSS position:fixed
2. Passare contesto da `st.session_state` (es. `current_client_id`)
3. Modificare `src/ada/chat.py` per accettare contesto iniziale
4. Aggiungere suggerimenti proattivi basati su pagina corrente

---

## Elementi da RIMUOVERE o Spostare

| Elemento Attuale | Decisione | Motivazione |
|------------------|-----------|-------------|
| Toggle Helios View/NBO | **RIMUOVERE** | Navigazione unificata |
| Analytics tab in Helios View | **SPOSTARE** in "Il Mio Portafoglio" | Aggregato utile solo lì |
| Analytics tab in NBO | **RIMUOVERE** | Poco actionable |
| Heatmap complessa | **SEMPLIFICARE** | Troppo tecnica per agente |
| Filtri sidebar (città/rischio/zona) | **CONTESTUALIZZARE** | Solo dove servono |
| Connessioni status (Supabase, INGV, etc.) | **RIMUOVERE** | Non rilevante per agente |
| Distribuzione zone sismiche (grafico) | **SPOSTARE** in scheda cliente | Utile solo a livello individuale |
| CLV vs Risk scatter plot | **RIMUOVERE** | Troppo analitico |

---

## Elementi da POTENZIARE

| Elemento | Potenziamento |
|----------|---------------|
| Top 5/Top 20 NBO | Landing page principale, card cliccabili |
| Scheda Cliente | Aggiungere immagine satellitare + A.D.A. contestuale |
| Form Chiamata | Semplificare, aggiungere quick notes |
| Ricerca Cliente | Search bar sempre visibile o sezione dedicata |
| A.D.A. | Floating button + contesto automatico |

---

## Flusso Utente Tipico (Redesigned)

```
1. Agente apre HELIOS
   ↓
2. Vede "AZIONI DEL GIORNO" con Top 5 clienti
   ↓
3. Clicca su primo cliente (Mario Rossi)
   ↓
4. Si apre SCHEDA CLIENTE 360°
   - Vede raccomandazione: Futuro Sicuro
   - Legge suggerimento A.D.A.
   - Clicca "Genera Email" per preparare comunicazione
   ↓
5. Clicca "Registra Chiamata"
   - Compila esito: Positivo
   - Note: "Interessato, richiamarlo venerdì"
   ↓
6. Torna a AZIONI DEL GIORNO
   - Mario Rossi non è più in Top 5
   - Passa al secondo cliente
   ↓
7. (Opzionale) Apre MAPPA TERRITORIALE
   - Pianifica giro visite per domani
   ↓
8. Fine giornata: consulta IL MIO PORTAFOGLIO
   - Vede KPI aggiornati
```

---

## Piano di Implementazione Dettagliato

### Fase 1: Ristrutturazione Navigazione (Priorità ALTA)

**File da modificare:** `app.py`

**Azioni:**
1. Rimuovere il toggle `dashboard_mode` (Helios View / Helios NBO)
2. Creare variabile `current_page` con valori:
   - `"azioni_giorno"` (default)
   - `"cerca_cliente"`
   - `"portafoglio"`
   - `"mappa"`
   - `"satellite"`
3. Implementare navigazione sidebar con radio button o st.selectbox
4. Creare routing con `if/elif` per ogni pagina

**Codice esempio:**
```python
# Sidebar navigation
with st.sidebar:
    st.markdown("### 📋 Navigazione")
    current_page = st.radio(
        "Seleziona sezione",
        ["📋 Azioni del Giorno", "🔍 Cerca Cliente", "📊 Il Mio Portafoglio",
         "🗺️ Mappa Territoriale", "🛰️ Analisi Satellitare"],
        label_visibility="collapsed"
    )

# Main content routing
if "Azioni del Giorno" in current_page:
    render_azioni_giorno()
elif "Cerca Cliente" in current_page:
    render_cerca_cliente()
# etc.
```

---

### Fase 2: AZIONI DEL GIORNO (Priorità ALTA)

**File da modificare:** `app.py`

**Azioni:**
1. Creare funzione `render_azioni_giorno()`
2. Portare la logica di Top 5 NBO come elemento principale
3. Creare componente card cliccabile per ogni cliente
4. Aggiungere sezione KPI agente (placeholder se dati non disponibili)
5. Aggiungere sezione Alert

**Dati necessari:**
- `get_all_recommendations()` già esiste
- KPI agente: da implementare (o mostrare placeholder)
- Alert: query su polizze in scadenza, churn alto, reclami

**Codice esempio per card:**
```python
def render_client_card(rec, rank):
    score_color = "#10B981" if rec['score'] >= 70 else "#F59E0B" if rec['score'] >= 50 else "#EF4444"
    st.markdown(f"""
    <div class="top-client-card" onclick="...">
        <span class="rank-badge">TOP {rank}</span>
        <h4>{rec['nome']} {rec['cognome']}</h4>
        <p class="score" style="color: {score_color}">{rec['score']:.0f}</p>
        <p class="product">{rec['area_bisogno']}</p>
    </div>
    """, unsafe_allow_html=True)

    if st.button(f"📞 Chiama", key=f"call_{rec['codice_cliente']}"):
        st.session_state.selected_client = rec
        st.session_state.current_page = "client_detail"
        st.rerun()
```

---

### Fase 3: SCHEDA CLIENTE 360° (Priorità ALTA)

**File da modificare:** `app.py` + nuovo file `src/components/client_detail.py`

**Azioni:**
1. Creare funzione `render_client_detail(codice_cliente)`
2. Aggregare dati da tutte le fonti:
   - `get_client_detail()` da db_utils.py
   - Raccomandazioni da nbo_master.json
3. Layout con tabs: Polizze, Rischio, Storico, Raccomandazioni
4. Aggiungere placeholder per immagine satellitare
5. Integrare A.D.A. contestuale (box con suggerimento)
6. Form chiamata semplificato

**Codice esempio per immagine satellitare:**
```python
def get_satellite_image_url(lat, lon, zoom=18):
    # Google Maps Static API
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    return f"https://maps.googleapis.com/maps/api/staticmap?center={lat},{lon}&zoom={zoom}&size=400x300&maptype=satellite&key={api_key}"

# Oppure Mapbox
def get_satellite_image_url_mapbox(lat, lon, zoom=18):
    token = os.getenv("MAPBOX_TOKEN")
    return f"https://api.mapbox.com/styles/v1/mapbox/satellite-v9/static/{lon},{lat},{zoom}/400x300?access_token={token}"
```

---

### Fase 4: IL MIO PORTAFOGLIO (Priorità MEDIA)

**File da modificare:** `app.py`

**Azioni:**
1. Creare funzione `render_portafoglio()`
2. Spostare grafici esistenti da Tab Analytics
3. Calcolare KPI aggregati
4. Aggiungere lista clienti churn alto
5. Aggiungere lista opportunità cross-selling

**KPI da calcolare:**
```python
def get_portfolio_kpi(df_clienti, df_polizze):
    return {
        'n_clienti': len(df_clienti),
        'clv_totale': df_clienti['clv_stimato'].sum(),
        'avg_churn': df_clienti['churn_probability'].mean(),
        'pct_multi_holding': (df_clienti['num_polizze'] > 1).mean() * 100,
    }
```

---

### Fase 5: MAPPA TERRITORIALE (Priorità MEDIA)

**File da modificare:** `app.py`

**Azioni:**
1. Semplificare la mappa esistente
2. Rimuovere HeatmapLayer
3. Colorare punti per NBO score (non rischio)
4. Aggiungere filtri sopra la mappa
5. Implementare click → navigare a scheda cliente

**Codice esempio per colorazione NBO:**
```python
def get_nbo_color(score):
    if score >= 70:
        return [16, 185, 129, 200]  # Verde
    elif score >= 50:
        return [245, 158, 11, 200]  # Arancione
    else:
        return [239, 68, 68, 200]   # Rosso
```

---

### Fase 6: ANALISI SATELLITARE (Priorità ALTA per Challenge)

**File da creare:** `src/satellite/analyzer.py`

**Azioni:**
1. Creare UI per ricerca abitazione
2. Mostrare immagine satellitare
3. Creare checklist features (inizialmente manuale)
4. Calcolare impatto pricing (formula semplice)
5. Predisporre per integrazione AI

**Struttura modulo:**
```python
# src/satellite/analyzer.py

class SatelliteAnalyzer:
    def __init__(self):
        self.features = [
            "piscina", "pannelli_solari", "alberi_tetto",
            "giardino", "stato_tetto", "garage"
        ]

    def get_image(self, lat, lon):
        """Ritorna URL immagine satellitare"""
        pass

    def analyze_manual(self, features_dict):
        """Analisi con features inserite manualmente"""
        pass

    def analyze_ai(self, image_url):
        """Analisi con AI (placeholder per ora)"""
        # TODO: Integrare quando AI pronta
        pass

    def calculate_pricing_impact(self, features_dict, base_premium):
        """Calcola impatto sul premio"""
        impact = 0
        if features_dict.get('piscina'):
            impact += 0.08  # +8%
        if features_dict.get('pannelli_solari'):
            impact -= 0.05  # -5%
        # etc.
        return base_premium * (1 + impact)
```

---

### Fase 7: A.D.A. Floating (Priorità MEDIA)

**File da modificare:** `src/ada/chat.py`

**Azioni:**
1. Creare componente floating button con CSS
2. Implementare pannello espandibile
3. Passare contesto da session_state
4. Aggiungere suggerimenti proattivi

**Codice CSS per floating:**
```css
.ada-floating-button {
    position: fixed;
    bottom: 24px;
    right: 24px;
    width: 60px;
    height: 60px;
    border-radius: 50%;
    background: linear-gradient(135deg, #00A0B0 0%, #00C9D4 100%);
    box-shadow: 0 4px 12px rgba(0, 160, 176, 0.4);
    cursor: pointer;
    z-index: 1000;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 28px;
    color: white;
    transition: transform 0.2s ease;
}

.ada-floating-button:hover {
    transform: scale(1.1);
}

.ada-chat-panel {
    position: fixed;
    bottom: 100px;
    right: 24px;
    width: 380px;
    height: 500px;
    background: white;
    border-radius: 16px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
    z-index: 999;
    display: flex;
    flex-direction: column;
}
```

---

## File da Modificare/Creare - Riepilogo

| File | Tipo | Descrizione |
|------|------|-------------|
| `app.py` | Modifica | Ristrutturazione completa navigazione e layout |
| `src/ada/chat.py` | Modifica | Adattamento per floating mode |
| `src/data/db_utils.py` | Modifica | Nuove query per KPI agente |
| `constants.py` | Modifica | Nuove costanti per sezioni |
| `src/components/client_card.py` | **NUOVO** | Componente scheda cliente riusabile |
| `src/components/top_actions.py` | **NUOVO** | Componente lista azioni Top 5 |
| `src/satellite/analyzer.py` | **NUOVO** | Modulo analisi satellitare |
| `src/satellite/__init__.py` | **NUOVO** | Init modulo |

---

## Verifiche Finali

1. **Test funzionale**: Navigare tra tutte le sezioni
2. **Test UX**: Far provare a un utente non tecnico
3. **Test performance**: Verificare tempi di caricamento
4. **Test dati**: Verificare che tutti i dati vengano caricati correttamente

---

## Note per la Presentazione alla Challenge

Questo redesign risponde direttamente agli obiettivi di Vita Sicura:

| Obiettivo Vita Sicura | Come il Redesign lo Supporta |
|----------------------|------------------------------|
| **Cross-selling** | Top 5 NBO in homepage guida l'azione quotidiana |
| **Multi-holding** | Raccomandazioni integrate nella scheda cliente |
| **Supporto rete agenziale** | Strumento pensato per l'agente, non per l'analista |
| **Computer Vision / Pricing** | Sezione Analisi Satellitare dedicata con massima visibilità |
| **A.D.A. potenziata** | Sempre accessibile con contesto automatico |

**Messaggio chiave per la presentazione:**
> "HELIOS è stato ridisegnato pensando a come un agente inizia la sua giornata, non a quali dati abbiamo disponibili. Ogni schermata risponde a una domanda operativa."

---

## Appendice: CSS Aggiuntivo Suggerito

```css
/* Top Client Card */
.top-client-card {
    background: white;
    border: 1px solid #E2E8F0;
    border-radius: 16px;
    padding: 1.25rem;
    transition: all 0.2s ease;
    cursor: pointer;
}

.top-client-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 24px rgba(0, 160, 176, 0.15);
    border-color: #00A0B0;
}

.rank-badge {
    background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%);
    color: white;
    padding: 0.25rem 0.75rem;
    border-radius: 100px;
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.05em;
}

/* Alert Card */
.alert-card {
    background: #FEF3C7;
    border-left: 4px solid #F59E0B;
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 0.5rem;
}

.alert-card.critical {
    background: #FEE2E2;
    border-left-color: #DC2626;
}

/* Feature Badge (Satellite Analysis) */
.feature-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    border-radius: 100px;
    font-size: 0.8rem;
    font-weight: 500;
}

.feature-badge.detected {
    background: #DCFCE7;
    color: #16A34A;
}

.feature-badge.not-detected {
    background: #F3F4F6;
    color: #64748B;
}
```

---

## Analisi del Brief vs. Redesign Proposto

### Cosa dice il Brief (Aree di Innovazione)

**Analisi:**
- Segmentare clienti per personas e cluster ad alto valore
- Migliorare reportistica per overview customer base e polizze
- Pricing evoluto con dati satellitari/Street View per scoring del rischio (polizze Casa)

**Azioni commerciali:**
- Modelli predittivi per cross-selling, retention, multi-holding
- Supporto consulenti con Next Best Action
- Individuare aree geografiche con protection gap elevato (polizze Casa e Salute)

---

### Il Problema del Redesign Attuale

Ho troppo semplificato la componente geo-rischio. Nel brief è centrale per:

- **Stream 2 - Visione Aumentata**: il rischio sismico/idrogeologico è un input per il pricing, non solo un dato da mostrare
- **Stream 4 - Competitive Edge**: l'analisi del loss ratio per zona/cluster richiede questi dati
- **Protection Gap**: serve capire dove il rischio è alto ma la penetrazione è bassa

---

### Cosa NON deve essere rimosso

| Dato | Utilità per la Challenge | Decisione Corretta |
|------|--------------------------|-------------------|
| Zona sismica | Input per pricing Casa | **MANTENERE** |
| Rischio idrogeologico | Input per pricing Casa | **MANTENERE** |
| Risk score | Sintesi per NBO/pricing | **MANTENERE** |
| Heatmap territoriale | Identificare protection gap | **SEMPLIFICARE** ma mantenere |

---

### Proposta di Correzione

La Scheda Cliente 360° deve avere una **Tab Rischio prominente**:

```
TAB RISCHIO:
┌─────────────────────────────────────────────────────────────┐
│  PROFILO DI RISCHIO ABITAZIONE                              │
├─────────────────────────────────────────────────────────────┤
│  📍 Via Roma 123, Milano                                    │
│                                                             │
│  🌍 RISCHIO SISMICO         🌊 RISCHIO IDROGEOLOGICO       │
│  ┌─────────────────┐        ┌─────────────────┐            │
│  │ Zona 3 (Medio)  │        │ P2 (Medio)      │            │
│  │ Score: 40       │        │ Alluvione: P3   │            │
│  └─────────────────┘        └─────────────────┘            │
│                                                             │
│  🛰️ FEATURES SATELLITARI (coming soon)                     │
│  [Piscina] [Pannelli solari] [Alberi tetto]                │
│                                                             │
│  📊 IMPATTO SU PRICING                                      │
│  Premio base: €380 → Premio suggerito: €425 (+12%)         │
│  Fattori: Zona sismica 3 (+5%), Idro P2 (+7%)              │
└─────────────────────────────────────────────────────────────┘
```

---

### Modalità Mappa Territoriale

La Mappa Territoriale deve avere **due modalità**:

1. **Modalità Commerciale**: colorata per NBO score (per l'agente)
2. **Modalità Rischio**: colorata per risk score (per analisi protection gap)

---

*Documento creato per il progetto HELIOS - AI Challenge Generali x Bicocca 2025*
