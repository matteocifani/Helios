"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                    HELIOS DATABASE UTILITIES                                   ║
║              Supabase Connection & Data Access Layer                          ║
╚═══════════════════════════════════════════════════════════════════════════════╝
"""

import os
import streamlit as st
from supabase import create_client, Client
from dotenv import load_dotenv
import pandas as pd

# Load environment variables
load_dotenv()


@st.cache_resource
def get_supabase_client() -> Client:
    """
    Initialize and cache Supabase client connection.
    """
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        st.error("⚠️ Supabase credentials not configured. Please set SUPABASE_URL and SUPABASE_KEY.")
        return None
    
    return create_client(url, key)


@st.cache_data(ttl=300)  # Cache for 5 minutes
def fetch_abitazioni() -> pd.DataFrame:
    """
    Fetch all abitazioni with risk scores from Supabase.
    """
    client = get_supabase_client()
    if not client:
        return pd.DataFrame()
    
    try:
        response = client.table("abitazioni").select(
            "id, codice_cliente, citta, latitudine, longitudine, "
            "zona_sismica, rischio_idrogeologico, risk_score, risk_category, "
            "solar_potential_kwh, premio_attuale, updated_at"
        ).execute()
        
        return pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"Error fetching abitazioni: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=300)
def fetch_clienti() -> pd.DataFrame:
    """
    Fetch client data with CLV and churn probability.
    """
    client = get_supabase_client()
    if not client:
        return pd.DataFrame()
    
    try:
        response = client.table("clienti").select(
            "codice_cliente, nome, cognome, eta, professione, reddito, "
            "churn_probability, latitudine, longitudine"
        ).execute()
        
        return pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"Error fetching clienti: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=300)
def fetch_risk_stats() -> dict:
    """
    Fetch aggregated risk statistics.
    """
    client = get_supabase_client()
    if not client:
        return {}
    
    try:
        # Get risk category counts
        response = client.rpc("get_risk_distribution").execute()
        return response.data if response.data else {}
    except Exception as e:
        # Fallback: calculate from data
        df = fetch_abitazioni()
        if df.empty:
            return {}
        
        stats = df['risk_category'].value_counts().to_dict()
        return {
            'critico': stats.get('Critico', 0),
            'alto': stats.get('Alto', 0),
            'medio': stats.get('Medio', 0),
            'basso': stats.get('Basso', 0),
            'total': len(df),
            'avg_score': round(df['risk_score'].mean(), 1)
        }


@st.cache_data(ttl=600)
def fetch_seismic_zones() -> pd.DataFrame:
    """
    Fetch reference seismic zone data.
    """
    client = get_supabase_client()
    if not client:
        return pd.DataFrame()
    
    try:
        response = client.table("ref_seismic_zones").select("*").execute()
        return pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"Error fetching seismic zones: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=600)
def fetch_hydro_zones() -> pd.DataFrame:
    """
    Fetch reference hydrogeological risk data.
    """
    client = get_supabase_client()
    if not client:
        return pd.DataFrame()
    
    try:
        response = client.table("ref_hydrogeological_zones").select("*").execute()
        return pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"Error fetching hydro zones: {e}")
        return pd.DataFrame()


def get_client_detail(codice_cliente: str) -> dict:
    """
    Get detailed information for a specific client.
    """
    client = get_supabase_client()
    if not client:
        return {}
    
    try:
        # Get client info
        client_response = client.table("clienti").select("*").eq("codice_cliente", codice_cliente).single().execute()
        
        # Get abitazione info
        abitazione_response = client.table("abitazioni").select("*").eq("codice_cliente", codice_cliente).execute()
        
        # Get polizze
        polizze_response = client.table("polizze").select("*").eq("codice_cliente", codice_cliente).execute()
        
        # Get sinistri
        sinistri_response = client.table("sinistri").select("*").eq("codice_cliente", codice_cliente).execute()
        
        return {
            "cliente": client_response.data if client_response.data else {},
            "abitazioni": abitazione_response.data if abitazione_response.data else [],
            "polizze": polizze_response.data if polizze_response.data else [],
            "sinistri": sinistri_response.data if sinistri_response.data else []
        }
    except Exception as e:
        st.error(f"Error fetching client detail: {e}")
        return {}


def search_clients(query: str, limit: int = 20) -> pd.DataFrame:
    """
    Search clients by ID, name, or city.
    """
    client = get_supabase_client()
    if not client:
        return pd.DataFrame()
    
    try:
        # Use ilike for case-insensitive search
        response = client.table("abitazioni").select(
            "*, clienti(nome, cognome, churn_probability)"
        ).or_(
            f"id.ilike.%{query}%,"
            f"codice_cliente.ilike.%{query}%,"
            f"citta.ilike.%{query}%"
        ).limit(limit).execute()
        
        return pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"Error searching clients: {e}")
        return pd.DataFrame()
