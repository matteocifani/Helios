#!/usr/bin/env python3
"""
Script per caricare i dati da nbo_master.json a Supabase.
Crea una struttura di database normalizzata senza colonne innestate.
"""

import json
import os
from typing import List, Dict, Any
from dotenv import load_dotenv
from supabase import create_client, Client

# Carica variabili d'ambiente
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Path al file JSON
JSON_FILE = "Data/nbo_master.json"
BATCH_SIZE = 100  # Numero di record per batch


def create_tables(supabase: Client):
    """Crea le tabelle se non esistono."""
    print("⚙️  Creazione tabelle...")
    
    # Query per creare le tabelle
    # Nota: Supabase/PostgreSQL richiede che le tabelle vengano create via SQL
    # Useremo il client Supabase per eseguire query SQL raw
    
    # Tabella master
    master_table_sql = """
    CREATE TABLE IF NOT EXISTS master (
        codice_cliente TEXT PRIMARY KEY,
        timestamp TIMESTAMPTZ,
        nome TEXT,
        cognome TEXT,
        eta INTEGER,
        indirizzo TEXT,
        citta TEXT,
        provincia TEXT,
        regione TEXT,
        latitudine FLOAT,
        longitudine FLOAT,
        churn_attuale FLOAT,
        num_polizze_attuali INTEGER,
        cluster_nba INTEGER,
        cluster_risposta TEXT,
        satisfaction_score FLOAT,
        engagement_score FLOAT,
        clv_stimato FLOAT
    );
    """
    
    # Tabella raccomandazioni
    raccomandazioni_table_sql = """
    CREATE TABLE IF NOT EXISTS master_raccomandazioni (
        id SERIAL PRIMARY KEY,
        codice_cliente TEXT REFERENCES master(codice_cliente) ON DELETE CASCADE,
        area_bisogno TEXT,
        prodotto TEXT,
        retention_gain FLOAT,
        redditivita FLOAT,
        propensione FLOAT,
        affinita_cluster FLOAT,
        delta_churn FLOAT,
        churn_prima FLOAT,
        churn_dopo FLOAT
    );
    """
    
    # Tabella prodotti posseduti
    prodotti_table_sql = """
    CREATE TABLE IF NOT EXISTS master_prodotti_posseduti (
        id SERIAL PRIMARY KEY,
        codice_cliente TEXT REFERENCES master(codice_cliente) ON DELETE CASCADE,
        prodotto TEXT
    );
    """
    
    try:
        # Esegui le query SQL
        supabase.postgrest.rpc('exec_sql', {'sql': master_table_sql}).execute()
        print("✅ Tabella 'master' creata/verificata")
    except Exception as e:
        print(f"ℹ️  Tabella 'master': {e}")
    
    try:
        supabase.postgrest.rpc('exec_sql', {'sql': raccomandazioni_table_sql}).execute()
        print("✅ Tabella 'master_raccomandazioni' creata/verificata")
    except Exception as e:
        print(f"ℹ️  Tabella 'master_raccomandazioni': {e}")
    
    try:
        supabase.postgrest.rpc('exec_sql', {'sql': prodotti_table_sql}).execute()
        print("✅ Tabella 'master_prodotti_posseduti' creata/verificata")
    except Exception as e:
        print(f"ℹ️  Tabella 'master_prodotti_posseduti': {e}")


def flatten_customer_record(customer: Dict[str, Any]) -> Dict[str, Any]:
    """Appiattisce un record cliente dal JSON."""
    anagrafica = customer.get("anagrafica", {})
    metadata = customer.get("metadata", {})
    
    return {
        "codice_cliente": customer.get("codice_cliente"),
        "timestamp": customer.get("timestamp"),
        # Campi anagrafica
        "nome": anagrafica.get("nome"),
        "cognome": anagrafica.get("cognome"),
        "eta": anagrafica.get("eta"),
        "indirizzo": anagrafica.get("indirizzo"),
        "citta": anagrafica.get("citta"),
        "provincia": anagrafica.get("provincia"),
        "regione": anagrafica.get("regione"),
        "latitudine": anagrafica.get("latitudine"),
        "longitudine": anagrafica.get("longitudine"),
        # Campi metadata
        "churn_attuale": metadata.get("churn_attuale"),
        "num_polizze_attuali": metadata.get("num_polizze_attuali"),
        "cluster_nba": metadata.get("cluster_nba"),
        "cluster_risposta": metadata.get("cluster_risposta"),
        "satisfaction_score": metadata.get("satisfaction_score"),
        "engagement_score": metadata.get("engagement_score"),
        "clv_stimato": metadata.get("clv_stimato"),
    }


