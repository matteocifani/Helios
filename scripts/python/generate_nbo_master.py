"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                    NBO MASTER JSON GENERATOR                                  ║
║         Generate Next Best Offer data from Supabase database                 ║
╚═══════════════════════════════════════════════════════════════════════════════╝

This script generates the nbo_master.json file using:
- REAL data from Supabase tables (clienti, polizze, abitazioni)
- All fields properly joined without nesting

Equivalent to the R script genera_prototipo_master.R but using Python + Supabase.
"""

import os
import sys
import json
import random
import math
from datetime import datetime, timezone
from typing import Dict, List, Optional
import argparse

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

# Set random seed for reproducibility
random.seed(42)

# Output path
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'Data', 'nbo_master.json')

# ═══════════════════════════════════════════════════════════════════════════════
# PROFITABILITY TABLE
# ═══════════════════════════════════════════════════════════════════════════════

PROFITABILITY_TABLE = {
    "Assicurazione Casa e Famiglia: Casa Serena": {
        "area_bisogno": "Protezione",
        "margine_medio_annuo": 450,
        "redditivita_norm": 0.75
    },
    "Polizza Salute e Infortuni: Salute Protetta": {
        "area_bisogno": "Protezione",
        "margine_medio_annuo": 520,
        "redditivita_norm": 0.87
    },
    "Polizza Vita a Premio Unico: Futuro Sicuro": {
        "area_bisogno": "Risparmio e Investimento",
        "margine_medio_annuo": 600,
        "redditivita_norm": 1.00
    },
    "Polizza Vita a Premi Ricorrenti: Risparmio Costante": {
        "area_bisogno": "Risparmio e Investimento",
        "margine_medio_annuo": 380,
        "redditivita_norm": 0.63
    },
    "Piano Individuale Pensionistico (PIP): Pensione Serenità": {
        "area_bisogno": "Previdenza",
        "margine_medio_annuo": 540,
        "redditivita_norm": 0.90
    }
}

# ═══════════════════════════════════════════════════════════════════════════════
# CHURN MODEL PARAMETERS (Simulated Logit)
# ═══════════════════════════════════════════════════════════════════════════════

CHURN_MODEL_PARAMS = {
    "intercept": -0.5,
    "coef_num_polizze": -0.42,
    "coef_anzianita": -0.08,
    "coef_visite": -0.15,
    "coef_satisfaction": -0.025,
    "coef_reclami": 0.35,
    "coef_eta": 0.015,
    "coef_reddito": -0.00001,
    "coef_engagement": -0.018,
    "coef_num_figli": -0.05,
    "coef_protezione": -0.25,
    "coef_risparmio": -0.30,
    "coef_previdenza": -0.35
}

# ═══════════════════════════════════════════════════════════════════════════════
# CLUSTER AFFINITY TABLE
# ═══════════════════════════════════════════════════════════════════════════════

CLUSTER_AFFINITY = {
    1: {"Protezione": 0.75, "Risparmio e Investimento": 0.42, "Previdenza": 0.25},
    2: {"Protezione": 0.50, "Risparmio e Investimento": 0.83, "Previdenza": 0.58},
    3: {"Protezione": 0.92, "Risparmio e Investimento": 0.33, "Previdenza": 0.30},
    4: {"Protezione": 0.67, "Risparmio e Investimento": 0.75, "Previdenza": 0.67},
    5: {"Protezione": 0.42, "Risparmio e Investimento": 1.00, "Previdenza": 0.92},
    6: {"Protezione": 1.00, "Risparmio e Investimento": 0.50, "Previdenza": 0.75},
    7: {"Protezione": 0.67, "Risparmio e Investimento": 0.58, "Previdenza": 0.50}
}


# ═══════════════════════════════════════════════════════════════════════════════
# DATABASE CONNECTION
# ═══════════════════════════════════════════════════════════════════════════════

def get_supabase_client() -> Optional[Client]:
    """Initialize Supabase client."""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

    if not url or not key:
        print("❌ ERROR: SUPABASE_URL and SUPABASE_KEY must be set in .env file")
        return None

    try:
        client = create_client(url, key)
        print("✅ Supabase client initialized")
        return client
    except Exception as e:
        print(f"❌ Failed to initialize Supabase: {e}")
        return None


def fetch_all_records(client: Client, table: str, columns: str = "*", chunk_size: int = 1000) -> List[Dict]:
    """Fetch all records from a table using pagination."""
    all_data = []
    offset = 0

    while True:
        try:
            response = client.table(table).select(columns).range(offset, offset + chunk_size - 1).execute()
            data = response.data

            if not data:
                break

            all_data.extend(data)
            print(f"  Fetched {len(data)} records from {table} (offset: {offset})")

            if len(data) < chunk_size:
                break

            offset += chunk_size

        except Exception as e:
            print(f"❌ Error fetching {table}: {e}")
            break

    return all_data


# ═══════════════════════════════════════════════════════════════════════════════
# SCORING FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def calculate_churn_logit(
    num_polizze: int,
    anzianita: float,
    visite: float,
    satisfaction: float,
    reclami: int,
    eta: int,
    reddito: float,
    engagement: float,
    num_figli: int,
    has_protezione: bool,
    has_risparmio: bool,
    has_previdenza: bool
) -> float:
    """Calculate churn probability using logistic regression model."""

    logit = (
        CHURN_MODEL_PARAMS["intercept"] +
        CHURN_MODEL_PARAMS["coef_num_polizze"] * num_polizze +
        CHURN_MODEL_PARAMS["coef_anzianita"] * anzianita +
        CHURN_MODEL_PARAMS["coef_visite"] * visite +
        CHURN_MODEL_PARAMS["coef_satisfaction"] * satisfaction +
        CHURN_MODEL_PARAMS["coef_reclami"] * reclami +
        CHURN_MODEL_PARAMS["coef_eta"] * eta +
        CHURN_MODEL_PARAMS["coef_reddito"] * reddito +
        CHURN_MODEL_PARAMS["coef_engagement"] * engagement +
        CHURN_MODEL_PARAMS["coef_num_figli"] * num_figli +
        CHURN_MODEL_PARAMS["coef_protezione"] * int(has_protezione) +
        CHURN_MODEL_PARAMS["coef_risparmio"] * int(has_risparmio) +
        CHURN_MODEL_PARAMS["coef_previdenza"] * int(has_previdenza)
    )

    # Sigmoid function
    prob = 1 / (1 + math.exp(-logit))
    return prob


def calculate_delta_churn(client_data: Dict, area_bisogno: str) -> Dict:
    """Calculate churn reduction from adding a product in a given area."""

    churn_prima = client_data["churn_probability"]

    # Simulate adding one product
    num_polizze_dopo = client_data["num_polizze"] + 1

    has_protezione_dopo = client_data["has_protezione"]
    has_risparmio_dopo = client_data["has_risparmio"]
    has_previdenza_dopo = client_data["has_previdenza"]

    if area_bisogno == "Protezione":
        has_protezione_dopo = True
    elif area_bisogno == "Risparmio e Investimento":
        has_risparmio_dopo = True
    elif area_bisogno == "Previdenza":
        has_previdenza_dopo = True

    churn_dopo = calculate_churn_logit(
        num_polizze=num_polizze_dopo,
        anzianita=client_data["anzianita"],
        visite=client_data["visite"],
        satisfaction=client_data["satisfaction"],
        reclami=client_data["reclami"],
        eta=client_data["eta"],
        reddito=client_data["reddito"],
        engagement=client_data["engagement"],
        num_figli=client_data["num_figli"],
        has_protezione=has_protezione_dopo,
        has_risparmio=has_risparmio_dopo,
        has_previdenza=has_previdenza_dopo
    )

    delta = churn_prima - churn_dopo

    return {
        "delta_churn": delta,
        "churn_prima": churn_prima,
        "churn_dopo": churn_dopo
    }


def generate_cluster_nba(eta: int, num_polizze: int, reddito: float,
                         propensione_vita: float, propensione_danni: float) -> int:
    """Generate NBA cluster based on demographic + behavioral patterns."""

    if eta < 35 and reddito < 40000:
        return 1
    elif eta < 35 and reddito >= 40000:
        return 2
    elif 35 <= eta < 55 and num_polizze <= 2:
        return 3
    elif 35 <= eta < 55 and num_polizze > 2:
        return 4
    elif eta >= 55 and propensione_vita > 0.6:
        return 5
    elif eta >= 55 and propensione_danni > 0.6:
        return 6
    else:
        return 7


def generate_recommendations(client_data: Dict) -> List[Dict]:
    """Generate NBO recommendations for a client."""

    cluster_nba = client_data["cluster_nba"]
    propensione_vita = client_data["propensione_vita"]
    propensione_danni = client_data["propensione_danni"]
    prodotti_posseduti = client_data.get("prodotti_posseduti", [])

    recommendations = []

    for prodotto, info in PROFITABILITY_TABLE.items():
        if prodotto in prodotti_posseduti:
            continue

        area_bisogno = info["area_bisogno"]

        if "Risparmio" in area_bisogno or "Investimento" in area_bisogno:
            propensione_score = propensione_vita * 100
        elif area_bisogno == "Protezione":
            propensione_score = propensione_danni * 100
        elif area_bisogno == "Previdenza":
            propensione_score = (propensione_vita * 0.7 + propensione_danni * 0.3) * 100
        else:
            propensione_score = 50.0

        delta_result = calculate_delta_churn(client_data, area_bisogno)
        redditivita_score = info["redditivita_norm"] * 100
        affinita_norm = CLUSTER_AFFINITY.get(cluster_nba, {}).get(area_bisogno, 0.5)
        affinita_cluster_score = affinita_norm * 100

        recommendations.append({
            "area_bisogno": area_bisogno,
            "prodotto": prodotto,
            "retention_gain_score": delta_result["delta_churn"],
            "redditivita_score": redditivita_score,
            "propensione_score": propensione_score,
            "affinita_cluster_score": affinita_cluster_score,
            "delta_churn": delta_result["delta_churn"],
            "churn_prima": delta_result["churn_prima"],
            "churn_dopo": delta_result["churn_dopo"]
        })

    if recommendations:
        max_delta = max(r["retention_gain_score"] for r in recommendations) or 0.001
        for r in recommendations:
            r["retention_gain_score"] = (r["retention_gain_score"] / max_delta) * 100

    recommendations.sort(
        key=lambda x: x["retention_gain_score"] + x["redditivita_score"] +
                      x["propensione_score"] + x["affinita_cluster_score"],
        reverse=True
    )

    output_recs = []
    for r in recommendations:
        output_recs.append({
            "area_bisogno": r["area_bisogno"],
            "prodotto": r["prodotto"],
            "componenti": {
                "retention_gain": round(r["retention_gain_score"], 1),
                "redditivita": round(r["redditivita_score"], 1),
                "propensione": round(r["propensione_score"], 1),
                "affinita_cluster": round(r["affinita_cluster_score"], 1)
            },
            "dettagli": {
                "delta_churn": round(r["delta_churn"], 4),
                "churn_prima": round(r["churn_prima"], 4),
                "churn_dopo": round(r["churn_dopo"], 4)
            }
        })

    return output_recs


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN PROCESSING
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description='Generate NBO Master JSON from Supabase')
    parser.add_argument('--sample', type=int, default=None,
                        help='Extract only N clients (must have abitazioni). If not set, processes all.')
    parser.add_argument('--only-with-abitazioni', action='store_true',
                        help='Only include clients that have abitazioni records')
    args = parser.parse_args()

    print("=" * 70)
    print("         NBO MASTER JSON GENERATOR")
    print("=" * 70)
    print()

    client = get_supabase_client()
    if not client:
        sys.exit(1)

    # ═══════════════════════════════════════════════════════════════════════════
    # FETCH DATA
    # ═══════════════════════════════════════════════════════════════════════════

    print("\n📥 Fetching data from Supabase...")

    print("\n1. Fetching clienti...")
    clienti = fetch_all_records(client, "clienti")
    print(f"   Total: {len(clienti)} clients")

    print("\n2. Fetching polizze...")
    polizze = fetch_all_records(client, "polizze")
    print(f"   Total: {len(polizze)} policies")

    print("\n3. Fetching abitazioni...")
    abitazioni = fetch_all_records(client, "abitazioni")
    print(f"   Total: {len(abitazioni)} properties")

    if not clienti:
        print("❌ No clients found in database!")
        sys.exit(1)

    # ═══════════════════════════════════════════════════════════════════════════
    # BUILD LOOKUP MAPS
    # ═══════════════════════════════════════════════════════════════════════════

    print("\n📊 Building lookup maps...")

    # Policy ownership map: codice_cliente -> list of active products
    policy_map = {}
    for p in polizze:
        stato = p.get("stato_polizza") or p.get("Stato_Polizza")
        if stato == "Attiva":
            cc = p.get("codice_cliente")
            prodotto = p.get("prodotto") or p.get("Prodotto")
            if cc and prodotto:
                if cc not in policy_map:
                    policy_map[cc] = []
                if prodotto not in policy_map[cc]:
                    policy_map[cc].append(prodotto)

    # Abitazioni map: codice_cliente -> first abitazione record
    abitazioni_map = {}
    for a in abitazioni:
        cc = a.get("codice_cliente")
        if cc and cc not in abitazioni_map:
            abitazioni_map[cc] = a

    print(f"   Clients with policies: {len(policy_map)}")
    print(f"   Clients with abitazioni: {len(abitazioni_map)}")

    # ═══════════════════════════════════════════════════════════════════════════
    # FILTER CLIENTS IF NEEDED
    # ═══════════════════════════════════════════════════════════════════════════

    if args.only_with_abitazioni or args.sample:
        # Filter to only clients with abitazioni
        clienti_filtered = [c for c in clienti if c.get("codice_cliente") in abitazioni_map]
        print(f"\n📋 Filtered to clients with abitazioni: {len(clienti_filtered)}")

        if args.sample and args.sample < len(clienti_filtered):
            # Random sample
            random.shuffle(clienti_filtered)
            clienti_filtered = clienti_filtered[:args.sample]
            print(f"   Sampled {args.sample} clients")

        clienti = clienti_filtered

    # ═══════════════════════════════════════════════════════════════════════════
    # PROCESS CLIENTS
    # ═══════════════════════════════════════════════════════════════════════════

    print(f"\n🔄 Generating NBO data for {len(clienti)} clients...")

    nbo_master_list = []

    for i, c in enumerate(clienti):
        if (i + 1) % 100 == 0:
            print(f"   Processing client {i + 1}/{len(clienti)}")

        codice_cliente = c.get("codice_cliente")

        # Get owned products
        prodotti_posseduti = policy_map.get(codice_cliente, [])
        num_polizze = len(prodotti_posseduti)

        # Product area flags
        has_protezione = any(
            "Casa Serena" in p or "Salute Protetta" in p
            for p in prodotti_posseduti
        )
        has_risparmio = any(
            "Futuro Sicuro" in p or "Risparmio Costante" in p
            for p in prodotti_posseduti
        )
        has_previdenza = any(
            "Pensione Serenità" in p
            for p in prodotti_posseduti
        )

        # Get real values from clienti table
        eta = c.get("eta") or 45
        reddito = c.get("reddito") or c.get("reddito_stimato") or 35000
        anzianita = c.get("anzianita_compagnia") or 5
        visite = c.get("visite_ultimo_anno") or 0
        satisfaction = c.get("satisfaction_score") or 75
        reclami = c.get("reclami_totali") or 0
        engagement = c.get("engagement_score") or 50
        num_figli = c.get("numero_figli") or 0
        propensione_vita = c.get("propensione_vita") or 0.5
        propensione_danni = c.get("propensione_danni") or 0.5
        cluster_risposta = c.get("cluster_risposta") or "Moderate_Responder"
        clv_stimato = c.get("clv_stimato") or 10000

        # Calculate churn using model (synthetic based on real features)
        churn_prob = calculate_churn_logit(
            num_polizze=num_polizze,
            anzianita=anzianita,
            visite=visite,
            satisfaction=satisfaction,
            reclami=reclami,
            eta=eta,
            reddito=reddito,
            engagement=engagement,
            num_figli=num_figli,
            has_protezione=has_protezione,
            has_risparmio=has_risparmio,
            has_previdenza=has_previdenza
        )

        # Generate NBA cluster
        cluster_nba = generate_cluster_nba(
            eta=eta,
            num_polizze=num_polizze,
            reddito=reddito,
            propensione_vita=propensione_vita,
            propensione_danni=propensione_danni
        )

        # Build client data for recommendations
        client_data = {
            "codice_cliente": codice_cliente,
            "eta": eta,
            "reddito": reddito,
            "num_polizze": num_polizze,
            "churn_probability": churn_prob,
            "cluster_nba": cluster_nba,
            "propensione_vita": propensione_vita,
            "propensione_danni": propensione_danni,
            "prodotti_posseduti": prodotti_posseduti,
            "has_protezione": has_protezione,
            "has_risparmio": has_risparmio,
            "has_previdenza": has_previdenza,
            "anzianita": anzianita,
            "visite": visite,
            "satisfaction": satisfaction,
            "reclami": reclami,
            "engagement": engagement,
            "num_figli": num_figli
        }

        # Generate recommendations
        raccomandazioni = generate_recommendations(client_data)

        # Get abitazione data (if exists)
        abit = abitazioni_map.get(codice_cliente, {})

        # Build output JSON - FLAT STRUCTURE with all real data
        cliente_json = {
            "codice_cliente": codice_cliente,
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),

            # Anagrafica - from clienti + abitazioni
            "anagrafica": {
                "nome": c.get("nome") or "",
                "cognome": c.get("cognome") or "",
                "eta": eta,
                "luogo_nascita": c.get("luogo_nascita") or "",
                "luogo_residenza": c.get("luogo_residenza") or "",
                "professione": c.get("professione") or "",
                "stato_civile": c.get("stato_civile") or "",
                "numero_figli": num_figli,
                # From abitazioni
                "indirizzo": abit.get("indirizzo_completo") or "",
                "via": abit.get("via") or "",
                "civico": abit.get("civico") or "",
                "citta": abit.get("citta") or c.get("luogo_residenza") or "",
                "cap": abit.get("cap") or "",
                "provincia": abit.get("provincia") or "",
                "latitudine": abit.get("latitudine") or c.get("latitudine"),
                "longitudine": abit.get("longitudine") or c.get("longitudine"),
            },

            # Raccomandazioni NBO
            "raccomandazioni": raccomandazioni,

            # Metadata - all real values from DB
            "metadata": {
                "churn_attuale": round(churn_prob, 4),
                "num_polizze_attuali": num_polizze,
                "cluster_nba": cluster_nba,
                "cluster_risposta": cluster_risposta,
                "prodotti_posseduti": prodotti_posseduti,
                "satisfaction_score": round(satisfaction, 1) if satisfaction else None,
                "engagement_score": round(engagement, 1) if engagement else None,
                "clv_stimato": clv_stimato,
                # Additional real data
                "reddito": reddito,
                "reddito_familiare": c.get("reddito_familiare"),
                "patrimonio_finanziario": c.get("patrimonio_finanziario_stimato"),
                "patrimonio_reale": c.get("patrimonio_reale_stimato"),
                "propensione_vita": round(propensione_vita, 4) if propensione_vita else None,
                "propensione_danni": round(propensione_danni, 4) if propensione_danni else None,
                "anzianita_compagnia": anzianita,
                "visite_ultimo_anno": visite,
                "reclami_totali": reclami,
                "agenzia": c.get("agenzia") or "",
                "zona_residenza": c.get("zona_residenza") or "",
            }
        }

        nbo_master_list.append(cliente_json)

    # ═══════════════════════════════════════════════════════════════════════════
    # SAVE OUTPUT
    # ═══════════════════════════════════════════════════════════════════════════

    print(f"\n💾 Saving JSON to {OUTPUT_PATH}...")

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(nbo_master_list, f, indent=2, ensure_ascii=False)

    # Also save as flat CSV
    csv_path = OUTPUT_PATH.replace('.json', '.csv')
    if args.sample:
        csv_path = os.path.join(os.path.dirname(OUTPUT_PATH), f'sample_{args.sample}_customers.csv')

    print(f"💾 Saving CSV to {csv_path}...")

    # Flatten the nested structure for CSV
    csv_rows = []
    for client in nbo_master_list:
        row = {
            'codice_cliente': client['codice_cliente'],
            'timestamp': client['timestamp'],
            # Anagrafica
            'nome': client['anagrafica']['nome'],
            'cognome': client['anagrafica']['cognome'],
            'eta': client['anagrafica']['eta'],
            'luogo_nascita': client['anagrafica'].get('luogo_nascita', ''),
            'luogo_residenza': client['anagrafica'].get('luogo_residenza', ''),
            'professione': client['anagrafica'].get('professione', ''),
            'stato_civile': client['anagrafica'].get('stato_civile', ''),
            'numero_figli': client['anagrafica'].get('numero_figli', 0),
            'indirizzo': client['anagrafica'].get('indirizzo', ''),
            'via': client['anagrafica'].get('via', ''),
            'civico': client['anagrafica'].get('civico', ''),
            'citta': client['anagrafica'].get('citta', ''),
            'cap': client['anagrafica'].get('cap', ''),
            'provincia': client['anagrafica'].get('provincia', ''),
            'latitudine': client['anagrafica'].get('latitudine'),
            'longitudine': client['anagrafica'].get('longitudine'),
            # Metadata
            'churn_attuale': client['metadata']['churn_attuale'],
            'num_polizze_attuali': client['metadata']['num_polizze_attuali'],
            'cluster_nba': client['metadata']['cluster_nba'],
            'cluster_risposta': client['metadata']['cluster_risposta'],
            'prodotti_posseduti': '; '.join(client['metadata'].get('prodotti_posseduti', [])),
            'satisfaction_score': client['metadata'].get('satisfaction_score'),
            'engagement_score': client['metadata'].get('engagement_score'),
            'clv_stimato': client['metadata'].get('clv_stimato'),
            'reddito': client['metadata'].get('reddito'),
            'reddito_familiare': client['metadata'].get('reddito_familiare'),
            'patrimonio_finanziario': client['metadata'].get('patrimonio_finanziario'),
            'patrimonio_reale': client['metadata'].get('patrimonio_reale'),
            'propensione_vita': client['metadata'].get('propensione_vita'),
            'propensione_danni': client['metadata'].get('propensione_danni'),
            'anzianita_compagnia': client['metadata'].get('anzianita_compagnia'),
            'visite_ultimo_anno': client['metadata'].get('visite_ultimo_anno'),
            'reclami_totali': client['metadata'].get('reclami_totali'),
            'agenzia': client['metadata'].get('agenzia', ''),
            'zona_residenza': client['metadata'].get('zona_residenza', ''),
            # Best recommendation (first one)
            'best_prodotto': client['raccomandazioni'][0]['prodotto'] if client['raccomandazioni'] else '',
            'best_area_bisogno': client['raccomandazioni'][0]['area_bisogno'] if client['raccomandazioni'] else '',
            'best_retention_gain': client['raccomandazioni'][0]['componenti']['retention_gain'] if client['raccomandazioni'] else None,
            'best_redditivita': client['raccomandazioni'][0]['componenti']['redditivita'] if client['raccomandazioni'] else None,
            'best_propensione': client['raccomandazioni'][0]['componenti']['propensione'] if client['raccomandazioni'] else None,
            'best_affinita_cluster': client['raccomandazioni'][0]['componenti']['affinita_cluster'] if client['raccomandazioni'] else None,
        }
        csv_rows.append(row)

    import csv
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=csv_rows[0].keys())
        writer.writeheader()
        writer.writerows(csv_rows)

    print(f"\n✅ Successfully generated:")
    print(f"   JSON: {OUTPUT_PATH}")
    print(f"   CSV:  {csv_path}")
    print(f"   Total clients: {len(nbo_master_list)}")

    # Print sample
    print("\n" + "=" * 70)
    print("SAMPLE OUTPUT (first client):")
    print("=" * 70)
    print(json.dumps(nbo_master_list[0], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
