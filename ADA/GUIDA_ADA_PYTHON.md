# 🐍 A.D.A. PYTHON ENGINE - Guida Rapida

## ✅ SETUP (5 minuti)

### 1. Copia i File

Nella cartella del tuo progetto Streamlit, sostituisci/aggiungi:

```
helios_dashboard/
├── ada_engine.py          # ← NUOVO (core engine)
├── ada_chat_enhanced.py   # ← SOSTITUISCE ada_chat.py
├── db_utils.py            # ← Mantieni quello esistente
├── app.py                 # ← Aggiorna l'import
├── requirements.txt       # ← Aggiorna
└── .env                   # ← Aggiungi OPENROUTER_API_KEY
```

### 2. Aggiorna .env

```bash
# Copia il template
cp .env.example .env

# Modifica .env e aggiungi:
OPENROUTER_API_KEY=sk-or-v1-[tua-chiave]
```

### 3. Aggiorna app.py

Nel tuo `app.py`, cambia l'import:

```python
# PRIMA (con n8n webhook):
from ada_chat import render_ada_chat

# DOPO (con Python engine):
from ada_chat_enhanced import render_ada_chat
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

### Test A.D.A.

1. Vai alla tab **A.D.A. Chat**
2. Dovresti vedere: `🐍 A.D.A. Status: Python Engine`
3. Scrivi: **"Analizza il rischio del cliente 100"**
4. Attendi 5-15 secondi
5. Dovresti ricevere una risposta con dati reali dal database!

---

## 🔧 COME FUNZIONA

### Architettura

```
User Input (Streamlit)
    ↓
ada_chat_enhanced.py
    ↓
ADAEngine (ada_engine.py)
    ↓
    ├─→ Supabase (per dati)
    └─→ OpenRouter API (Claude 3.5 Sonnet)
    ↓
    ├─→ Tools (6 disponibili)
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

---

## 📊 QUERY DI ESEMPIO

### Test Basici

```
"Ciao A.D.A., come stai?"
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

### Errore: "Module 'ada_engine' not found"

```bash
# Assicurati che ada_engine.py sia nella stessa cartella di app.py
ls -la ada_engine.py
```

### Errore: "OPENROUTER_API_KEY not found"

```bash
# Verifica .env
cat .env | grep OPENROUTER

# Se manca, aggiungi:
echo "OPENROUTER_API_KEY=sk-or-v1-..." >> .env
```

### Errore: "Connection timeout"

- Claude impiega 10-20 secondi per rispondere
- Normale per la prima query (cold start)
- Query successive: 5-10 secondi

### Risposta: "Nessuna risposta generata"

- Verifica che OPENROUTER_API_KEY sia valida
- Controlla crediti OpenRouter (Dashboard)
- Guarda logs Streamlit per errori specifici

### Tools Non Vengono Chiamati

- Verifica connessione Supabase
- Controlla che le tabelle esistano nel DB
- Prova query più esplicite: "Usa il tool client_profile_lookup per il cliente 100"

---

## 💡 TIPS

### Ottimizza Performance

Nel file `ada_engine.py`, modifica:

```python
self.model = "anthropic/claude-3.5-sonnet"  # Qualità massima
# Oppure per risparmio/velocità:
self.model = "anthropic/claude-3.5-haiku"   # 4x più economico, 2x più veloce
```

### Debug Mode

Aggiungi print statements in `ada_engine.py`:

```python
def _call_claude(self, messages):
    print(f"[DEBUG] Calling Claude with {len(messages)} messages")
    # ... rest of code
```

### Logging Interazioni

Il logging in `log_ada_interactions` è **disabilitato** di default nella versione Python. 

Per abilitarlo, aggiungi alla fine di `ADAEngine.chat()`:

```python
# Log to database
self.supabase.table("log_ada_interactions").insert({
    "session_id": "python_session",
    "client_id": client_id,
    "user_message": message,
    "ada_response": final_text,
    "tools_used": json.dumps(tools_used),
    "execution_time_ms": 0  # Calculate if needed
}).execute()
```

---

## 🔄 MIGRAZIONE DA N8N

Se in futuro riesci ad attivare n8n, puoi tornare alla versione webhook:

```python
# In app.py
from ada_chat import render_ada_chat  # Versione n8n original

# Oppure usa entrambe con toggle:
use_python = os.getenv("USE_PYTHON_ENGINE", "true").lower() == "true"
if use_python:
    from ada_chat_enhanced import render_ada_chat
else:
    from ada_chat import render_ada_chat
```

---

## 📈 MONITORING

### Check OpenRouter Usage

Dashboard: https://openrouter.ai/activity

Guarda:
- Total requests
- Cost per request
- Errors

### Check Performance

In Streamlit, i tempi tipici sono:
- Query senza tools: 3-5 sec
- Query con 1-2 tools: 8-12 sec
- Query con 3+ tools: 15-25 sec

Se supera 30 sec costantemente → problema API/network

---

## ✅ CHECKLIST FUNZIONAMENTO

- [ ] File `ada_engine.py` presente
- [ ] File `ada_chat_enhanced.py` presente
- [ ] `.env` con `OPENROUTER_API_KEY` configurata
- [ ] `app.py` importa `ada_chat_enhanced`
- [ ] Streamlit si avvia senza errori
- [ ] Status mostra "🐍 Python Engine"
- [ ] Query di test risponde con successo
- [ ] Tools vengono chiamati (verifica in expander)

---

## 🎉 CONGRATULAZIONI!

Se tutto funziona, hai A.D.A. **operativo al 100%** senza dipendenze da n8n!

**Prossimi step:**
1. Testa tutti gli scenari della guida test
2. Integra con NBO module (domani)
3. Polish UI Streamlit

---

**Domande? Problemi?**
Consulta i logs Streamlit per dettagli errori.