def extract_raccomandazioni(customer: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Estrae le raccomandazioni per un cliente."""
    codice_cliente = customer.get("codice_cliente")
    raccomandazioni = customer.get("raccomandazioni", [])
    
    result = []
    for racc in raccomandazioni:
        componenti = racc.get("componenti", {})
        dettagli = racc.get("dettagli", {})
        
        result.append({
            "codice_cliente": codice_cliente,
            "area_bisogno": racc.get("area_bisogno"),
            "prodotto": racc.get("prodotto"),
            "retention_gain": componenti.get("retention_gain"),
            "redditivita": componenti.get("redditivita"),
            "propensione": componenti.get("propensione"),
            "affinita_cluster": componenti.get("affinita_cluster"),
            "delta_churn": dettagli.get("delta_churn"),
            "churn_prima": dettagli.get("churn_prima"),
            "churn_dopo": dettagli.get("churn_dopo"),
        })
    
    return result


def extract_prodotti_posseduti(customer: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Estrae i prodotti posseduti per un cliente."""
    codice_cliente = customer.get("codice_cliente")
    metadata = customer.get("metadata", {})
    prodotti = metadata.get("prodotti_posseduti", [])
    
    return [
        {
            "codice_cliente": codice_cliente,
            "prodotto": prodotto
        }
        for prodotto in prodotti
    ]


def clear_tables(supabase: Client):
    """Svuota le tabelle prima del caricamento (per idempotenza)."""
    print("\n🗑️  Pulizia tabelle esistenti...")

    # Ordine importante: prima le tabelle con FK, poi la master
    tables_to_clear = [
        "master_raccomandazioni",
        "master_prodotti_posseduti",
        "master"
    ]

    for table in tables_to_clear:
        try:
            # Cancella tutti i record dalla tabella
            supabase.table(table).delete().neq("codice_cliente", "").execute()
            print(f"   ✅ Tabella '{table}' svuotata")
        except Exception as e:
            print(f"   ⚠️  Tabella '{table}': {e}")


def upload_data(supabase: Client, customers: List[Dict[str, Any]]):
    """Carica i dati su Supabase in batch (idempotente)."""
    total = len(customers)
    print(f"\n📊 Totale clienti da caricare: {total}")

    # Svuota le tabelle prima del caricamento
    clear_tables(supabase)

    # Prepara i dati
    master_records = []
    raccomandazioni_records = []
    prodotti_records = []

    print("\n📦 Preparazione dati...")
    for i, customer in enumerate(customers, 1):
        if i % 1000 == 0:
            print(f"   Processati {i}/{total} clienti...")

        # Appiattisci il record principale
        master_records.append(flatten_customer_record(customer))

        # Estrai raccomandazioni
        raccomandazioni_records.extend(extract_raccomandazioni(customer))

        # Estrai prodotti posseduti
        prodotti_records.extend(extract_prodotti_posseduti(customer))

    print(f"✅ Dati preparati:")
    print(f"   - {len(master_records)} clienti")
    print(f"   - {len(raccomandazioni_records)} raccomandazioni")
    print(f"   - {len(prodotti_records)} prodotti posseduti")

    # Carica tabella master
    print(f"\n📤 Caricamento tabella 'master'...")
    for i in range(0, len(master_records), BATCH_SIZE):
        batch = master_records[i:i + BATCH_SIZE]
        try:
            supabase.table("master").insert(batch).execute()
            print(f"   ✅ Caricati {min(i + BATCH_SIZE, len(master_records))}/{len(master_records)} record")
        except Exception as e:
            print(f"   ❌ Errore nel batch {i}-{i + BATCH_SIZE}: {e}")
            raise

    # Carica tabella raccomandazioni
    print(f"\n📤 Caricamento tabella 'master_raccomandazioni'...")
    for i in range(0, len(raccomandazioni_records), BATCH_SIZE):
        batch = raccomandazioni_records[i:i + BATCH_SIZE]
        try:
            supabase.table("master_raccomandazioni").insert(batch).execute()
            print(f"   ✅ Caricati {min(i + BATCH_SIZE, len(raccomandazioni_records))}/{len(raccomandazioni_records)} record")
        except Exception as e:
            print(f"   ❌ Errore nel batch {i}-{i + BATCH_SIZE}: {e}")
            raise

    # Carica tabella prodotti posseduti
    print(f"\n📤 Caricamento tabella 'master_prodotti_posseduti'...")
    for i in range(0, len(prodotti_records), BATCH_SIZE):
        batch = prodotti_records[i:i + BATCH_SIZE]
        try:
            supabase.table("master_prodotti_posseduti").insert(batch).execute()
            print(f"   ✅ Caricati {min(i + BATCH_SIZE, len(prodotti_records))}/{len(prodotti_records)} record")
        except Exception as e:
            print(f"   ❌ Errore nel batch {i}-{i + BATCH_SIZE}: {e}")
            raise

    print("\n✅ Tutti i dati sono stati caricati con successo!")


def main():
    """Funzione principale."""
    print("🚀 Avvio upload dati a Supabase\n")
    
    # Verifica credenziali
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("❌ Errore: SUPABASE_URL e SUPABASE_KEY devono essere definiti nel file .env")
        return
    
    # Verifica file JSON
    if not os.path.exists(JSON_FILE):
        print(f"❌ Errore: File {JSON_FILE} non trovato")
        return
    
    # Crea client Supabase
    print("🔌 Connessione a Supabase...")
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✅ Connesso a Supabase\n")
    
    # Nota: La creazione delle tabelle deve essere fatta tramite dashboard Supabase
    # o usando un client SQL diretto. Per ora assumiamo che le tabelle siano già create.
    print("ℹ️  Assicurati che le tabelle siano già create su Supabase")
    print("   (puoi usare la dashboard SQL Editor di Supabase)\n")
    
    # Carica dati JSON
    print(f"📖 Lettura file {JSON_FILE}...")
    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        customers = json.load(f)
    print(f"✅ File caricato: {len(customers)} clienti\n")
    
    # Upload dati
    upload_data(supabase, customers)
    
    print("\n🎉 Processo completato!")


if __name__ == "__main__":
    main()
