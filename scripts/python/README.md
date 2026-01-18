# Script Python per Supabase

Questa directory contiene gli script Python per gestire i dati del database Supabase.

## Setup

1. **Installa le dipendenze:**
   ```bash
   pip install -r scripts/python/requirements.txt
   ```

2. **Configura le credenziali:**
   Assicurati che il file `.env` contenga:
   ```
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_key
   ```

3. **Crea le tabelle su Supabase:**
   - Vai alla dashboard di Supabase
   - Apri il SQL Editor
   - Esegui il contenuto del file `create_tables.sql`

## Script Disponibili

### upload_to_supabase.py
Carica i dati da `Data/nbo_master.json` al database Supabase.

**Struttura database creata:**
- `master`: tabella principale con dati cliente appiattiti
- `master_raccomandazioni`: raccomandazioni prodotto per cliente
- `master_prodotti_posseduti`: prodotti posseduti da ogni cliente

**Uso:**
```bash
python scripts/python/upload_to_supabase.py
```

### extract_sample.py
Estrae 40 clienti random dal database e li salva in CSV.

**Caratteristiche:**
- Usa un seed fisso (42) per riproducibilità
- Estrae tutti i dettagli cliente
- Crea un CSV appiattito con prodotti e raccomandazioni
- Output: `Data/sample_40_customers.csv`

**Uso:**
```bash
python scripts/python/extract_sample.py
```

## Note

- Tutti gli script usano strutture dati completamente appiattite (nessuna colonna innestata)
- La relazione tra tabelle è gestita tramite foreign key su `codice_cliente`
- Il seed random è fisso (42) per garantire la riproducibilità dell'estrazione
