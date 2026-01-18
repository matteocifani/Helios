#!/usr/bin/env python3
"""
Script per estrarre 40 clienti random dal database Supabase e salvarli in CSV.
Usa un seed fisso per garantire riproducibilità.
"""

import os
import random
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client, Client

# Carica variabili d'ambiente
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Configurazione
RANDOM_SEED = 42
SAMPLE_SIZE = 40
OUTPUT_FILE = "Data/sample_40_customers.csv"


def fetch_all_customers(supabase: Client):
    """Recupera tutti i clienti dalla tabella master."""
    print("📥 Recupero clienti dal database...")
    
    try:
        response = supabase.table("master").select("*").execute()
        customers = response.data
        print(f"✅ Recuperati {len(customers)} clienti")
        return customers
    except Exception as e:
        print(f"❌ Errore nel recupero clienti: {e}")
        raise


def fetch_prodotti_posseduti(supabase: Client, codici_clienti: list):
    """Recupera i prodotti posseduti per i clienti selezionati."""
    print("📥 Recupero prodotti posseduti...")
    
    try:
        response = supabase.table("master_prodotti_posseduti")\
            .select("codice_cliente, prodotto")\
            .in_("codice_cliente", codici_clienti)\
            .execute()
        
        # Raggruppa per codice_cliente
        prodotti_map = {}
        for item in response.data:
            cod = item['codice_cliente']
            if cod not in prodotti_map:
                prodotti_map[cod] = []
            prodotti_map[cod].append(item['prodotto'])
        
        print(f"✅ Recuperati prodotti per {len(prodotti_map)} clienti")
        return prodotti_map
    except Exception as e:
        print(f"❌ Errore nel recupero prodotti: {e}")
        raise


def fetch_raccomandazioni(supabase: Client, codici_clienti: list):
    """Recupera le raccomandazioni per i clienti selezionati."""
    print("📥 Recupero raccomandazioni...")
    
    try:
        response = supabase.table("master_raccomandazioni")\
            .select("codice_cliente, prodotto")\
            .in_("codice_cliente", codici_clienti)\
            .execute()
        
        # Raggruppa per codice_cliente
        racc_map = {}
        for item in response.data:
            cod = item['codice_cliente']
            if cod not in racc_map:
                racc_map[cod] = []
            racc_map[cod].append(item['prodotto'])
        
        print(f"✅ Recuperate raccomandazioni per {len(racc_map)} clienti")
        return racc_map
    except Exception as e:
        print(f"❌ Errore nel recupero raccomandazioni: {e}")
        raise


def select_random_sample(customers: list, seed: int, sample_size: int):
    """Seleziona un campione random con seed fisso."""
    print(f"\n🎲 Selezione campione random (seed={seed}, size={sample_size})...")
    
    random.seed(seed)
    sample = random.sample(customers, min(sample_size, len(customers)))
    
    print(f"✅ Selezionati {len(sample)} clienti")
    return sample


def enrich_customers_data(customers: list, prodotti_map: dict, racc_map: dict):
    """Arricchisce i dati dei clienti con prodotti e raccomandazioni."""
    print("\n🔧 Arricchimento dati clienti...")
    
    enriched = []
    for customer in customers:
        cod = customer['codice_cliente']
        
        # Aggiungi prodotti posseduti come stringa separata da virgole
        prodotti = prodotti_map.get(cod, [])
        customer['prodotti_posseduti'] = ', '.join(prodotti) if prodotti else ''
        customer['num_prodotti_posseduti'] = len(prodotti)
        
        # Aggiungi statistiche raccomandazioni
        raccomandazioni = racc_map.get(cod, [])
        customer['num_raccomandazioni'] = len(raccomandazioni)
        customer['top_raccomandazione'] = raccomandazioni[0] if raccomandazioni else ''
        
        enriched.append(customer)
    
    print(f"✅ Dati arricchiti per {len(enriched)} clienti")
    return enriched


def save_to_csv(customers: list, output_file: str):
    """Salva i dati in CSV."""
    print(f"\n💾 Salvataggio dati in {output_file}...")
    
    # Converti in DataFrame
    df = pd.DataFrame(customers)
    
    # Ordina le colonne in modo logico
    column_order = [
        'codice_cliente',
        'timestamp',
        'nome',
        'cognome',
        'eta',
        'indirizzo',
        'citta',
        'provincia',
        'regione',
        'latitudine',
        'longitudine',
        'churn_attuale',
        'num_polizze_attuali',
        'cluster_nba',
        'cluster_risposta',
        'satisfaction_score',
        'engagement_score',
        'clv_stimato',
        'prodotti_posseduti',
        'num_prodotti_posseduti',
        'num_raccomandazioni',
        'top_raccomandazione'
    ]
    
    # Riordina le colonne (mantieni solo quelle esistenti)
    existing_columns = [col for col in column_order if col in df.columns]
    df = df[existing_columns]
    
    # Salva CSV
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    df.to_csv(output_file, index=False, encoding='utf-8')
    
    print(f"✅ File salvato: {output_file}")
    print(f"   - Righe: {len(df)}")
    print(f"   - Colonne: {len(df.columns)}")
    
    # Mostra preview
    print("\n📊 Preview dati (prime 3 righe):")
    print(df[['codice_cliente', 'nome', 'cognome', 'eta', 'citta', 'num_raccomandazioni']].head(3).to_string(index=False))


def main():
    """Funzione principale."""
    print("🚀 Avvio estrazione campione clienti\n")
    
    # Verifica credenziali
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("❌ Errore: SUPABASE_URL e SUPABASE_KEY devono essere definiti nel file .env")
        return
    
    # Crea client Supabase
    print("🔌 Connessione a Supabase...")
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✅ Connesso a Supabase\n")
    
    # Recupera tutti i clienti
    all_customers = fetch_all_customers(supabase)
    
    if len(all_customers) < SAMPLE_SIZE:
        print(f"⚠️  Attenzione: nel database ci sono solo {len(all_customers)} clienti, meno di {SAMPLE_SIZE}")
    
    # Seleziona campione random
    sample_customers = select_random_sample(all_customers, RANDOM_SEED, SAMPLE_SIZE)
    
    # Ottieni i codici clienti del campione
    sample_codes = [c['codice_cliente'] for c in sample_customers]
    
    # Recupera dati aggiuntivi
    prodotti_map = fetch_prodotti_posseduti(supabase, sample_codes)
    racc_map = fetch_raccomandazioni(supabase, sample_codes)
    
    # Arricchisci i dati
    enriched_customers = enrich_customers_data(sample_customers, prodotti_map, racc_map)
    
    # Salva in CSV
    save_to_csv(enriched_customers, OUTPUT_FILE)
    
    print("\n🎉 Processo completato!")
    print(f"\n💡 Per verificare la riproducibilità, esegui di nuovo lo script:")
    print(f"   python scripts/python/extract_sample.py")
    print(f"   I codici cliente dovrebbero essere gli stessi!")


if __name__ == "__main__":
    main()
