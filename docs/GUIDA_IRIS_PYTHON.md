# 🐍 IRIS PYTHON ENGINE - Guida Rapida

**✅ AGGIORNATO: Gennaio 2026 - Versione Production (Renamed from A.D.A.)**

## ✅ SETUP (5 minuti)

### 1. File del Progetto

Struttura attuale del progetto:

```
helios_dashboard/
├── src/
│   ├── iris/
│   │   ├── engine.py          # ✅ Core engine (production version)
│   │   └── chat.py            # ✅ UI Streamlit per Iris
│   ├── config/
│   │   └── constants.py       # ✅ Costanti centralizzate
│   └── data/
│       └── db_utils.py        # ✅ Database layer
├── app.py                     # ✅ Main dashboard
├── requirements.txt           # ✅ Dipendenze Python
└── .env                       # ✅ Credenziali (OPENROUTER_API_KEY, SUPABASE_URL, SUPABASE_KEY)
```

### 2. Aggiorna .env

```bash
# Copia il template
cp .env.example .env

# Modifica .env e aggiungi:
OPENROUTER_API_KEY=sk-or-v1-[tua-chiave]
```

### 3. Aggiorna app.py

Nel tuo `app.py`, assicurati che l'import sia corretto (già configurato):

```python
# Import corretto:
from src.iris.chat import render_iris_chat
```

### 4. Installa Dipendenze

```bash
pip install -r requirements.txt
```

---

## 🚀 TEST IMMEDIATO

### Avvia Streamlit

```bash
streamlit run app.py
```

### Test Iris

1. Vai alla sidebar e trova il box **Iris Chat**.
2. Dovresti vedere: `Online` (pallino verde).
3. Scrivi: **"Analizza il rischio del cliente 100"**.
4. Attendi 5-15 secondi.
5. Dovresti ricevere una risposta con dati reali dal database!

---

## 🔧 COME FUNZIONA

### Architettura

```
User Input (Streamlit)
    ↓
src/iris/chat.py (render_iris_chat)
    ↓
IrisEngine (src/iris/engine.py)
    ↓
    ├─→ Supabase (per dati)
    └─→ OpenRouter API (Claude 3.5 Sonnet)
    ↓
    ├─→ Tools (7 disponibili)
    └─→ Response formatting
    ↓
Streamlit UI
```

### Tools Disponibili

1. **client_profile_lookup** - Profilo completo cliente
2. **policy_status_check** - Polizze attive
3. **risk_assessment** - Analisi rischio proprietà
4. **solar_potential_calc** - Calcolo potenziale solare
5. **doc_retriever_rag** - Ricerca semantica storico
6. **premium_calculator** - Calcolo preventivi
7. **database_explorer** - Esplorazione generica DB

---

## 📊 QUERY DI ESEMPIO

### Test Basici

```
"Ciao Iris, come stai?"
→ Risposta generica senza tools

"Mostra il profilo del cliente 100"
→ Usa: client_profile_lookup

"Quali polizze ha il cliente 100?"
→ Usa: policy_status_check
```

### Test Avanzati

```
"Analizza il rischio completo del cliente 100"
→ Usa: client_profile_lookup + risk_assessment

"Calcola un preventivo NatCat per il cliente 100"
→ Usa: risk_assessment + premium_calculator

"Il cliente 100 ha potenziale per pannelli solari?"
→ Usa: solar_potential_calc
```

### Test Multi-Tool

```
"Fai un'analisi completa del cliente 100: profilo, rischio, polizze e potenziale solare"
→ Usa: Tutti i tools!
```

---

## 🐛 TROUBLESHOOTING

### Errore: "Module 'src.iris' not found"

Assicurati di eseguire `streamlit run app.py` dalla root del progetto.

### Errore: "OPENROUTER_API_KEY not found"

```bash
# Verifica .env
cat .env | grep OPENROUTER
```

### Errore: "Connection timeout"

- Claude impiega 10-20 secondi per rispondere.
- Normale per la prima query (cold start).
- Query successive: 5-10 secondi.

### Risposta: "Nessuna risposta generata"

- Verifica che OPENROUTER_API_KEY sia valida.
- Controlla crediti OpenRouter (Dashboard).
- Guarda logs Streamlit per errori specifici.

---

## 💡 TIPS

### Ottimizza Performance

Nel file `src/iris/engine.py`, modifica:

```python
self.model = "anthropic/claude-3.5-sonnet"  # Qualità massima
# Oppure per risparmio/velocità:
self.model = "anthropic/claude-3.5-haiku"   # 4x più economico
```

### Debug Mode

Aggiungi print statements in `src/iris/engine.py` se necessario.

---

## ✅ CHECKLIST FUNZIONAMENTO

- [ ] Directory `src/iris` presente con `engine.py` e `chat.py`
- [ ] `.env` con `OPENROUTER_API_KEY` configurata
- [ ] `app.py` importa `src.iris.chat`
- [ ] Streamlit si avvia senza errori
- [ ] Status mostra indicatore verde "Online"
- [ ] Query di test risponde con successo
- [ ] Tools vengono chiamati
