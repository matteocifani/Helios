-- Schema SQL per creare le tabelle su Supabase
-- Esegui questo script nel SQL Editor di Supabase prima di usare upload_to_supabase.py

-- ============================================================================
-- TABELLA MASTER - Clienti
-- ============================================================================
-- Note: codice_cliente è PRIMARY KEY, quindi PostgreSQL crea automaticamente
-- un indice univoco su questa colonna. Non serve creare un indice aggiuntivo.

CREATE TABLE IF NOT EXISTS master (
    codice_cliente TEXT PRIMARY KEY,
    timestamp TIMESTAMPTZ,
    -- Anagrafica
    nome TEXT,
    cognome TEXT,
    eta INTEGER,
    indirizzo TEXT,
    citta TEXT,
    provincia TEXT,
    regione TEXT,
    latitudine FLOAT,
    longitudine FLOAT,
    -- Metadata business
    churn_attuale FLOAT,
    num_polizze_attuali INTEGER,
    cluster_nba INTEGER,
    cluster_risposta TEXT,
    satisfaction_score FLOAT,
    engagement_score FLOAT,
    clv_stimato FLOAT
);

-- Indici secondari per query comuni (filtri e aggregazioni)
CREATE INDEX IF NOT EXISTS idx_master_cluster_nba ON master(cluster_nba);
CREATE INDEX IF NOT EXISTS idx_master_cluster_risposta ON master(cluster_risposta);
CREATE INDEX IF NOT EXISTS idx_master_churn ON master(churn_attuale);
CREATE INDEX IF NOT EXISTS idx_master_citta ON master(citta);

COMMENT ON TABLE master IS 'Tabella principale dei clienti con dati anagrafici e metadata';

-- ============================================================================
-- TABELLA MASTER_RACCOMANDAZIONI - Next Best Offer per cliente
-- ============================================================================

CREATE TABLE IF NOT EXISTS master_raccomandazioni (
    id SERIAL PRIMARY KEY,
    codice_cliente TEXT NOT NULL REFERENCES master(codice_cliente) ON DELETE CASCADE,
    -- Raccomandazione
    area_bisogno TEXT,
    prodotto TEXT,
    -- Componenti scoring
    retention_gain FLOAT,
    redditivita FLOAT,
    propensione FLOAT,
    affinita_cluster FLOAT,
    -- Metriche churn
    delta_churn FLOAT,
    churn_prima FLOAT,
    churn_dopo FLOAT
);

-- Indice FONDAMENTALE per JOIN con master (foreign key)
CREATE INDEX IF NOT EXISTS idx_racc_codice_cliente ON master_raccomandazioni(codice_cliente);

-- Indici per query di analisi
CREATE INDEX IF NOT EXISTS idx_racc_area_bisogno ON master_raccomandazioni(area_bisogno);
CREATE INDEX IF NOT EXISTS idx_racc_prodotto ON master_raccomandazioni(prodotto);
CREATE INDEX IF NOT EXISTS idx_racc_propensione ON master_raccomandazioni(propensione);

COMMENT ON TABLE master_raccomandazioni IS 'Raccomandazioni prodotti per ogni cliente (Next Best Offer)';

-- ============================================================================
-- TABELLA MASTER_PRODOTTI_POSSEDUTI - Prodotti attuali del cliente
-- ============================================================================

CREATE TABLE IF NOT EXISTS master_prodotti_posseduti (
    id SERIAL PRIMARY KEY,
    codice_cliente TEXT NOT NULL REFERENCES master(codice_cliente) ON DELETE CASCADE,
    prodotto TEXT NOT NULL
);

-- Indice FONDAMENTALE per JOIN con master (foreign key)
CREATE INDEX IF NOT EXISTS idx_prodotti_codice_cliente ON master_prodotti_posseduti(codice_cliente);

-- Indice per ricerche per prodotto
CREATE INDEX IF NOT EXISTS idx_prodotti_prodotto ON master_prodotti_posseduti(prodotto);

-- Indice composito per query "quali clienti hanno prodotto X"
CREATE INDEX IF NOT EXISTS idx_prodotti_prodotto_cliente ON master_prodotti_posseduti(prodotto, codice_cliente);

COMMENT ON TABLE master_prodotti_posseduti IS 'Prodotti attualmente posseduti da ogni cliente';
