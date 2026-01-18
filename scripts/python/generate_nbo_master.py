"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                    NBO MASTER JSON GENERATOR                                  ║
║         Generate Next Best Offer data from Supabase database                 ║
╚═══════════════════════════════════════════════════════════════════════════════╝

This script generates the nbo_master.json file using:
- REAL data from Supabase tables (clienti, polizze, etc.)
- SYNTHETIC model scores (propensity, churn simulation)

Equivalent to the R script genera_prototipo_master.R but using Python + Supabase.
"""

import os
import sys
import json
import random
import math
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from dotenv import load_dotenv
from supabase import create_client, Client
import numpy as np

# Load environment variables
load_dotenv()

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

# Set random seed for reproducibility
random.seed(42)
np.random.seed(42)

# Output path
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'Data', 'nbo_master.json')

# ═══════════════════════════════════════════════════════════════════════════════
# PROFITABILITY TABLE (Same as R script)
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
# CHURN MODEL PARAMETERS (Simulated Logit - Same as R script)
# ═══════════════════════════════════════════════════════════════════════════════

CHURN_MODEL_PARAMS = {
    "intercept": -0.5,
    "coef_num_polizze": -0.42,      # More policies = less churn
    "coef_anzianita": -0.08,        # More years = less churn
    "coef_visite": -0.15,           # More visits = less churn
    "coef_satisfaction": -0.025,    # Higher satisfaction = less churn
    "coef_reclami": 0.35,           # More complaints = more churn
    "coef_eta": 0.015,              # Older = slightly more churn
    "coef_reddito": -0.00001,       # Higher income = less churn (scaled)
    "coef_engagement": -0.018,      # Higher engagement = less churn
    "coef_num_figli": -0.05,        # More children = less churn (family ties)
    "coef_protezione": -0.25,       # Has protection products = less churn
    "coef_risparmio": -0.30,        # Has investment products = less churn
    "coef_previdenza": -0.35        # Has pension products = less churn (strongest)
}

# ═══════════════════════════════════════════════════════════════════════════════
# CLUSTER AFFINITY TABLE (Same as R script)
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
# CLUSTER RISPOSTA MAPPING
# ═══════════════════════════════════════════════════════════════════════════════

CLUSTER_RISPOSTA_LABELS = [
    "High_Responder",
    "Moderate_Responder",
    "Low_Responder",
    "Selective_Responder"
]


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
        return 1  # Young, low income
    elif eta < 35 and reddito >= 40000:
        return 2  # Young, high income
    elif 35 <= eta < 55 and num_polizze <= 2:
        return 3  # Middle age, low engagement
    elif 35 <= eta < 55 and num_polizze > 2:
        return 4  # Middle age, high engagement
    elif eta >= 55 and propensione_vita > 0.6:
        return 5  # Senior, investment-focused
    elif eta >= 55 and propensione_danni > 0.6:
        return 6  # Senior, protection-focused
    else:
        return 7  # Other


def generate_recommendations(client_data: Dict) -> List[Dict]:
    """Generate NBO recommendations for a client."""

    cluster_nba = client_data["cluster_nba"]
    propensione_vita = client_data["propensione_vita"]
    propensione_danni = client_data["propensione_danni"]
    prodotti_posseduti = client_data.get("prodotti_posseduti", [])

    recommendations = []

    # Calculate scores for each product
    for prodotto, info in PROFITABILITY_TABLE.items():
        # Skip if client already owns this product
        if prodotto in prodotti_posseduti:
            continue

        area_bisogno = info["area_bisogno"]

        # Propensity score based on area (0-100)
        if "Risparmio" in area_bisogno or "Investimento" in area_bisogno:
            propensione_score = propensione_vita * 100
        elif area_bisogno == "Protezione":
            propensione_score = propensione_danni * 100
        elif area_bisogno == "Previdenza":
            propensione_score = (propensione_vita * 0.7 + propensione_danni * 0.3) * 100
        else:
            propensione_score = 50.0

        # Calculate retention gain
        delta_result = calculate_delta_churn(client_data, area_bisogno)

        # Profitability score (0-100)
        redditivita_score = info["redditivita_norm"] * 100

        # Cluster affinity score (0-100)
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

    # Normalize retention gain to 0-100 scale
    if recommendations:
        max_delta = max(r["retention_gain_score"] for r in recommendations) or 0.001
        for r in recommendations:
            r["retention_gain_score"] = (r["retention_gain_score"] / max_delta) * 100

    # Sort by combined score (for display purposes)
    recommendations.sort(
        key=lambda x: x["retention_gain_score"] + x["redditivita_score"] +
                      x["propensione_score"] + x["affinita_cluster_score"],
        reverse=True
    )

    # Convert to output format
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
# SYNTHETIC DATA GENERATION (for fields not in DB)
# ═══════════════════════════════════════════════════════════════════════════════

def generate_synthetic_fields(client: Dict) -> Dict:
    """Generate synthetic fields that may not exist in the database."""

    # Use client ID as seed for reproducibility
    client_seed = hash(client.get("codice_cliente", 0)) % (2**31)
    rng = random.Random(client_seed)

    # Generate synthetic values if not present
    synthetic = {}

    # Anzianità (years with company) - synthetic
    synthetic["anzianita"] = client.get("anzianita", rng.uniform(1, 20))

    # Visite ultimo anno - synthetic
    synthetic["visite"] = client.get("visite_ultimo_anno", rng.randint(0, 12))

    # Satisfaction score - synthetic (60-100)
    synthetic["satisfaction"] = client.get("satisfaction_score", rng.uniform(60, 100))

    # Reclami - synthetic (0-3)
    synthetic["reclami"] = client.get("reclami_totali", rng.choices([0, 1, 2, 3], weights=[0.7, 0.2, 0.08, 0.02])[0])

    # Engagement score - synthetic (20-100)
    synthetic["engagement"] = client.get("engagement_score", rng.uniform(20, 100))

    # Numero figli - synthetic (0-4)
    synthetic["num_figli"] = client.get("num_figli", rng.choices([0, 1, 2, 3, 4], weights=[0.3, 0.25, 0.3, 0.1, 0.05])[0])

    # Propensione acquisto vita (0-1) - synthetic
    synthetic["propensione_vita"] = client.get("propensione_vita", rng.uniform(0.2, 0.9))

    # Propensione acquisto danni (0-1) - synthetic
    synthetic["propensione_danni"] = client.get("propensione_danni", rng.uniform(0.2, 0.9))

    return synthetic


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN PROCESSING
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    print("=" * 70)
    print("         NBO MASTER JSON GENERATOR")
    print("=" * 70)
    print()

    # Initialize Supabase client
    client = get_supabase_client()
    if not client:
        sys.exit(1)

    # Fetch data from Supabase
    print("\n📥 Fetching data from Supabase...")

    print("\n1. Fetching clienti...")
    clienti = fetch_all_records(client, "clienti")
    print(f"   Total: {len(clienti)} clients")

    print("\n2. Fetching polizze...")
    polizze = fetch_all_records(client, "polizze")
    print(f"   Total: {len(polizze)} policies")

    print("\n3. Fetching abitazioni (for addresses)...")
    abitazioni = fetch_all_records(client, "abitazioni")
    print(f"   Total: {len(abitazioni)} properties")

    if not clienti:
        print("❌ No clients found in database!")
        sys.exit(1)

    # Build policy ownership map
    print("\n📊 Processing policy ownership...")
    policy_map = {}  # codice_cliente -> list of products
    for p in polizze:
        if p.get("stato_polizza") == "Attiva" or p.get("Stato_Polizza") == "Attiva":
            cc = p.get("codice_cliente")
            prodotto = p.get("prodotto") or p.get("Prodotto")
            if cc and prodotto:
                if cc not in policy_map:
                    policy_map[cc] = []
                if prodotto not in policy_map[cc]:
                    policy_map[cc].append(prodotto)

    # Build address map from abitazioni
    print("📊 Processing addresses...")
    address_map = {}  # codice_cliente -> address info
    for a in abitazioni:
        cc = a.get("codice_cliente")
        if cc and cc not in address_map:
            address_map[cc] = {
                "citta": a.get("citta", ""),
                "provincia": a.get("provincia", ""),
                "regione": a.get("regione", ""),
                "latitudine": a.get("latitudine"),
                "longitudine": a.get("longitudine"),
                "indirizzo": a.get("indirizzo", "")
            }

    # Process each client
    print(f"\n🔄 Generating NBO recommendations for {len(clienti)} clients...")

    nbo_master_list = []

    for i, c in enumerate(clienti):
        if (i + 1) % 100 == 0:
            print(f"   Processing client {i + 1}/{len(clienti)}")

        codice_cliente = c.get("codice_cliente")

        # Get owned products
        prodotti_posseduti = policy_map.get(codice_cliente, [])
        num_polizze = len(prodotti_posseduti)

        # Determine product area flags
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

        # Get synthetic fields
        synthetic = generate_synthetic_fields(c)

        # Get basic client info
        eta = c.get("eta") or c.get("Età") or 45
        reddito = c.get("reddito") or c.get("reddito_stimato") or c.get("Reddito Stimato") or 35000

        # Calculate churn probability
        churn_prob = calculate_churn_logit(
            num_polizze=num_polizze,
            anzianita=synthetic["anzianita"],
            visite=synthetic["visite"],
            satisfaction=synthetic["satisfaction"],
            reclami=synthetic["reclami"],
            eta=eta,
            reddito=reddito,
            engagement=synthetic["engagement"],
            num_figli=synthetic["num_figli"],
            has_protezione=has_protezione,
            has_risparmio=has_risparmio,
            has_previdenza=has_previdenza
        )

        # Generate NBA cluster
        cluster_nba = generate_cluster_nba(
            eta=eta,
            num_polizze=num_polizze,
            reddito=reddito,
            propensione_vita=synthetic["propensione_vita"],
            propensione_danni=synthetic["propensione_danni"]
        )

        # Build client data dict for recommendation generation
        client_data = {
            "codice_cliente": codice_cliente,
            "eta": eta,
            "reddito": reddito,
            "num_polizze": num_polizze,
            "churn_probability": churn_prob,
            "cluster_nba": cluster_nba,
            "propensione_vita": synthetic["propensione_vita"],
            "propensione_danni": synthetic["propensione_danni"],
            "prodotti_posseduti": prodotti_posseduti,
            "has_protezione": has_protezione,
            "has_risparmio": has_risparmio,
            "has_previdenza": has_previdenza,
            "anzianita": synthetic["anzianita"],
            "visite": synthetic["visite"],
            "satisfaction": synthetic["satisfaction"],
            "reclami": synthetic["reclami"],
            "engagement": synthetic["engagement"],
            "num_figli": synthetic["num_figli"]
        }

        # Generate recommendations
        raccomandazioni = generate_recommendations(client_data)

        # Get address info
        addr = address_map.get(codice_cliente, {})

        # Generate cluster risposta (synthetic)
        rng = random.Random(hash(codice_cliente) % (2**31))
        cluster_risposta = rng.choice(CLUSTER_RISPOSTA_LABELS)

        # Build output object
        cliente_json = {
            "codice_cliente": f"CLI_{codice_cliente}",
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "anagrafica": {
                "nome": c.get("nome") or c.get("Nome") or "",
                "cognome": c.get("cognome") or c.get("Cognome") or "",
                "eta": eta,
                "indirizzo": addr.get("indirizzo", f"Via {rng.choice(['Roma', 'Garibaldi', 'Mazzini', 'Dante'])}, {rng.randint(1, 200)}"),
                "citta": addr.get("citta", ""),
                "provincia": addr.get("provincia", ""),
                "regione": addr.get("regione", ""),
                "latitudine": round(addr.get("latitudine") or c.get("latitudine") or 44.5, 6),
                "longitudine": round(addr.get("longitudine") or c.get("longitudine") or 11.3, 6)
            },
            "raccomandazioni": raccomandazioni,
            "metadata": {
                "churn_attuale": round(churn_prob, 4),
                "num_polizze_attuali": num_polizze,
                "cluster_nba": cluster_nba,
                "cluster_risposta": cluster_risposta,
                "prodotti_posseduti": prodotti_posseduti,
                "satisfaction_score": round(synthetic["satisfaction"], 1),
                "engagement_score": round(synthetic["engagement"], 0),
                "clv_stimato": c.get("clv_stimato") or c.get("CLV_Stimato") or rng.randint(5000, 50000)
            }
        }

        nbo_master_list.append(cliente_json)

    # Save output
    print(f"\n💾 Saving to {OUTPUT_PATH}...")

    # Ensure directory exists
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(nbo_master_list, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Successfully generated nbo_master.json")
    print(f"   Total clients: {len(nbo_master_list)}")
    print(f"   Output: {OUTPUT_PATH}")

    # Print sample
    print("\n" + "=" * 70)
    print("SAMPLE OUTPUT (first client):")
    print("=" * 70)
    print(json.dumps(nbo_master_list[0], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
