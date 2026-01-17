"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                         🌞 PROGETTO HELIOS                                     ║
║              Ecosistema Assicurativo Geo-Cognitivo                            ║
║                     Dashboard FluidView v1.0                                   ║
╚═══════════════════════════════════════════════════════════════════════════════╝
"""

import streamlit as st
import pandas as pd
import pydeck as pdk
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from ada_chat_enhanced import render_ada_chat
import json
import folium
from streamlit_folium import folium_static

# Import constants
from constants import (
    DEFAULT_SEISMIC_ZONE,
    SEISMIC_ZONE_COLORS,
    ABITAZIONI_COLUMNS,
)

# Import db utilities
from db_utils import (
    fetch_abitazioni,
    fetch_clienti,
    check_client_interactions,
    is_client_eligible_for_top20,
    check_all_clients_interactions_batch,
    insert_phone_call_interaction
)

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURAZIONE PAGINA
# ═══════════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Helios | Geo-Cognitive Insurance",
    page_icon="☀️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ═══════════════════════════════════════════════════════════════════════════════
# CUSTOM CSS - Design System "Aurora Borealis meets Data Visualization"
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<style>
    /* ═══════════════════════════════════════════════════════════════════════
       GOOGLE FONTS IMPORT
    ═══════════════════════════════════════════════════════════════════════ */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Playfair+Display:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    /* ═══════════════════════════════════════════════════════════════════════
       CSS VARIABLES - Vita Sicura Light Theme
    ═══════════════════════════════════════════════════════════════════════ */
    :root {
        /* Primary Colors (from logo) */
        --vs-navy: #1B3A5F;
        --vs-navy-light: #2C5282;
        --vs-teal: #00A0B0;
        --vs-cyan: #00C9D4;
        --vs-aqua: #B8E6E8;

        /* Backgrounds */
        --vs-white: #FFFFFF;
        --vs-off-white: #FAFBFC;
        --vs-gray-light: #F3F4F6;
        --vs-glass: rgba(255, 255, 255, 0.85);

        /* Text */
        --vs-text-primary: #1B3A5F;
        --vs-text-secondary: #64748B;
        --vs-text-muted: #94A3B8;

        /* Borders */
        --vs-border: #E2E8F0;
        --vs-border-medium: #CBD5E1;
        --vs-border-accent: rgba(0, 160, 176, 0.3);

        /* Risk Colors - Light theme */
        --risk-critical: #DC2626;
        --risk-critical-bg: #FEE2E2;
        --risk-high: #EA580C;
        --risk-high-bg: #FFEDD5;
        --risk-medium: #CA8A04;
        --risk-medium-bg: #FEF9C3;
        --risk-low: #16A34A;
        --risk-low-bg: #DCFCE7;

        /* Effects */
        --shadow-sm: 0 1px 2px 0 rgba(27, 58, 95, 0.05);
        --shadow-md: 0 4px 6px -1px rgba(27, 58, 95, 0.07), 0 2px 4px -1px rgba(27, 58, 95, 0.04);
        --shadow-lg: 0 10px 15px -3px rgba(27, 58, 95, 0.08), 0 4px 6px -2px rgba(27, 58, 95, 0.04);
        --shadow-xl: 0 20px 25px -5px rgba(27, 58, 95, 0.1), 0 10px 10px -5px rgba(27, 58, 95, 0.04);
        --glow-teal: 0 0 20px rgba(0, 160, 176, 0.15);

        /* Legacy aliases for compatibility */
        --helios-sun: #00A0B0;
        --helios-amber: #00C9D4;
        --helios-coral: #38B2AC;
        --aurora-cyan: #00A0B0;
        --deep-space: #FFFFFF;
        --space-gray: #F3F4F6;
        --star-white: #1B3A5F;
        --comet-gray: #64748B;
        --glass-bg: rgba(255, 255, 255, 0.85);
        --glass-border: #E2E8F0;
    }

    /* ═══════════════════════════════════════════════════════════════════════
       GLOBAL STYLES
    ═══════════════════════════════════════════════════════════════════════ */
    .stApp {
        background: linear-gradient(180deg, var(--vs-white) 0%, var(--vs-gray-light) 100%);
        background-attachment: fixed;
    }

    /* Subtle gradient overlay */
    .stApp::before {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        height: 400px;
        background: linear-gradient(180deg, rgba(0, 160, 176, 0.03) 0%, transparent 100%);
        pointer-events: none;
        z-index: 0;
    }

    /* Typography */
    h1, h2, h3, h4, h5, h6, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        color: var(--vs-navy) !important;
        letter-spacing: -0.025em;
    }

    p, span, div, .stMarkdown p {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        color: var(--vs-text-secondary);
    }

    code, .stCode {
        font-family: 'JetBrains Mono', monospace !important;
    }

    /* ═══════════════════════════════════════════════════════════════════════
       SIDEBAR STYLING
    ═══════════════════════════════════════════════════════════════════════ */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, var(--vs-white) 0%, var(--vs-gray-light) 100%) !important;
        border-right: 1px solid var(--vs-border) !important;
    }

    [data-testid="stSidebar"]::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 200px;
        background: linear-gradient(180deg, rgba(0, 160, 176, 0.05) 0%, transparent 100%);
        pointer-events: none;
    }

    [data-testid="stSidebar"] .stMarkdown h1 {
        background: linear-gradient(135deg, var(--vs-teal) 0%, var(--vs-cyan) 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 800;
        font-size: 1.75rem;
        text-align: center;
        padding: 1rem 0;
    }

    [data-testid="stSidebar"] .stSelectbox > div > div {
        background: var(--vs-white) !important;
        border: 1px solid var(--vs-border) !important;
        border-radius: 12px !important;
        transition: all 0.2s ease;
    }

    [data-testid="stSidebar"] .stSelectbox > div > div:hover {
        border-color: var(--vs-teal) !important;
    }

    [data-testid="stSidebar"] .stSelectbox > div > div:focus-within {
        border-color: var(--vs-teal) !important;
        box-shadow: 0 0 0 3px rgba(0, 160, 176, 0.15);
    }

    /* ═══════════════════════════════════════════════════════════════════════
       METRIC CARDS
    ═══════════════════════════════════════════════════════════════════════ */
    [data-testid="stMetric"] {
        background: var(--vs-glass) !important;
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid var(--vs-border);
        border-radius: 20px;
        padding: 1.5rem;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
        box-shadow: var(--shadow-md);
    }

    [data-testid="stMetric"]::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, var(--vs-teal) 0%, var(--vs-cyan) 100%);
        opacity: 0;
        transition: opacity 0.3s ease;
    }

    [data-testid="stMetric"]:hover {
        transform: translateY(-4px);
        box-shadow: var(--shadow-xl), var(--glow-teal);
        border-color: var(--vs-border-accent);
    }

    [data-testid="stMetric"]:hover::before {
        opacity: 1;
    }

    [data-testid="stMetricLabel"] {
        font-family: 'Inter', sans-serif !important;
        font-weight: 600;
        color: var(--vs-text-muted) !important;
        text-transform: uppercase;
        font-size: 0.7rem !important;
        letter-spacing: 0.1em;
    }

    [data-testid="stMetricValue"] {
        font-family: 'JetBrains Mono', monospace !important;
        font-weight: 700;
        color: var(--vs-navy) !important;
        font-size: 2rem !important;
        letter-spacing: -0.025em;
    }

    [data-testid="stMetricDelta"] {
        font-family: 'Inter', sans-serif !important;
        font-size: 0.8rem !important;
        font-weight: 500;
    }

    /* ═══════════════════════════════════════════════════════════════════════
       CUSTOM COMPONENTS
    ═══════════════════════════════════════════════════════════════════════ */
    .hero-header {
        text-align: center;
        padding: 1.5rem 0 2rem;
        position: relative;
    }

    .hero-title {
        font-family: 'Playfair Display', serif !important;
        font-size: 2.75rem !important;
        font-weight: 700 !important;
        color: var(--vs-navy) !important;
        -webkit-text-fill-color: var(--vs-navy);
        margin-bottom: 0.5rem;
        letter-spacing: -0.03em;
    }

    .hero-subtitle {
        font-family: 'Inter', sans-serif !important;
        font-size: 0.9rem !important;
        color: var(--vs-text-secondary) !important;
        font-weight: 500;
        letter-spacing: 0.15em;
        text-transform: uppercase;
    }

    .glass-card {
        background: var(--vs-glass);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid var(--vs-border);
        border-radius: 20px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: var(--shadow-md);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }

    .glass-card:hover {
        box-shadow: var(--shadow-lg);
        transform: translateY(-2px);
    }

    .risk-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem 1rem;
        border-radius: 100px;
        font-family: 'Inter', sans-serif;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        transition: all 0.2s ease;
    }

    .risk-critical {
        background: var(--risk-critical-bg);
        color: var(--risk-critical);
        border: 1px solid rgba(220, 38, 38, 0.2);
    }
    .risk-high {
        background: var(--risk-high-bg);
        color: var(--risk-high);
        border: 1px solid rgba(234, 88, 12, 0.2);
    }
    .risk-medium {
        background: var(--risk-medium-bg);
        color: var(--risk-medium);
        border: 1px solid rgba(202, 138, 4, 0.2);
    }
    .risk-low {
        background: var(--risk-low-bg);
        color: var(--risk-low);
        border: 1px solid rgba(22, 163, 74, 0.2);
    }

    .stat-highlight {
        font-family: 'JetBrains Mono', monospace;
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, var(--vs-teal), var(--vs-cyan));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        line-height: 1;
    }

    .section-divider {
        height: 1px;
        background: linear-gradient(90deg,
            transparent 0%,
            var(--vs-border) 20%,
            var(--vs-teal) 50%,
            var(--vs-border) 80%,
            transparent 100%);
        margin: 2rem 0;
    }

    /* ═══════════════════════════════════════════════════════════════════════
       BUTTONS & INTERACTIONS
    ═══════════════════════════════════════════════════════════════════════ */
    .stButton > button {
        font-family: 'Inter', sans-serif !important;
        font-weight: 600;
        font-size: 0.875rem;
        background: linear-gradient(135deg, var(--vs-teal) 0%, var(--vs-cyan) 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.75rem 1.5rem;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 4px 6px -1px rgba(0, 160, 176, 0.25);
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow-lg), var(--glow-teal);
    }

    .stButton > button:active {
        transform: translateY(0);
    }

    /* Select boxes */
    .stSelectbox > div > div {
        background: var(--vs-white) !important;
        border: 1px solid var(--vs-border) !important;
        border-radius: 12px !important;
        color: var(--vs-navy) !important;
        transition: all 0.2s ease;
    }

    .stSelectbox > div > div:hover {
        border-color: var(--vs-border-medium) !important;
    }

    .stSelectbox > div > div:focus-within {
        border-color: var(--vs-teal) !important;
        box-shadow: 0 0 0 3px rgba(0, 160, 176, 0.15);
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.25rem;
        background: var(--vs-gray-light);
        padding: 0.375rem;
        border-radius: 16px;
        border: 1px solid var(--vs-border);
    }

    .stTabs [data-baseweb="tab"] {
        font-family: 'Inter', sans-serif !important;
        font-weight: 500;
        font-size: 0.875rem;
        color: var(--vs-text-secondary);
        background: transparent;
        border-radius: 12px;
        padding: 0.75rem 1.25rem;
        transition: all 0.2s ease;
    }

    .stTabs [data-baseweb="tab"]:hover {
        background: rgba(255, 255, 255, 0.7);
        color: var(--vs-navy);
    }

    .stTabs [aria-selected="true"] {
        background: var(--vs-white) !important;
        color: var(--vs-navy) !important;
        font-weight: 600;
        box-shadow: var(--shadow-sm);
    }

    /* Text Input */
    .stTextInput > div > div > input {
        font-family: 'Inter', sans-serif;
        background: var(--vs-white);
        border: 1px solid var(--vs-border);
        border-radius: 12px;
        padding: 0.75rem 1rem;
        color: var(--vs-navy);
        transition: all 0.2s ease;
    }

    .stTextInput > div > div > input:focus {
        border-color: var(--vs-teal);
        box-shadow: 0 0 0 3px rgba(0, 160, 176, 0.15);
        outline: none;
    }

    /* DataFrame styling */
    .stDataFrame {
        border-radius: 16px;
        overflow: hidden;
        border: 1px solid var(--vs-border);
        box-shadow: var(--shadow-sm);
    }

    /* Progress bar */
    .stProgress > div > div {
        background: linear-gradient(90deg, var(--vs-teal), var(--vs-cyan));
        border-radius: 100px;
    }

    /* Expander */
    .streamlit-expanderHeader {
        font-family: 'Inter', sans-serif !important;
        font-weight: 600;
        background: var(--vs-white);
        border: 1px solid var(--vs-border);
        border-radius: 12px;
    }

    /* ═══════════════════════════════════════════════════════════════════════
       ANIMATIONS
    ═══════════════════════════════════════════════════════════════════════ */
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }

    @keyframes shimmer {
        0% { background-position: -200% 0; }
        100% { background-position: 200% 0; }
    }

    .animate-fade-in {
        animation: fadeInUp 0.5s cubic-bezier(0.4, 0, 0.2, 1) forwards;
    }

    /* ═══════════════════════════════════════════════════════════════════════
       RESPONSIVE ADJUSTMENTS
    ═══════════════════════════════════════════════════════════════════════ */
    @media (max-width: 768px) {
        .hero-title { font-size: 2rem !important; }
        .stat-highlight { font-size: 1.75rem; }
        [data-testid="stMetricValue"] { font-size: 1.5rem !important; }
    }
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# DATA LOADING FROM SUPABASE
# ═══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=300)
def load_data():
    """
    Load real data from Supabase.
    """
    # Fetch data
    df_abitazioni = fetch_abitazioni()
    df_clienti = fetch_clienti()

    if df_abitazioni.empty:
        # If no data is found, return empty dataframe with expected columns to avoid crashes
        return pd.DataFrame(columns=ABITAZIONI_COLUMNS)

    # Merge data
    # We want details of the habitation, enriched with client info (CLV, churn)

    # Rename clv_stimato to clv for compatibility
    if not df_clienti.empty:
        df_clienti = df_clienti.rename(columns={'clv_stimato': 'clv'})

        # Select only necessary columns from client to avoid duplicates/conflicts
        client_cols = ['codice_cliente', 'clv', 'churn_probability']
        # Filter only existing columns
        client_cols = [c for c in client_cols if c in df_clienti.columns]

        df_clienti_subset = df_clienti[client_cols]

        # Merge on codice_cliente
        df = df_abitazioni.merge(df_clienti_subset, on='codice_cliente', how='left')
    else:
        # No client data available, use abitazioni only
        df = df_abitazioni
        df['clv'] = 0
        df['churn_probability'] = 0.0

    # Ensure numeric types with protection against invalid values
    df['risk_score'] = pd.to_numeric(df['risk_score'], errors='coerce').fillna(0)
    df['clv'] = pd.to_numeric(df['clv'], errors='coerce').fillna(0)
    df['churn_probability'] = pd.to_numeric(df['churn_probability'], errors='coerce').fillna(0)
    df['zona_sismica'] = pd.to_numeric(df['zona_sismica'], errors='coerce').fillna(DEFAULT_SEISMIC_ZONE)

    # Fill missing values
    df['risk_category'] = df['risk_category'].fillna('Non valutato')
    df['citta'] = df['citta'].fillna('Sconosciuta')

    # Normalize City Names (Title Case)
    df['citta'] = df['citta'].astype(str).str.title()

    return df


def get_risk_stats(df):
    """Calculate risk distribution statistics."""
    stats = df['risk_category'].value_counts()
    # Protect against division by zero and NaN
    total = len(df)
    if total > 0:
        avg_score = df['risk_score'].mean()
        avg_score = round(avg_score, 1) if not pd.isna(avg_score) else 0
        high_risk_pct = round((stats.get('Critico', 0) + stats.get('Alto', 0)) / total * 100, 1)
    else:
        avg_score = 0
        high_risk_pct = 0

    return {
        'critico': stats.get('Critico', 0),
        'alto': stats.get('Alto', 0),
        'medio': stats.get('Medio', 0),
        'basso': stats.get('Basso', 0),
        'total': total,
        'avg_score': avg_score,
        'high_risk_pct': high_risk_pct
    }


# ═══════════════════════════════════════════════════════════════════════════════
# NBO FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=300)
def load_nbo_data():
    """Load NBO data from JSON file."""
    try:
        with open('Data/nbo_master.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        st.error("File Data/nbo_master.json non trovato")
        return []
    except json.JSONDecodeError:
        st.error("Errore nel parsing del file JSON")
        return []


def calculate_recommendation_score(rec, weights):
    """Calculate weighted score for a recommendation."""
    components = rec['componenti']
    score = (
        components['retention_gain'] * weights['retention'] / 100 +
        components['redditivita'] * weights['redditivita'] / 100 +
        components['propensione'] * weights['propensione'] / 100
    )
    return score


def get_all_recommendations(data, weights, filter_top20=True):
    """
    Get all recommendations with scores across all clients.

    Args:
        data: Client data with recommendations
        weights: Scoring weights
        filter_top20: If True, filter out clients not eligible for Top 20

    Returns:
        List of recommendations sorted by score (descending)
    """
    # Batch check all clients at once (MUCH faster - 3 queries instead of N*5)
    if filter_top20:
        all_client_codes = [client['codice_cliente'] for client in data]
        batch_interactions = check_all_clients_interactions_batch(all_client_codes)
    else:
        batch_interactions = {}

    all_recs = []
    for client in data:
        codice_cliente = client['codice_cliente']

        # Get pre-fetched interaction data from batch
        if filter_top20:
            indicators = batch_interactions.get(codice_cliente, {})
            is_eligible = not any(indicators.values())  # Eligible if NO interactions

            # Store eligibility status in client data for later use
            client['_is_eligible_top20'] = is_eligible
            client['_interaction_indicators'] = indicators
        else:
            is_eligible = True
            client['_is_eligible_top20'] = True
            client['_interaction_indicators'] = {}

        # Only include eligible clients in Top 20 list
        if not filter_top20 or is_eligible:
            for rec in client['raccomandazioni']:
                score = calculate_recommendation_score(rec, weights)
                all_recs.append({
                    'codice_cliente': codice_cliente,
                    'nome': client['anagrafica']['nome'],
                    'cognome': client['anagrafica']['cognome'],
                    'prodotto': rec['prodotto'],
                    'area_bisogno': rec['area_bisogno'],
                    'score': score,
                    'client_data': client,
                    'recommendation': rec
                })

    return sorted(all_recs, key=lambda x: x['score'], reverse=True)


# ═══════════════════════════════════════════════════════════════════════════════
# SESSION STATE INITIALIZATION
# ═══════════════════════════════════════════════════════════════════════════════

# Map layer toggles
if 'layer_scatter' not in st.session_state:
    st.session_state.layer_scatter = True
if 'layer_heatmap' not in st.session_state:
    st.session_state.layer_heatmap = True
if 'layer_columns' not in st.session_state:
    st.session_state.layer_columns = False

# Map selection state
if 'selected_client_id' not in st.session_state:
    st.session_state.selected_client_id = None
if 'selected_abitazione' not in st.session_state:
    st.session_state.selected_abitazione = None

# A.D.A. integration
if 'ada_auto_prompt' not in st.session_state:
    st.session_state.ada_auto_prompt = None

# User info (for login - to be implemented)
if 'user_name' not in st.session_state:
    st.session_state.user_name = "Agente Vita Sicura"  # Default until login is implemented
if 'user_email' not in st.session_state:
    st.session_state.user_email = "agente@vitasicura.it"  # Default until login is implemented
if 'user_phone' not in st.session_state:
    st.session_state.user_phone = "+39 02 1234 5678"  # Default until login is implemented

# Dashboard mode
if 'dashboard_mode' not in st.session_state:
    st.session_state.dashboard_mode = 'Helios View'

# NBO state
if 'nbo_page' not in st.session_state:
    st.session_state.nbo_page = 'dashboard'
if 'nbo_weights' not in st.session_state:
    st.session_state.nbo_weights = {
        'retention': 0.33,
        'redditivita': 0.33,
        'propensione': 0.34
    }
if 'nbo_selected_client' not in st.session_state:
    st.session_state.nbo_selected_client = None
if 'nbo_selected_recommendation' not in st.session_state:
    st.session_state.nbo_selected_recommendation = None

# ═══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════════

with st.sidebar:
    # Sidebar header with logo
    st.markdown("""
    <div style="text-align: center; padding: 1rem 0 0.5rem;">
        <div style="display: inline-flex; align-items: center; gap: 0.5rem;">
            <svg width="32" height="32" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
                <defs>
                    <linearGradient id="tealGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" stop-color="#00A0B0"/>
                        <stop offset="100%" stop-color="#00C9D4"/>
                    </linearGradient>
                    <radialGradient id="centerGlow" cx="50%" cy="50%" r="50%">
                        <stop offset="0%" stop-color="#FFFFFF"/>
                        <stop offset="60%" stop-color="#B8E6E8"/>
                        <stop offset="100%" stop-color="#00C9D4"/>
                    </radialGradient>
                </defs>
                <circle cx="50" cy="50" r="20" fill="url(#centerGlow)"/>
                <circle cx="50" cy="50" r="20" fill="none" stroke="url(#tealGrad)" stroke-width="2"/>
                <circle cx="50" cy="50" r="35" fill="none" stroke="url(#tealGrad)" stroke-width="1.5"/>
                <g stroke="url(#tealGrad)" stroke-width="2" fill="none">
                    <line x1="50" y1="10" x2="50" y2="25"/>
                    <line x1="50" y1="75" x2="50" y2="90"/>
                    <line x1="10" y1="50" x2="25" y2="50"/>
                    <line x1="75" y1="50" x2="90" y2="50"/>
                    <line x1="22" y1="22" x2="32" y2="32"/>
                    <line x1="68" y1="68" x2="78" y2="78"/>
                    <line x1="78" y1="22" x2="68" y2="32"/>
                    <line x1="32" y1="68" x2="22" y2="78"/>
                </g>
            </svg>
            <span style="font-family: 'Inter', sans-serif; font-size: 1.5rem; font-weight: 800; background: linear-gradient(135deg, #00A0B0 0%, #00C9D4 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">HELIOS</span>
        </div>
        <p style="font-family: 'Inter', sans-serif; font-size: 0.65rem; color: #94A3B8; letter-spacing: 0.05em; margin-top: 0.25rem;">VITA SICURA INTELLIGENCE</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Dashboard mode selector
    st.markdown("""
    <p style="font-family: 'Inter', sans-serif; font-size: 0.7rem; font-weight: 600; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 0.75rem;">
        Modalita Dashboard
    </p>
    """, unsafe_allow_html=True)

    dashboard_mode = st.radio(
        "Seleziona modalita",
        ["Helios View", "Helios NBO"],
        index=0 if st.session_state.dashboard_mode == 'Helios View' else 1,
        label_visibility="collapsed",
        horizontal=True
    )
    st.session_state.dashboard_mode = dashboard_mode

    st.markdown("---")

    # Load data (always needed)
    df = load_data()

    # Conditional sidebar content based on mode
    if st.session_state.dashboard_mode == 'Helios View':
        # Filter section title
        st.markdown("""
        <p style="font-family: 'Inter', sans-serif; font-size: 0.7rem; font-weight: 600; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 0.75rem;">
            Filtri Analisi
        </p>
        """, unsafe_allow_html=True)

        # City filter
        cities_list = ['Tutte le città'] + sorted(df['citta'].unique().tolist())
        selected_city = st.selectbox("Città", cities_list, label_visibility="collapsed")
        st.caption("📍 Filtra per città")

        # Risk category filter
        risk_options = ['Tutti i rischi', 'Critico', 'Alto', 'Medio', 'Basso']
        selected_risk = st.selectbox("Categoria Rischio", risk_options, label_visibility="collapsed")
        st.caption("⚠️ Filtra per livello di rischio")

        # Seismic zone filter
        zone_options = ['Tutte le zone', 'Zona 1', 'Zona 2', 'Zona 3', 'Zona 4']
        selected_zone = st.selectbox("Zona Sismica", zone_options, label_visibility="collapsed")
        st.caption("🌍 Filtra per zona sismica")

        st.markdown("---")

        # Apply filters
        filtered_df = df.copy()
        if selected_city != 'Tutte le città':
            filtered_df = filtered_df[filtered_df['citta'] == selected_city]
        if selected_risk != 'Tutti i rischi':
            filtered_df = filtered_df[filtered_df['risk_category'] == selected_risk]
        if selected_zone != 'Tutte le zone':
            zone_num = int(selected_zone.split()[-1])
            filtered_df = filtered_df[filtered_df['zona_sismica'] == zone_num]

        # Quick stats card
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, rgba(0, 160, 176, 0.08) 0%, rgba(0, 201, 212, 0.05) 100%); border: 1px solid rgba(0, 160, 176, 0.15); border-radius: 16px; padding: 1.25rem; margin: 0.5rem 0;">
            <p style="font-family: 'Inter', sans-serif; font-size: 0.65rem; font-weight: 600; color: #64748B; text-transform: uppercase; letter-spacing: 0.05em; margin: 0;">Abitazioni Filtrate</p>
            <p style="font-family: 'JetBrains Mono', monospace; font-size: 2.25rem; font-weight: 700; background: linear-gradient(135deg, #00A0B0 0%, #00C9D4 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 0.25rem 0; line-height: 1.1;">{len(filtered_df):,}</p>
            <p style="font-family: 'Inter', sans-serif; font-size: 0.75rem; color: #94A3B8; margin: 0;">di {len(df):,} totali ({round(len(filtered_df)/len(df)*100) if len(df) > 0 else 0}%)</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        # Connections status
        st.markdown("""
        <p style="font-family: 'Inter', sans-serif; font-size: 0.7rem; font-weight: 600; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 0.75rem;">
            Connessioni
        </p>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem;">
            <div style="display: flex; align-items: center; gap: 0.5rem; padding: 0.5rem; background: rgba(16, 185, 129, 0.08); border-radius: 8px;">
                <span style="width: 6px; height: 6px; background: #10B981; border-radius: 50%;"></span>
                <span style="font-family: 'Inter', sans-serif; font-size: 0.7rem; color: #1B3A5F; font-weight: 500;">Supabase</span>
            </div>
            <div style="display: flex; align-items: center; gap: 0.5rem; padding: 0.5rem; background: rgba(16, 185, 129, 0.08); border-radius: 8px;">
                <span style="width: 6px; height: 6px; background: #10B981; border-radius: 50%;"></span>
                <span style="font-family: 'Inter', sans-serif; font-size: 0.7rem; color: #1B3A5F; font-weight: 500;">INGV</span>
            </div>
            <div style="display: flex; align-items: center; gap: 0.5rem; padding: 0.5rem; background: rgba(16, 185, 129, 0.08); border-radius: 8px;">
                <span style="width: 6px; height: 6px; background: #10B981; border-radius: 50%;"></span>
                <span style="font-family: 'Inter', sans-serif; font-size: 0.7rem; color: #1B3A5F; font-weight: 500;">n8n</span>
            </div>
            <div style="display: flex; align-items: center; gap: 0.5rem; padding: 0.5rem; background: rgba(16, 185, 129, 0.08); border-radius: 8px;">
                <span style="width: 6px; height: 6px; background: #10B981; border-radius: 50%;"></span>
                <span style="font-family: 'Inter', sans-serif; font-size: 0.7rem; color: #1B3A5F; font-weight: 500;">ISPRA</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

    else:
        # NBO Mode sidebar
        st.markdown("""
        <p style="font-family: 'Inter', sans-serif; font-size: 0.7rem; font-weight: 600; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 0.75rem;">
            Pesi Componenti NBO
        </p>
        """, unsafe_allow_html=True)

        st.markdown("""
        <p style="font-family: 'Inter', sans-serif; font-size: 0.75rem; color: #64748B; margin-bottom: 1rem;">
            Regola i pesi per calcolare lo score delle raccomandazioni
        </p>
        """, unsafe_allow_html=True)

        retention_weight = st.slider(
            "Retention Gain",
            min_value=0.0,
            max_value=1.0,
            value=st.session_state.nbo_weights['retention'],
            step=0.01,
            help="Peso per la componente Retention Gain"
        )

        redditivita_weight = st.slider(
            "Redditivita",
            min_value=0.0,
            max_value=1.0,
            value=st.session_state.nbo_weights['redditivita'],
            step=0.01,
            help="Peso per la componente Redditivita"
        )

        propensione_weight = st.slider(
            "Propensione",
            min_value=0.0,
            max_value=1.0,
            value=st.session_state.nbo_weights['propensione'],
            step=0.01,
            help="Peso per la componente Propensione"
        )

        # Update weights
        st.session_state.nbo_weights = {
            'retention': retention_weight,
            'redditivita': redditivita_weight,
            'propensione': propensione_weight
        }

        # Show total weight
        total_weight = retention_weight + redditivita_weight + propensione_weight
        weight_color = "#10B981" if abs(total_weight - 1.0) < 0.01 else "#DC2626"

        st.markdown(f"""
        <div style="background: linear-gradient(135deg, rgba(0, 160, 176, 0.08) 0%, rgba(0, 201, 212, 0.05) 100%); border: 1px solid rgba(0, 160, 176, 0.15); border-radius: 16px; padding: 1.25rem; margin: 0.5rem 0;">
            <p style="font-family: 'Inter', sans-serif; font-size: 0.65rem; font-weight: 600; color: #64748B; text-transform: uppercase; letter-spacing: 0.05em; margin: 0;">Somma Pesi</p>
            <p style="font-family: 'JetBrains Mono', monospace; font-size: 2rem; font-weight: 700; color: {weight_color}; margin: 0.25rem 0; line-height: 1.1;">{total_weight:.2f}</p>
            <p style="font-family: 'Inter', sans-serif; font-size: 0.7rem; color: #94A3B8; margin: 0;">{"Ottimo" if abs(total_weight - 1.0) < 0.01 else "Somma consigliata: 1.00"}</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        # Load NBO data and show stats
        nbo_data = load_nbo_data()
        if nbo_data:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, rgba(0, 160, 176, 0.08) 0%, rgba(0, 201, 212, 0.05) 100%); border: 1px solid rgba(0, 160, 176, 0.15); border-radius: 16px; padding: 1.25rem; margin: 0.5rem 0;">
                <p style="font-family: 'Inter', sans-serif; font-size: 0.65rem; font-weight: 600; color: #64748B; text-transform: uppercase; letter-spacing: 0.05em; margin: 0;">Clienti NBO</p>
                <p style="font-family: 'JetBrains Mono', monospace; font-size: 2.25rem; font-weight: 700; background: linear-gradient(135deg, #00A0B0 0%, #00C9D4 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 0.25rem 0; line-height: 1.1;">{len(nbo_data):,}</p>
                <p style="font-family: 'Inter', sans-serif; font-size: 0.75rem; color: #94A3B8; margin: 0;">clienti con raccomandazioni</p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        # Set default for filtered_df to avoid NameError
        filtered_df = df

    # Footer
    st.markdown("""
    <div style="text-align: center; padding: 0.5rem 0;">
        <p style="font-family: 'Inter', sans-serif; font-size: 0.65rem; color: #94A3B8; margin: 0;">
            Powered by <strong style="color: #1B3A5F;">Vita Sicura</strong>
        </p>
        <p style="font-family: 'Inter', sans-serif; font-size: 0.6rem; color: #CBD5E1; margin-top: 0.25rem;">
            Helios v2.0 • Generali AI Challenge
        </p>
    </div>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN CONTENT
# ═══════════════════════════════════════════════════════════════════════════════

# Hero Header with Vita Sicura Logo + Helios Brand
st.markdown("""
<style>
    .header-container {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 1rem 0 1.5rem;
        margin-bottom: 1rem;
    }

    .logo-section {
        display: flex;
        align-items: center;
        gap: 1.5rem;
    }

    .vita-sicura-logo {
        height: 60px;
        width: auto;
    }

    .logo-divider {
        width: 1px;
        height: 45px;
        background: linear-gradient(180deg, transparent 0%, #E2E8F0 50%, transparent 100%);
    }

    .helios-brand {
        display: flex;
        flex-direction: column;
        gap: 0.15rem;
    }

    .helios-title {
        font-family: 'Inter', sans-serif;
        font-size: 1.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, #00A0B0 0%, #00C9D4 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        letter-spacing: -0.025em;
        line-height: 1.1;
    }

    .helios-subtitle {
        font-family: 'Inter', sans-serif;
        font-size: 0.65rem;
        font-weight: 500;
        color: #64748B;
        letter-spacing: 0.1em;
        text-transform: uppercase;
    }

    .header-status {
        display: flex;
        align-items: center;
        gap: 1rem;
    }

    .status-badge {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem 1rem;
        background: rgba(16, 185, 129, 0.1);
        border: 1px solid rgba(16, 185, 129, 0.2);
        border-radius: 100px;
        font-family: 'Inter', sans-serif;
        font-size: 0.75rem;
        font-weight: 500;
        color: #10B981;
    }

    .status-dot {
        width: 8px;
        height: 8px;
        background: #10B981;
        border-radius: 50%;
        animation: pulse-dot 2s ease-in-out infinite;
    }

    @keyframes pulse-dot {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.7; transform: scale(0.9); }
    }

    .page-title-section {
        text-align: center;
        padding: 0.5rem 0 1rem;
    }

    .page-title {
        font-family: 'Playfair Display', serif;
        font-size: 2rem;
        font-weight: 700;
        color: #1B3A5F;
        margin: 0;
        letter-spacing: -0.02em;
    }

    .page-description {
        font-family: 'Inter', sans-serif;
        font-size: 0.85rem;
        color: #64748B;
        margin-top: 0.25rem;
        font-weight: 400;
    }
</style>
""", unsafe_allow_html=True)

# Dynamic header content based on mode
page_title = "Dashboard Geo-Rischio" if st.session_state.dashboard_mode == 'Helios View' else "NBO Dashboard - Raccomandazioni Prodotti"
page_description = "Monitoraggio in tempo reale del portafoglio assicurativo territoriale" if st.session_state.dashboard_mode == 'Helios View' else "Sistema intelligente di Next Best Offer per cross-selling e up-selling"

# Header with logo
header_col1, header_col2, header_col3 = st.columns([2, 6, 2])

with header_col1:
    try:
        st.image("Logo/Gemini_Generated_Image_t6htt1t6htt1t6ht.png", width=80)
    except Exception:
        st.markdown("🌞", unsafe_allow_html=True)

with header_col2:
    st.markdown(f"""
    <div style="text-align: center;">
        <div style="display: flex; align-items: center; justify-content: center; gap: 1rem;">
            <span style="font-family: 'Inter', sans-serif; font-size: 1.5rem; font-weight: 800; background: linear-gradient(135deg, #00A0B0 0%, #00C9D4 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">HELIOS</span>
            <span style="font-family: 'Inter', sans-serif; font-size: 0.65rem; font-weight: 500; color: #64748B; letter-spacing: 0.1em; text-transform: uppercase;">Geo-Cognitive Intelligence</span>
        </div>
        <h1 style="font-family: 'Playfair Display', serif; font-size: 2rem; font-weight: 700; color: #1B3A5F; margin: 0.5rem 0 0; letter-spacing: -0.02em;">{page_title}</h1>
        <p style="font-family: 'Inter', sans-serif; font-size: 0.85rem; color: #64748B; margin-top: 0.25rem; font-weight: 400;">{page_description}</p>
    </div>
    """, unsafe_allow_html=True)

with header_col3:
    st.markdown("""
    <div style="display: flex; justify-content: flex-end; align-items: center; height: 100%;">
        <div style="display: flex; align-items: center; gap: 0.5rem; padding: 0.5rem 1rem; background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.2); border-radius: 100px; font-family: 'Inter', sans-serif; font-size: 0.75rem; font-weight: 500; color: #10B981;">
            <span style="width: 8px; height: 8px; background: #10B981; border-radius: 50%;"></span>
            Sistema Attivo
        </div>
    </div>
    """, unsafe_allow_html=True)

# Divider
st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# CONDITIONAL CONTENT BASED ON DASHBOARD MODE
# ═══════════════════════════════════════════════════════════════════════════════

if st.session_state.dashboard_mode == 'Helios View':
    # ═══════════════════════════════════════════════════════════════════════════════
    # HELIOS VIEW CONTENT
    # ═══════════════════════════════════════════════════════════════════════════════

    # Warning if no results match filters
    if len(filtered_df) == 0:
        st.warning("⚠️ Nessuna abitazione corrisponde ai filtri selezionati. Prova a modificare i criteri nella sidebar.")

    # Get stats
    stats = get_risk_stats(filtered_df)
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # KPI METRICS ROW
    # ═══════════════════════════════════════════════════════════════════════════════
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            label="🏠 Abitazioni Valutate",
            value=f"{stats['total']:,}",
            delta=f"{round(stats['total']/len(df)*100)}% copertura"
        )
    
    with col2:
        st.metric(
            label="⚡ Risk Score Medio",
            value=f"{stats['avg_score']}",
            delta=f"su scala 0-100"
        )
    
    with col3:
        st.metric(
            label="🔴 Alto Rischio",
            value=f"{stats['critico'] + stats['alto']:,}",
            delta=f"{stats['high_risk_pct']}% del totale",
            delta_color="inverse"
        )
    
    with col4:
        solar_coverage = filtered_df['solar_potential_kwh'].notna().sum()
        # Protect against division by zero when filtered_df is empty
        if len(filtered_df) > 0:
            coverage_pct = round(solar_coverage / len(filtered_df) * 100)
        else:
            coverage_pct = 0
    
        st.metric(
            label="☀️ Potenziale Solare",
            value=f"{solar_coverage:,}",
            delta=f"{coverage_pct}% analizzati"
        )
    
    with col5:
        # Protect against NaN when filtered_df is empty
        if len(filtered_df) > 0:
            avg_clv = filtered_df['clv'].mean()
            # Handle NaN case (if all CLV values are missing)
            if pd.isna(avg_clv):
                avg_clv = 0
        else:
            avg_clv = 0
    
        st.metric(
            label="💎 CLV Medio",
            value=f"€{avg_clv:,.0f}",
            delta="lifetime value"
        )
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # MAIN TABS
    # ═══════════════════════════════════════════════════════════════════════════════
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "🗺️ Mappa Geo-Rischio", 
        "📊 Analytics", 
        "🔍 Dettaglio Clienti",
        "🤖 A.D.A. Chat"
    ])
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # TAB 1: GEO-RISK MAP
    # ═══════════════════════════════════════════════════════════════════════════════
    
    with tab1:
        st.markdown("### 🌍 Mappa del Rischio Territoriale")
        st.markdown(
            "<p style='color: #64748B; font-size: 0.9rem;'>"
            "Visualizzazione geospaziale del portafoglio con indicatori di rischio sismico e idrogeologico. "
            "Ogni punto rappresenta un'abitazione assicurata."
            "</p>",
            unsafe_allow_html=True
        )
        
        # Prepare map data - FILTER OUT records without valid coordinates
        map_df = filtered_df[
            filtered_df['latitudine'].notna() & 
            filtered_df['longitudine'].notna()
        ].copy()
        
        # Show count
        if len(map_df) == 0:
            st.warning("⚠️ Nessuna abitazione con coordinate geografiche disponibile. Il geocoding potrebbe essere ancora in corso.")
        else:
            st.caption(f"📍 Visualizzando {len(map_df)} abitazioni con coordinate su {len(filtered_df)} totali")
            
            # Prepare data for st.map (needs 'lat' and 'lon' columns)
            map_display = map_df.rename(columns={
                'latitudine': 'lat',
                'longitudine': 'lon'
            })[['lat', 'lon']]
            
            # Display the map
            st.map(map_display, width="stretch")
            
            # Show data table for selection
            st.markdown("### 📋 Dettaglio Abitazioni")
            
            # Display table with key columns
            display_cols = ['id', 'citta', 'risk_score', 'risk_category', 'zona_sismica', 'codice_cliente']
            display_df = map_df[[c for c in display_cols if c in map_df.columns]].copy()
            display_df['risk_score'] = display_df['risk_score'].fillna(0).round(1)
            
            st.dataframe(
                display_df,
                width="stretch",
                height=300,
                column_config={
                    'id': st.column_config.TextColumn('ID'),
                    'citta': st.column_config.TextColumn('Città'),
                    'risk_score': st.column_config.ProgressColumn('Risk Score', min_value=0, max_value=100, format="%.1f"),
                    'risk_category': st.column_config.TextColumn('Categoria'),
                    'zona_sismica': st.column_config.NumberColumn('Zona Sism.'),
                    'codice_cliente': st.column_config.TextColumn('Cliente'),
                }
            )
        
        # Legend
        st.markdown("""
        <div style="display: flex; gap: 2rem; justify-content: center; margin-top: 1rem; flex-wrap: wrap;">
            <span class="risk-badge risk-critical">🔴 Critico (≥80)</span>
            <span class="risk-badge risk-high">🟠 Alto (60-79)</span>
            <span class="risk-badge risk-medium">🟡 Medio (40-59)</span>
            <span class="risk-badge risk-low">🟢 Basso (<40)</span>
        </div>
        """, unsafe_allow_html=True)
    
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # TAB 2: ANALYTICS
    # ═══════════════════════════════════════════════════════════════════════════════
    
    with tab2:
        st.markdown("### 📈 Analytics Dashboard")
    
        analytics_col1, analytics_col2 = st.columns(2)
    
        with analytics_col1:
            # Risk Distribution Donut - Light Theme
            risk_counts = filtered_df['risk_category'].value_counts()
    
            fig_donut = go.Figure(data=[go.Pie(
                labels=risk_counts.index,
                values=risk_counts.values,
                hole=0.65,
                marker_colors=['#DC2626', '#EA580C', '#CA8A04', '#16A34A'],
                textinfo='percent+label',
                textfont=dict(family='Inter', size=12, color='#1B3A5F'),
                hovertemplate="<b>%{label}</b><br>%{value:,} abitazioni<br>%{percent}<extra></extra>"
            )])
    
            fig_donut.update_layout(
                title=dict(
                    text="Distribuzione Rischio",
                    font=dict(family='Inter', size=18, color='#1B3A5F', weight=600),
                    x=0.5
                ),
                paper_bgcolor='rgba(255,255,255,0)',
                plot_bgcolor='rgba(255,255,255,0)',
                font=dict(color='#64748B', family='Inter'),
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=-0.2,
                    xanchor="center",
                    x=0.5,
                    font=dict(family='Inter', size=11, color='#64748B')
                ),
                annotations=[dict(
                    text=f"<b>{len(filtered_df):,}</b><br>Totale",
                    x=0.5, y=0.5,
                    font=dict(family='JetBrains Mono', size=20, color='#1B3A5F'),
                    showarrow=False
                )],
                height=400,
                margin=dict(t=60, b=60, l=20, r=20)
            )
    
            st.plotly_chart(fig_donut, width="stretch")
    
        with analytics_col2:
            # Seismic Zone Bar Chart - Light Theme
            zone_counts = filtered_df['zona_sismica'].value_counts().sort_index()
    
            fig_bar = go.Figure(data=[go.Bar(
                x=[f"Zona {z}" for z in zone_counts.index],
                y=zone_counts.values,
                marker=dict(
                    color=['#DC2626', '#EA580C', '#CA8A04', '#16A34A'][:len(zone_counts)],
                    line=dict(color='rgba(255,255,255,0.8)', width=1)
                ),
                text=zone_counts.values,
                textposition='outside',
                textfont=dict(family='JetBrains Mono', size=12, color='#1B3A5F'),
                hovertemplate="<b>%{x}</b><br>%{y:,} abitazioni<extra></extra>"
            )])
    
            fig_bar.update_layout(
                title=dict(
                    text="Distribuzione Zone Sismiche",
                    font=dict(family='Inter', size=18, color='#1B3A5F', weight=600),
                    x=0.5
                ),
                paper_bgcolor='rgba(255,255,255,0)',
                plot_bgcolor='rgba(255,255,255,0)',
                font=dict(color='#64748B', family='Inter'),
                xaxis=dict(
                    showgrid=False,
                    tickfont=dict(family='Inter', size=12, color='#64748B'),
                    linecolor='#E2E8F0'
                ),
                yaxis=dict(
                    showgrid=True,
                    gridcolor='rgba(226, 232, 240, 0.5)',
                    tickfont=dict(family='JetBrains Mono', size=11, color='#64748B'),
                    linecolor='#E2E8F0'
                ),
                height=400,
                margin=dict(t=60, b=40, l=40, r=40)
            )
    
            st.plotly_chart(fig_bar, width="stretch")
        
        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
        
        # Second row of charts
        analytics_col3, analytics_col4 = st.columns(2)
    
        with analytics_col3:
            # CLV vs Risk Score Scatter - Light Theme
            fig_scatter = px.scatter(
                filtered_df,
                x='risk_score',
                y='clv',
                color='risk_category',
                color_discrete_map={
                    'Critico': '#DC2626',
                    'Alto': '#EA580C',
                    'Medio': '#CA8A04',
                    'Basso': '#16A34A'
                },
                size='churn_probability',
                hover_data=['citta', 'zona_sismica'],
                labels={
                    'risk_score': 'Risk Score',
                    'clv': 'Customer Lifetime Value (€)',
                    'risk_category': 'Categoria'
                }
            )
    
            fig_scatter.update_layout(
                title=dict(
                    text="CLV vs Risk Score",
                    font=dict(family='Inter', size=18, color='#1B3A5F', weight=600),
                    x=0.5
                ),
                paper_bgcolor='rgba(255,255,255,0)',
                plot_bgcolor='rgba(255,255,255,0)',
                font=dict(color='#64748B', family='Inter'),
                xaxis=dict(
                    showgrid=True,
                    gridcolor='rgba(226, 232, 240, 0.5)',
                    title_font=dict(size=12, color='#64748B'),
                    linecolor='#E2E8F0',
                    tickfont=dict(color='#64748B')
                ),
                yaxis=dict(
                    showgrid=True,
                    gridcolor='rgba(226, 232, 240, 0.5)',
                    title_font=dict(size=12, color='#64748B'),
                    linecolor='#E2E8F0',
                    tickfont=dict(color='#64748B')
                ),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=-0.3,
                    xanchor="center",
                    x=0.5,
                    font=dict(color='#64748B')
                ),
                height=400,
                margin=dict(t=60, b=80, l=60, r=40)
            )
    
            st.plotly_chart(fig_scatter, width="stretch")
    
        with analytics_col4:
            # Churn Probability Distribution - Light Theme
            churn_bins = pd.cut(filtered_df['churn_probability'], bins=[0, 0.2, 0.4, 0.6, 0.8, 1.0],
                               labels=['Molto Basso', 'Basso', 'Medio', 'Alto', 'Molto Alto'])
            churn_counts = churn_bins.value_counts().sort_index()
    
            fig_churn = go.Figure(data=[go.Bar(
                y=churn_counts.index.astype(str),
                x=churn_counts.values,
                orientation='h',
                marker=dict(
                    color=['#16A34A', '#00A0B0', '#CA8A04', '#EA580C', '#DC2626'][:len(churn_counts)],
                    line=dict(color='rgba(255,255,255,0.8)', width=1)
                ),
                text=churn_counts.values,
                textposition='outside',
                textfont=dict(family='JetBrains Mono', size=11, color='#1B3A5F'),
                hovertemplate="<b>%{y}</b><br>%{x:,} clienti<extra></extra>"
            )])
    
            fig_churn.update_layout(
                title=dict(
                    text="Distribuzione Churn Probability",
                    font=dict(family='Inter', size=18, color='#1B3A5F', weight=600),
                    x=0.5
                ),
                paper_bgcolor='rgba(255,255,255,0)',
                plot_bgcolor='rgba(255,255,255,0)',
                font=dict(color='#64748B', family='Inter'),
                xaxis=dict(
                    showgrid=True,
                    gridcolor='rgba(226, 232, 240, 0.5)',
                    tickfont=dict(family='JetBrains Mono', size=11, color='#64748B'),
                    linecolor='#E2E8F0'
                ),
                yaxis=dict(
                    showgrid=False,
                    tickfont=dict(family='Inter', size=12, color='#64748B')
                ),
                height=400,
                margin=dict(t=60, b=40, l=120, r=60)
            )
    
            st.plotly_chart(fig_churn, width="stretch")
        
        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
        
        # City breakdown - Light Theme
        st.markdown("### 🏙️ Top 10 Città per Concentrazione Rischio")
    
        city_risk = filtered_df.groupby('citta').agg({
            'risk_score': 'mean',
            'id': 'count',
            'clv': 'sum'
        }).rename(columns={'id': 'n_abitazioni', 'clv': 'clv_totale'}).reset_index()
        city_risk = city_risk.sort_values('risk_score', ascending=False).head(10)
    
        fig_city = go.Figure(data=[go.Bar(
            x=city_risk['citta'],
            y=city_risk['risk_score'],
            marker=dict(
                color=city_risk['risk_score'],
                colorscale=[[0, '#16A34A'], [0.5, '#CA8A04'], [1, '#DC2626']],
                line=dict(color='rgba(255,255,255,0.8)', width=1)
            ),
            text=[f"{x:.0f}" for x in city_risk['risk_score']],
            textposition='outside',
            textfont=dict(family='JetBrains Mono', size=11, color='#1B3A5F'),
            hovertemplate="<b>%{x}</b><br>Risk Score: %{y:.1f}<br>Abitazioni: %{customdata[0]:,}<br>CLV Totale: €%{customdata[1]:,.0f}<extra></extra>",
            customdata=city_risk[['n_abitazioni', 'clv_totale']].values
        )])
    
        fig_city.update_layout(
            paper_bgcolor='rgba(255,255,255,0)',
            plot_bgcolor='rgba(255,255,255,0)',
            font=dict(color='#64748B', family='Inter'),
            xaxis=dict(
                showgrid=False,
                tickfont=dict(size=11, color='#64748B'),
                tickangle=-45,
                linecolor='#E2E8F0'
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor='rgba(226, 232, 240, 0.5)',
                title="Risk Score Medio",
                title_font=dict(size=12, color='#64748B'),
                range=[0, 100],
                linecolor='#E2E8F0',
                tickfont=dict(color='#64748B')
            ),
            height=350,
            margin=dict(t=20, b=80, l=60, r=40)
        )
    
        st.plotly_chart(fig_city, width="stretch")
    
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # TAB 3: CLIENT DETAIL
    # ═══════════════════════════════════════════════════════════════════════════════
    
    with tab3:
        st.markdown("### 🔍 Ricerca Clienti")
        
        search_col1, search_col2 = st.columns([3, 1])
        
        with search_col1:
            search_term = st.text_input(
                "🔎 Cerca per ID, città o codice cliente",
                placeholder="Es: HAB00001, Milano, CLI1234..."
            )
        
        with search_col2:
            sort_by = st.selectbox(
                "Ordina per",
                ["Risk Score ↓", "Risk Score ↑", "CLV ↓", "CLV ↑", "Churn ↓"]
            )
        
        # Filter and sort
        display_df = filtered_df.copy()
        
        if search_term:
            mask = (
                display_df['id'].str.contains(search_term, case=False, na=False) |
                display_df['citta'].str.contains(search_term, case=False, na=False) |
                display_df['codice_cliente'].str.contains(search_term, case=False, na=False)
            )
            display_df = display_df[mask]
        
        # Sort
        sort_mapping = {
            "Risk Score ↓": ('risk_score', False),
            "Risk Score ↑": ('risk_score', True),
            "CLV ↓": ('clv', False),
            "CLV ↑": ('clv', True),
            "Churn ↓": ('churn_probability', False)
        }
        sort_col, ascending = sort_mapping[sort_by]
        display_df = display_df.sort_values(sort_col, ascending=ascending)
        
        st.markdown(f"**{len(display_df):,}** risultati trovati")
        
        # Display as cards - Light Theme
        for idx, row in display_df.head(20).iterrows():
            risk_class = row['risk_category'].lower()
            solar_info = f"☀️ {row['solar_potential_kwh']:,} kWh/anno" if pd.notna(row['solar_potential_kwh']) else "☀️ Non calcolato"
    
            st.markdown(f"""
            <div class="glass-card" style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem;">
                <div style="flex: 1; min-width: 200px;">
                    <h4 style="margin: 0; color: #1B3A5F; font-size: 1.1rem; font-weight: 600;">{row['id']}</h4>
                    <p style="margin: 0.25rem 0; color: #64748B; font-size: 0.85rem;">
                        📍 {row['citta']} · {row['codice_cliente']}
                    </p>
                </div>
                <div style="display: flex; gap: 1.5rem; flex-wrap: wrap; align-items: center;">
                    <div style="text-align: center;">
                        <p style="margin: 0; color: #94A3B8; font-size: 0.65rem; text-transform: uppercase; letter-spacing: 0.05em; font-weight: 600;">Risk Score</p>
                        <p style="margin: 0; color: #1B3A5F; font-size: 1.5rem; font-weight: 700; font-family: 'JetBrains Mono', monospace;">{row['risk_score']}</p>
                    </div>
                    <div style="text-align: center;">
                        <p style="margin: 0; color: #94A3B8; font-size: 0.65rem; text-transform: uppercase; letter-spacing: 0.05em; font-weight: 600;">Zona</p>
                        <p style="margin: 0; color: #1B3A5F; font-size: 1.5rem; font-weight: 700; font-family: 'JetBrains Mono', monospace;">{row['zona_sismica']}</p>
                    </div>
                    <div style="text-align: center;">
                        <p style="margin: 0; color: #94A3B8; font-size: 0.65rem; text-transform: uppercase; letter-spacing: 0.05em; font-weight: 600;">CLV</p>
                        <p style="margin: 0; color: #00A0B0; font-size: 1.5rem; font-weight: 700; font-family: 'JetBrains Mono', monospace;">€{row['clv']:,}</p>
                    </div>
                    <span class="risk-badge risk-{risk_class}">{row['risk_category']}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        if len(display_df) > 20:
            st.info(f"📄 Mostrati i primi 20 risultati di {len(display_df):,}. Usa i filtri per restringere la ricerca.")
    
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # TAB 4: A.D.A. CHAT
    # ═══════════════════════════════════════════════════════════════════════════════
    
    with tab4:
        render_ada_chat()

else:
    # ═══════════════════════════════════════════════════════════════════════════════
    # NBO DASHBOARD CONTENT
    # ═══════════════════════════════════════════════════════════════════════════════

    # Load NBO data
    nbo_data = load_nbo_data()

    if not nbo_data:
        st.error("Impossibile caricare i dati NBO. Verifica che il file Data/nbo_master.json esista.")
    else:
        # Check if we're in Top 5 view
        if st.session_state.nbo_page == 'top5':
            # ═══════════════════════════════════════════════════════════════════════════════
            # TOP 5 AZIONI PRIORITARIE VIEW
            # ═══════════════════════════════════════════════════════════════════════════════

            # Back button
            if st.button("← Torna al Top 20", type="secondary"):
                st.session_state.nbo_page = 'dashboard'
                st.rerun()

            st.markdown("# 🎯 Top 5 Azioni Prioritarie")
            st.markdown("""
            <div style="background: #FEF3C7; border-left: 4px solid #F59E0B; padding: 1rem; margin-bottom: 1.5rem; border-radius: 4px;">
                <p style="margin: 0; color: #92400E; font-size: 0.95rem; line-height: 1.6;">
                    <strong>📞 Azione Immediata Richiesta</strong><br>
                    Questi sono i clienti con il punteggio più alto per i quali è consigliato effettuare una chiamata
                    o aumentare la pressione commerciale. Contatta questi clienti prioritariamente.
                </p>
            </div>
            """, unsafe_allow_html=True)

            # Get top 5 from all_recs
            all_recs = get_all_recommendations(nbo_data, st.session_state.nbo_weights)
            top5_recs = all_recs[:5]

            # Display Top 5 clients
            for i, rec in enumerate(top5_recs):
                score_color = "#10B981" if rec['score'] >= 70 else "#F59E0B" if rec['score'] >= 50 else "#EF4444"

                col_card, col_btn = st.columns([5, 1])

                with col_card:
                    st.markdown(f"""
                    <div class="glass-card" style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem; border-left: 4px solid {score_color};">
                        <div style="flex: 1; min-width: 200px;">
                            <div style="display: flex; align-items: center; gap: 0.75rem;">
                                <span style="background: linear-gradient(135deg, #F59E0B 0%, #FBBF24 100%); color: white; padding: 0.35rem 0.85rem; border-radius: 100px; font-size: 0.85rem; font-weight: 700;">TOP #{i+1}</span>
                                <h4 style="margin: 0; color: #1B3A5F; font-size: 1.1rem; font-weight: 700;">{rec['nome']} {rec['cognome']}</h4>
                            </div>
                            <p style="margin: 0.25rem 0 0 3rem; color: #64748B; font-size: 0.85rem;">
                                {rec['codice_cliente']} · {rec['prodotto']}
                            </p>
                        </div>
                        <div style="display: flex; gap: 1.5rem; align-items: center;">
                            <div style="text-align: center;">
                                <p style="margin: 0; color: #94A3B8; font-size: 0.6rem; text-transform: uppercase; letter-spacing: 0.05em;">Area</p>
                                <p style="margin: 0; color: #1B3A5F; font-size: 0.9rem; font-weight: 600;">{rec['area_bisogno'].split()[0]}</p>
                            </div>
                            <div style="text-align: center;">
                                <p style="margin: 0; color: #94A3B8; font-size: 0.6rem; text-transform: uppercase; letter-spacing: 0.05em;">Score</p>
                                <p style="margin: 0; color: {score_color}; font-size: 1.5rem; font-weight: 700; font-family: 'JetBrains Mono', monospace;">{rec['score']:.1f}</p>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                with col_btn:
                    if st.button("Dettagli", key=f"top5_detail_{i}", width="stretch"):
                        st.session_state.nbo_page = 'detail'
                        st.session_state.nbo_selected_client = rec['client_data']
                        st.session_state.nbo_selected_recommendation = rec['recommendation']
                        st.rerun()

            # ADA Section at the end of Top 5
            st.markdown("<br><br>", unsafe_allow_html=True)
            st.markdown("## 🤖 ADA – Sintesi e Azioni")
            st.markdown("""
            <div class="glass-card" style="border-left: 4px solid #00A0B0;">
                <p style="color: #64748B; font-size: 0.95rem; line-height: 1.6; margin-bottom: 1rem;">
                    ADA può aiutarti ad analizzare questi clienti prioritari e preparare comunicazioni personalizzate.
                </p>
            </div>
            """, unsafe_allow_html=True)

            # Prepare context for ADA about Top 5 clients
            top5_context = "I Top 5 clienti prioritari sono:\n\n"
            for i, rec in enumerate(top5_recs):
                top5_context += f"{i+1}. {rec['nome']} {rec['cognome']} ({rec['codice_cliente']}) - Score: {rec['score']:.1f} - Prodotto raccomandato: {rec['prodotto']}\n"

            # Button for mass email action
            if st.button("📧 Prepara Email Personalizzate", type="primary", width="stretch", key="mass_email_top5"):
                st.session_state.ada_auto_prompt = f"""Analizza questi {len(top5_recs)} clienti prioritari e crea una strategia di contatto:

{top5_context}

Per ciascun cliente, suggerisci:
1. Il miglior approccio di contatto
2. I punti chiave da evidenziare nella comunicazione
3. Una bozza di email personalizzata che tenga conto del prodotto raccomandato e dello score

Le email devono essere personalizzate per ogni cliente, non identiche."""
                st.rerun()

        # Check if we're in detail view
        elif st.session_state.nbo_page == 'detail' and st.session_state.nbo_selected_client:
            # ═══════════════════════════════════════════════════════════════════════════════
            # NBO CLIENT DETAIL VIEW
            # ═══════════════════════════════════════════════════════════════════════════════

            client_data = st.session_state.nbo_selected_client
            recommendation = st.session_state.nbo_selected_recommendation

            # Back button and action button
            col_back, col_action = st.columns([1, 1])
            with col_back:
                if st.button("← Torna alla Dashboard", type="secondary", width="stretch"):
                    st.session_state.nbo_page = 'dashboard'
                    st.session_state.nbo_selected_client = None
                    st.session_state.nbo_selected_recommendation = None
                    st.rerun()

            with col_action:
                # Create a button instead of expander to avoid label issues
                if st.button("📞 Ho chiamato il cliente", type="primary", width="stretch", key="open_call_form"):
                    st.session_state.show_call_form = True

                # Show form in a modal-like container if button was clicked
                if st.session_state.get('show_call_form', False):
                    st.markdown("---")
                    st.markdown("##### 📞 Dettagli della chiamata")

                    # Get top recommendation for this client
                    top_recommendation = None
                    if client_data.get('raccomandazioni'):
                        # Calculate scores and get the top one
                        recs_with_scores = []
                        for rec in client_data['raccomandazioni']:
                            score = calculate_recommendation_score(rec, st.session_state.nbo_weights)
                            recs_with_scores.append((score, rec))
                        recs_with_scores.sort(key=lambda x: x[0], reverse=True)
                        top_recommendation = recs_with_scores[0][1] if recs_with_scores else None

                    # Define available products
                    available_products = [
                        "Assicurazione Casa e Famiglia: Casa Serena",              
                        "Piano Individuale Pensionistico (PIP): Pensione Serenità",
                        "Polizza Salute e Infortuni: Salute Protetta",             
                        "Polizza Vita a Premi Ricorrenti: Risparmio Costante",     
                        "Polizza Vita a Premio Unico: Futuro Sicuro"
                    ]

                    # Polizza proposta (obbligatorio) - Sì/No/Altre
                    polizza_scelta = st.radio(
                        "Polizza proposta *",
                        options=["Sì", "No", "Altre"],
                        help="Sì = raccomandata con score maggiore, Altre = scegli tra le opzioni disponibili",
                        horizontal=True
                    )

                    # If "Sì", use top recommendation; if "Altre", show dropdown
                    polizza_proposta = None
                    if polizza_scelta == "Sì" and top_recommendation:
                        polizza_proposta = top_recommendation['prodotto']
                        st.info(f"💡 Polizza raccomandata: **{polizza_proposta}**")
                    elif polizza_scelta == "Altre":
                        polizza_proposta = st.selectbox(
                            "Seleziona polizza",
                            options=available_products,
                            help="Scegli una polizza tra quelle disponibili"
                        )
                    elif polizza_scelta == "No":
                        polizza_proposta = "Nessuna proposta"

                    # Esito (obbligatorio) - no empty option
                    esito = st.selectbox(
                        "Esito della chiamata *",
                        options=["Positivo", "Neutro", "Negativo"],
                        help="Campo obbligatorio"
                    )

                    # Note aggiuntive (opzionale)
                    note_aggiuntive = st.text_area(
                        "Note aggiuntive",
                        placeholder="Inserisci eventuali note sulla chiamata...",
                        help="Campo opzionale"
                    )

                    st.markdown("<br>", unsafe_allow_html=True)

                    col_cancel, col_submit = st.columns(2)
                    with col_cancel:
                        if st.button("❌ Annulla", width="stretch"):
                            st.session_state.show_call_form = False
                            st.rerun()

                    with col_submit:
                        if st.button("✅ Registra chiamata", type="primary", width="stretch"):
                            codice_cliente = client_data['codice_cliente']

                            # Costruisci le note complete
                            note_complete = f"Polizza proposta: {polizza_proposta}\nEsito: {esito}"
                            if note_aggiuntive and note_aggiuntive.strip():
                                note_complete += f"\nNote: {note_aggiuntive}"

                            success = insert_phone_call_interaction(
                                codice_cliente,
                                polizza_proposta=polizza_proposta,
                                esito=esito.lower(),
                                note=note_complete
                            )

                            if success:
                                # Update client data to reflect the call
                                client_data['_interaction_indicators']['call_last_10_days'] = True
                                client_data['_is_eligible_top20'] = False

                                # Close form and show success
                                st.session_state.show_call_form = False
                                st.session_state.show_success_message = True
                                st.rerun()
                            else:
                                st.error("❌ Errore nella registrazione della chiamata. Riprova.")

                    st.markdown("---")

                # Show success message if flag is set
                if st.session_state.get('show_success_message', False):
                    st.success("✅ Esito registrato! Il cliente non sarà più visibile nel Top 20/Top 5.")
                    st.session_state.show_success_message = False

            st.markdown("<br>", unsafe_allow_html=True)

            # Client header
            st.markdown(f"""
            <div class="glass-card" style="margin-bottom: 1.5rem;">
                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem;">
                    <div>
                        <h2 style="margin: 0; color: #1B3A5F; font-size: 1.75rem; font-weight: 700;">
                            {client_data['anagrafica']['nome']} {client_data['anagrafica']['cognome']}
                        </h2>
                        <p style="margin: 0.25rem 0; color: #64748B; font-size: 0.9rem;">
                            {client_data['codice_cliente']} · {client_data['anagrafica']['citta']}, {client_data['anagrafica']['provincia']}
                        </p>
                    </div>
                    <div style="text-align: right;">
                        <p style="margin: 0; color: #94A3B8; font-size: 0.65rem; text-transform: uppercase; letter-spacing: 0.05em;">CLV Stimato</p>
                        <p style="margin: 0; color: #00A0B0; font-size: 1.75rem; font-weight: 700; font-family: 'JetBrains Mono', monospace;">
                            €{client_data['metadata']['clv_stimato']:,}
                        </p>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Client info columns
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("### Anagrafica")
                ana = client_data['anagrafica']
                st.markdown(f"""
                <div class="glass-card">
                    <p><strong>Eta:</strong> {ana['eta']} anni</p>
                    <p><strong>Indirizzo:</strong> {ana['indirizzo']}</p>
                    <p><strong>Citta:</strong> {ana['citta']}</p>
                    <p><strong>Provincia:</strong> {ana['provincia']}</p>
                    <p><strong>Regione:</strong> {ana['regione']}</p>
                </div>
                """, unsafe_allow_html=True)

                st.markdown("### Metadata Cliente")
                meta = client_data['metadata']

                # Determine cluster response badge color
                cluster_colors = {
                    'High_Responder': '#10B981',
                    'Moderate_Responder': '#F59E0B',
                    'Low_Responder': '#EF4444'
                }
                cluster_color = cluster_colors.get(meta['cluster_risposta'], '#64748B')

                st.markdown(f"""
                <div class="glass-card">
                    <p><strong>Churn Attuale:</strong> <span style="font-family: 'JetBrains Mono', monospace;">{meta['churn_attuale']:.4f}</span></p>
                    <p><strong>Polizze Attuali:</strong> {meta['num_polizze_attuali']}</p>
                    <p><strong>Cluster NBA:</strong> {meta['cluster_nba']}</p>
                    <p><strong>Cluster Risposta:</strong> <span style="background: {cluster_color}20; color: {cluster_color}; padding: 0.25rem 0.5rem; border-radius: 4px; font-weight: 600;">{meta['cluster_risposta']}</span></p>
                    <p><strong>Satisfaction Score:</strong> {meta['satisfaction_score']:.1f}</p>
                    <p><strong>Engagement Score:</strong> {meta['engagement_score']:.1f}</p>
                </div>
                """, unsafe_allow_html=True)

                # Interazione cliente section
                st.markdown("<br>", unsafe_allow_html=True)

                # Get interaction indicators
                indicators = client_data.get('_interaction_indicators', {})
                is_eligible = client_data.get('_is_eligible_top20', True)

                # Show warning icon if client has any active interaction
                warning_icon = " ⚠️" if not is_eligible else ""

                st.markdown(f"### Interazione cliente{warning_icon}")

                if not is_eligible:
                    st.markdown("""
                    <div style="background: #FEF3C7; border-left: 4px solid #F59E0B; padding: 0.75rem; margin-bottom: 1rem; border-radius: 4px;">
                        <p style="margin: 0; color: #92400E; font-size: 0.85rem; font-weight: 500;">
                            ⚠️ Cliente non eleggibile per azioni commerciali a causa di interazioni recenti
                        </p>
                    </div>
                    """, unsafe_allow_html=True)

                # Indicators display
                def render_indicator(label, value):
                    icon = "✓" if value else "✗"
                    color = "#EF4444" if value else "#10B981"
                    bg_color = "#FEE2E2" if value else "#DCFCE7"
                    text = "Sì" if value else "No"

                    return f"""<div style="display: flex; justify-content: space-between; align-items: center; padding: 0.5rem 0; border-bottom: 1px solid #E2E8F0;">
    <span style="color: #64748B; font-size: 0.85rem;">{label}</span>
    <span style="background: {bg_color}; color: {color}; padding: 0.15rem 0.5rem; border-radius: 4px; font-size: 0.75rem; font-weight: 600;">{icon} {text}</span>
</div>"""

                indicators_html = "".join([
                    render_indicator("Email ultimi 5 giorni lav.", indicators.get('email_last_5_days', False)),
                    render_indicator("Telefonata ultimi 10 giorni", indicators.get('call_last_10_days', False)),
                    render_indicator("Nuova polizza ultimi 30 gg", indicators.get('new_policy_last_30_days', False)),
                    render_indicator("Reclamo aperto", indicators.get('open_complaint', False)),
                    render_indicator("Sinistro ultimi 60 giorni", indicators.get('claim_last_60_days', False))
                ])

                st.markdown(f"""<div class="glass-card">{indicators_html}</div>""", unsafe_allow_html=True)

            with col2:
                st.markdown("### Prodotti Posseduti")
                prodotti = meta.get('prodotti_posseduti', [])
                if prodotti:
                    if isinstance(prodotti, str):
                        prodotti = [prodotti]
                    products_html = "".join([f"<li style='margin: 0.5rem 0; color: #1B3A5F;'>{p}</li>" for p in prodotti])
                    st.markdown(f"""
                    <div class="glass-card">
                        <ul style="padding-left: 1.25rem; margin: 0;">
                            {products_html}
                        </ul>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div class="glass-card">
                        <p style="color: #94A3B8; font-style: italic;">Nessun prodotto posseduto</p>
                    </div>
                    """, unsafe_allow_html=True)

                if recommendation:
                    st.markdown("### Raccomandazione Selezionata")
                    comp = recommendation['componenti']
                    det = recommendation['dettagli']
                    st.markdown(f"""
                    <div class="glass-card" style="border-left: 4px solid #00A0B0;">
                        <p style="font-size: 1.1rem; font-weight: 600; color: #1B3A5F; margin-bottom: 0.5rem;">{recommendation['prodotto']}</p>
                        <p style="color: #64748B; margin-bottom: 1rem;">Area: {recommendation['area_bisogno']}</p>
                        <hr style="border: none; border-top: 1px solid #E2E8F0; margin: 1rem 0;">
                        <p style="color: #94A3B8; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.5rem;">Componenti Score</p>
                        <p><strong>Retention Gain:</strong> {comp['retention_gain']:.1f}%</p>
                        <p><strong>Redditivita:</strong> {comp['redditivita']:.1f}%</p>
                        <p><strong>Propensione:</strong> {comp['propensione']:.1f}%</p>
                        <p><strong>Affinita Cluster:</strong> {comp['affinita_cluster']:.1f}%</p>
                        <hr style="border: none; border-top: 1px solid #E2E8F0; margin: 1rem 0;">
                        <p style="color: #94A3B8; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.5rem;">Dettagli Churn</p>
                        <p><strong>Delta Churn:</strong> <span style="color: #10B981;">-{det['delta_churn']:.6f}</span></p>
                        <p><strong>Churn Prima:</strong> {det['churn_prima']:.6f}</p>
                        <p><strong>Churn Dopo:</strong> {det['churn_dopo']:.6f}</p>
                    </div>
                    """, unsafe_allow_html=True)

            # Map
            st.markdown("### Localizzazione Cliente")
            lat = client_data['anagrafica']['latitudine']
            lon = client_data['anagrafica']['longitudine']

            m = folium.Map(location=[lat, lon], zoom_start=13, tiles='CartoDB positron')
            folium.Marker(
                [lat, lon],
                popup=f"{client_data['anagrafica']['nome']} {client_data['anagrafica']['cognome']}<br>{client_data['anagrafica']['indirizzo']}<br>{client_data['anagrafica']['citta']}",
                tooltip=f"{client_data['anagrafica']['nome']} {client_data['anagrafica']['cognome']}",
                icon=folium.Icon(color='lightblue', icon='home', prefix='fa')
            ).add_to(m)

            folium_static(m, width=None, height=400)

            # ═══════════════════════════════════════════════════════════════════
            # Computer Vision - Satellite View Section
            # ═══════════════════════════════════════════════════════════════════
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("### 🛰️ Abitazione – Vista Satellitare")

            # For now, use simulated CV data (will be replaced with real DB fields)
            # In production, these would come from: client_data.get('has_solar_panels', False), etc.
            import hashlib
            client_hash = int(hashlib.md5(client_data['codice_cliente'].encode()).hexdigest(), 16)

            # Simulate CV detections based on client hash (for demonstration)
            has_solar_panels = (client_hash % 3) == 0  # ~33% have solar panels
            has_pool = (client_hash % 5) == 0  # ~20% have pool
            has_garden = (client_hash % 2) == 0  # ~50% have garden

            # Satellite image placeholder
            st.markdown("""
            <div class="glass-card" style="text-align: center; background: #F3F4F6; padding: 2rem;">
                <p style="color: #94A3B8; font-size: 3rem; margin: 0;">🗺️</p>
                <p style="color: #64748B; font-size: 0.85rem; margin-top: 0.5rem;">
                    Immagine satellitare dell'abitazione<br>
                    <span style="font-size: 0.75rem; color: #94A3B8;">
                        Lat: {lat:.6f}, Lon: {lon:.6f}
                    </span>
                </p>
                <p style="color: #94A3B8; font-size: 0.75rem; font-style: italic; margin-top: 1rem;">
                    [L'immagine satellitare verrà caricata dal database]
                </p>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("#### Caratteristiche Rilevate (Computer Vision)")

            # CV indicators
            col_cv1, col_cv2, col_cv3 = st.columns(3)

            with col_cv1:
                icon = "✅" if has_solar_panels else "❌"
                color = "#10B981" if has_solar_panels else "#EF4444"
                bg_color = "#DCFCE7" if has_solar_panels else "#FEE2E2"

                st.markdown(f"""
                <div class="glass-card" style="text-align: center; background: {bg_color}; border-left: 4px solid {color};">
                    <p style="font-size: 2rem; margin: 0;">{icon}</p>
                    <p style="margin: 0.5rem 0 0 0; color: {color}; font-weight: 600; font-size: 0.9rem;">
                        Pannelli Solari
                    </p>
                    <p style="margin: 0.25rem 0 0 0; color: #64748B; font-size: 0.75rem;">
                        {'Rilevati' if has_solar_panels else 'Non rilevati'}
                    </p>
                </div>
                """, unsafe_allow_html=True)

            with col_cv2:
                icon = "✅" if has_pool else "❌"
                color = "#10B981" if has_pool else "#EF4444"
                bg_color = "#DCFCE7" if has_pool else "#FEE2E2"

                st.markdown(f"""
                <div class="glass-card" style="text-align: center; background: {bg_color}; border-left: 4px solid {color};">
                    <p style="font-size: 2rem; margin: 0;">{icon}</p>
                    <p style="margin: 0.5rem 0 0 0; color: {color}; font-weight: 600; font-size: 0.9rem;">
                        Piscina
                    </p>
                    <p style="margin: 0.25rem 0 0 0; color: #64748B; font-size: 0.75rem;">
                        {'Rilevata' if has_pool else 'Non rilevata'}
                    </p>
                </div>
                """, unsafe_allow_html=True)

            with col_cv3:
                icon = "✅" if has_garden else "❌"
                color = "#10B981" if has_garden else "#EF4444"
                bg_color = "#DCFCE7" if has_garden else "#FEE2E2"

                st.markdown(f"""
                <div class="glass-card" style="text-align: center; background: {bg_color}; border-left: 4px solid {color};">
                    <p style="font-size: 2rem; margin: 0;">{icon}</p>
                    <p style="margin: 0.5rem 0 0 0; color: {color}; font-weight: 600; font-size: 0.9rem;">
                        Giardino
                    </p>
                    <p style="margin: 0.25rem 0 0 0; color: #64748B; font-size: 0.75rem;">
                        {'Rilevato' if has_garden else 'Non rilevato'}
                    </p>
                </div>
                """, unsafe_allow_html=True)

            # All recommendations for this client
            st.markdown("### Tutte le Raccomandazioni")
            recs_data = []
            for rec in client_data['raccomandazioni']:
                score = calculate_recommendation_score(rec, st.session_state.nbo_weights)
                recs_data.append({
                    'Prodotto': rec['prodotto'],
                    'Area Bisogno': rec['area_bisogno'],
                    'Score': f"{score:.2f}",
                    'Retention Gain': f"{rec['componenti']['retention_gain']:.1f}%",
                    'Redditivita': f"{rec['componenti']['redditivita']:.1f}%",
                    'Propensione': f"{rec['componenti']['propensione']:.1f}%",
                    'Affinita': f"{rec['componenti']['affinita_cluster']:.1f}%"
                })

            df_recs = pd.DataFrame(recs_data)
            st.dataframe(df_recs, width="stretch", hide_index=True)

            # ═══════════════════════════════════════════════════════════════════
            # ADA SECTION - Client Support
            # ═══════════════════════════════════════════════════════════════════
            st.markdown("<br><br>", unsafe_allow_html=True)
            st.markdown("## 🤖 ADA – Supporto Cliente")

            # Initialize session state for email draft
            if 'client_email_draft' not in st.session_state:
                st.session_state.client_email_draft = None
            if 'current_draft_client' not in st.session_state:
                st.session_state.current_draft_client = None

            # Prepare client context for ADA
            codice_cliente = client_data['codice_cliente']
            nome_completo = f"{client_data['anagrafica']['nome']} {client_data['anagrafica']['cognome']}"

            # Get interaction indicators
            indicators = client_data.get('_interaction_indicators', {})
            has_interactions = any(indicators.values())

            # Build context string
            client_context = f"""Cliente: {nome_completo} ({codice_cliente})
CLV Stimato: €{client_data['metadata']['clv_stimato']:,}
Polizze Attuali: {client_data['metadata']['num_polizze_attuali']}
Prodotto Raccomandato: {recommendation['prodotto']}
Area Bisogno: {recommendation['area_bisogno']}
Score Raccomandazione: {calculate_recommendation_score(recommendation, st.session_state.nbo_weights):.1f}
Retention Gain: {recommendation['componenti']['retention_gain']:.1f}%
Propensione: {recommendation['componenti']['propensione']:.1f}%"""

            # Generate email draft button
            if st.button("✍️ Genera Bozza Email con ADA", type="primary", width="stretch", key="generate_email_draft"):
                prompt = f"""IMPORTANTE: NON usare alcun tool. Ti sto fornendo TUTTI i dati necessari qui sotto. Genera DIRETTAMENTE l'email.

DATI CLIENTE (già forniti, non recuperare dal database):
{client_context}

DATI AGENTE:
Nome: {st.session_state.user_name}
Email: {st.session_state.user_email}
Telefono: {st.session_state.user_phone}
Azienda: Vita Sicura

TASK: Scrivi una bozza di email commerciale professionale che:
1. Sia personalizzata per {nome_completo}
2. Proponga il prodotto "{recommendation['prodotto']}" evidenziandone i benefici
3. Usi un tono professionale ma cordiale
4. Includa una call-to-action chiara
5. Sia lunga 150-200 parole
6. Sia firmata da {st.session_state.user_name} di Vita Sicura (NON Generali)
7. Includa i contatti dell'agente (email e telefono) nella firma

FORMATO RICHIESTO:
**Oggetto:** [scrivi qui l'oggetto]

---

[Corpo dell'email con saluti, contenuto e firma che include nome agente, "Vita Sicura", email e telefono]

GENERA L'EMAIL ORA senza usare tool."""

                # Generate email using ADA engine
                with st.spinner("🤖 ADA sta generando la bozza email..."):
                    # Import ADA chat function
                    from ada_chat_enhanced import init_ada_engine, get_ada_response

                    # Initialize engine if needed
                    init_ada_engine()

                    # Get response from ADA
                    result = get_ada_response(prompt)

                    if result.get("success"):
                        st.session_state.client_email_draft = result.get("response")
                        st.session_state.current_draft_client = codice_cliente
                        st.success("✅ Bozza email generata con successo!")
                        st.rerun()
                    else:
                        st.error("❌ Errore nella generazione della bozza email. Riprova.")

            # Show email draft if available
            if st.session_state.current_draft_client == codice_cliente and st.session_state.client_email_draft:
                st.markdown("### 📧 Bozza Email Generata")
                st.markdown(f"""
                <div class="glass-card" style="background: #F0FDF4; border-left: 4px solid #10B981;">
                    {st.session_state.client_email_draft}
                </div>
                """, unsafe_allow_html=True)

                # Modify email button
                col1, col2 = st.columns(2)
                with col1:
                    modify_prompt = st.text_input(
                        "Modifica l'email con un prompt",
                        placeholder="es. 'rendila più formale', 'aggiungi urgenza'",
                        key="email_modify_prompt"
                    )

                with col2:
                    if st.button("🔄 Applica Modifica", key="apply_email_modification") and modify_prompt:
                        updated_prompt = f"""IMPORTANTE: NON usare alcun tool. Modifica DIRETTAMENTE l'email fornita.

EMAIL ATTUALE:
{st.session_state.client_email_draft}

RICHIESTA DI MODIFICA:
{modify_prompt}

CONTESTO CLIENTE (già fornito):
{client_context}

TASK: Modifica l'email secondo la richiesta mantenendo il formato:
**Oggetto:** [oggetto modificato]

---

[Corpo modificato]

GENERA LA VERSIONE MODIFICATA ORA senza usare tool."""

                        # Update email using ADA engine
                        with st.spinner("🤖 ADA sta modificando l'email..."):
                            # Import ADA chat function
                            from ada_chat_enhanced import get_ada_response

                            # Get response from ADA
                            result = get_ada_response(updated_prompt)

                            if result.get("success"):
                                st.session_state.client_email_draft = result.get("response")
                                st.success("✅ Email modificata con successo!")
                                st.rerun()
                            else:
                                st.error("❌ Errore nella modifica dell'email. Riprova.")

        else:
            # ═══════════════════════════════════════════════════════════════════════════════
            # NBO MAIN DASHBOARD VIEW
            # ═══════════════════════════════════════════════════════════════════════════════

            # Get all recommendations with current weights
            all_recs = get_all_recommendations(nbo_data, st.session_state.nbo_weights)

            # KPI Metrics
            total_clients = len(nbo_data)
            total_recs = len(all_recs)
            avg_score = sum(r['score'] for r in all_recs) / len(all_recs) if all_recs else 0

            # Count by area
            area_counts = {}
            for rec in all_recs:
                area = rec['area_bisogno']
                area_counts[area] = area_counts.get(area, 0) + 1

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric(
                    label="👥 Clienti Analizzati",
                    value=f"{total_clients:,}",
                    delta="con raccomandazioni"
                )

            with col2:
                st.metric(
                    label="📋 Raccomandazioni Totali",
                    value=f"{total_recs:,}",
                    delta=f"{total_recs/total_clients:.1f} per cliente" if total_clients > 0 else "0"
                )

            with col3:
                st.metric(
                    label="📈 Score Medio",
                    value=f"{avg_score:.2f}",
                    delta="ponderato"
                )

            with col4:
                top_area = max(area_counts, key=area_counts.get) if area_counts else "N/A"
                st.metric(
                    label="🎯 Top Area Bisogno",
                    value=top_area.split()[0] if top_area != "N/A" else "N/A",
                    delta=f"{area_counts.get(top_area, 0)} recs" if top_area != "N/A" else ""
                )

            st.markdown("<br>", unsafe_allow_html=True)

            # Tabs for NBO
            nbo_tab1, nbo_tab2, nbo_tab3 = st.tabs([
                "🏆 Top Raccomandazioni",
                "📊 Analytics NBO",
                "🔍 Ricerca Clienti"
            ])

            with nbo_tab1:
                st.markdown("### Top 20 Raccomandazioni per Score")
                st.markdown("""
                <p style="color: #64748B; font-size: 0.9rem; margin-bottom: 0.5rem;">
                    Le migliori opportunita di cross-selling/up-selling ordinate per score ponderato.
                    Clicca su un cliente per vedere i dettagli.
                </p>
                """, unsafe_allow_html=True)

                # Info box about filtering criteria
                st.markdown("""
                <div style="background: #EFF6FF; border-left: 4px solid #3B82F6; padding: 0.75rem; margin-bottom: 1rem; border-radius: 4px;">
                    <p style="margin: 0; color: #1E40AF; font-size: 0.85rem;">
                        ℹ️ <strong>Filtro automatico attivo:</strong> Vengono esclusi clienti con email (ultimi 5 gg lavorativi),
                        telefonate (ultimi 10 gg), nuove polizze (ultimi 30 gg), reclami aperti o sinistri (ultimi 60 gg).
                    </p>
                </div>
                """, unsafe_allow_html=True)

                # Top 5 button
                if st.button("🎯 Vai al Top 5 Azioni Prioritarie", type="primary", width="stretch"):
                    st.session_state.nbo_page = 'top5'
                    st.rerun()

                st.markdown("<br>", unsafe_allow_html=True)

                for i, rec in enumerate(all_recs[:20]):
                    score_color = "#10B981" if rec['score'] >= 70 else "#F59E0B" if rec['score'] >= 50 else "#EF4444"

                    # Check if client is eligible (should always be true due to filtering, but check for safety)
                    client_eligible = rec['client_data'].get('_is_eligible_top20', True)
                    warning_badge = "" if client_eligible else '<span style="background: #FEF3C7; color: #92400E; padding: 0.15rem 0.4rem; border-radius: 4px; font-size: 0.65rem; font-weight: 600; margin-left: 0.5rem;">⚠️ FILTRO</span>'

                    col_card, col_btn = st.columns([5, 1])

                    with col_card:
                        st.markdown(f"""
                        <div class="glass-card" style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem;">
                            <div style="flex: 1; min-width: 200px;">
                                <div style="display: flex; align-items: center; gap: 0.75rem;">
                                    <span style="background: linear-gradient(135deg, #00A0B0 0%, #00C9D4 100%); color: white; padding: 0.25rem 0.75rem; border-radius: 100px; font-size: 0.75rem; font-weight: 600;">#{i+1}</span>
                                    <h4 style="margin: 0; color: #1B3A5F; font-size: 1rem; font-weight: 600;">{rec['nome']} {rec['cognome']}{warning_badge}</h4>
                                </div>
                                <p style="margin: 0.25rem 0 0 2.5rem; color: #64748B; font-size: 0.85rem;">
                                    {rec['codice_cliente']} · {rec['prodotto']}
                                </p>
                            </div>
                            <div style="display: flex; gap: 1.5rem; align-items: center;">
                                <div style="text-align: center;">
                                    <p style="margin: 0; color: #94A3B8; font-size: 0.6rem; text-transform: uppercase; letter-spacing: 0.05em;">Area</p>
                                    <p style="margin: 0; color: #1B3A5F; font-size: 0.85rem; font-weight: 500;">{rec['area_bisogno'].split()[0]}</p>
                                </div>
                                <div style="text-align: center;">
                                    <p style="margin: 0; color: #94A3B8; font-size: 0.6rem; text-transform: uppercase; letter-spacing: 0.05em;">Score</p>
                                    <p style="margin: 0; color: {score_color}; font-size: 1.25rem; font-weight: 700; font-family: 'JetBrains Mono', monospace;">{rec['score']:.1f}</p>
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                    with col_btn:
                        if st.button("Dettagli", key=f"detail_{i}", width="stretch"):
                            st.session_state.nbo_page = 'detail'
                            st.session_state.nbo_selected_client = rec['client_data']
                            st.session_state.nbo_selected_recommendation = rec['recommendation']
                            st.rerun()

                # ADA Section at the end of Top 20
                st.markdown("<br><br>", unsafe_allow_html=True)
                st.markdown("## 🤖 ADA – Sintesi e Azioni")
                st.markdown("""
                <div class="glass-card" style="border-left: 4px solid #00A0B0;">
                    <p style="color: #64748B; font-size: 0.95rem; line-height: 1.6; margin-bottom: 1rem;">
                        ADA può aiutarti ad analizzare questi clienti prioritari e preparare comunicazioni personalizzate.
                    </p>
                </div>
                """, unsafe_allow_html=True)

                # Prepare context for ADA about Top 20 clients
                top20_context = "I Top 20 clienti prioritari sono:\n\n"
                for i, rec in enumerate(all_recs[:20]):
                    top20_context += f"{i+1}. {rec['nome']} {rec['cognome']} ({rec['codice_cliente']}) - Score: {rec['score']:.1f} - Prodotto: {rec['prodotto']}\n"

                # Button for mass email action
                if st.button("📧 Prepara Email Personalizzate", type="primary", width="stretch", key="mass_email_top20"):
                    st.session_state.ada_auto_prompt = f"""Analizza questi {len(all_recs[:20])} clienti prioritari del Top 20 e crea una strategia di contatto:

{top20_context}

Per i primi 5 clienti, suggerisci:
1. Il miglior approccio di contatto
2. I punti chiave da evidenziare nella comunicazione
3. Una bozza di email personalizzata che tenga conto del prodotto raccomandato e dello score

Le email devono essere personalizzate per ogni cliente, non identiche."""
                    st.rerun()

            with nbo_tab2:
                st.markdown("### Analytics NBO")

                analytics_col1, analytics_col2 = st.columns(2)

                with analytics_col1:
                    # Area distribution pie chart
                    fig_area = go.Figure(data=[go.Pie(
                        labels=list(area_counts.keys()),
                        values=list(area_counts.values()),
                        hole=0.6,
                        marker_colors=['#00A0B0', '#F59E0B', '#10B981', '#8B5CF6', '#EC4899'],
                        textinfo='percent+label',
                        textfont=dict(family='Inter', size=11, color='#1B3A5F')
                    )])

                    fig_area.update_layout(
                        title=dict(
                            text="Distribuzione per Area Bisogno",
                            font=dict(family='Inter', size=16, color='#1B3A5F', weight=600),
                            x=0.5
                        ),
                        paper_bgcolor='rgba(255,255,255,0)',
                        plot_bgcolor='rgba(255,255,255,0)',
                        font=dict(color='#64748B', family='Inter'),
                        showlegend=False,
                        height=350,
                        margin=dict(t=50, b=30, l=30, r=30),
                        annotations=[dict(
                            text=f"<b>{total_recs}</b><br>Totale",
                            x=0.5, y=0.5,
                            font=dict(family='JetBrains Mono', size=16, color='#1B3A5F'),
                            showarrow=False
                        )]
                    )

                    st.plotly_chart(fig_area, width="stretch")

                with analytics_col2:
                    # Score distribution histogram
                    scores = [r['score'] for r in all_recs]
                    fig_score = go.Figure(data=[go.Histogram(
                        x=scores,
                        nbinsx=20,
                        marker_color='#00A0B0',
                        marker_line_color='white',
                        marker_line_width=1
                    )])

                    fig_score.update_layout(
                        title=dict(
                            text="Distribuzione Score",
                            font=dict(family='Inter', size=16, color='#1B3A5F', weight=600),
                            x=0.5
                        ),
                        paper_bgcolor='rgba(255,255,255,0)',
                        plot_bgcolor='rgba(255,255,255,0)',
                        font=dict(color='#64748B', family='Inter'),
                        xaxis=dict(
                            title="Score",
                            showgrid=True,
                            gridcolor='rgba(226, 232, 240, 0.5)',
                            linecolor='#E2E8F0'
                        ),
                        yaxis=dict(
                            title="Frequenza",
                            showgrid=True,
                            gridcolor='rgba(226, 232, 240, 0.5)',
                            linecolor='#E2E8F0'
                        ),
                        height=350,
                        margin=dict(t=50, b=50, l=50, r=30)
                    )

                    st.plotly_chart(fig_score, width="stretch")

                # Product distribution
                st.markdown("### Top Prodotti Raccomandati")
                product_counts = {}
                for rec in all_recs:
                    prod = rec['prodotto']
                    product_counts[prod] = product_counts.get(prod, 0) + 1

                sorted_products = sorted(product_counts.items(), key=lambda x: x[1], reverse=True)[:10]

                fig_products = go.Figure(data=[go.Bar(
                    y=[p[0] for p in sorted_products][::-1],
                    x=[p[1] for p in sorted_products][::-1],
                    orientation='h',
                    marker_color='#00A0B0',
                    marker_line_color='white',
                    marker_line_width=1
                )])

                fig_products.update_layout(
                    paper_bgcolor='rgba(255,255,255,0)',
                    plot_bgcolor='rgba(255,255,255,0)',
                    font=dict(color='#64748B', family='Inter'),
                    xaxis=dict(
                        title="Numero Raccomandazioni",
                        showgrid=True,
                        gridcolor='rgba(226, 232, 240, 0.5)'
                    ),
                    yaxis=dict(
                        showgrid=False,
                        tickfont=dict(size=10)
                    ),
                    height=400,
                    margin=dict(t=20, b=50, l=250, r=30)
                )

                st.plotly_chart(fig_products, width="stretch")

            with nbo_tab3:
                st.markdown("### Ricerca Clienti NBO")

                search_term = st.text_input(
                    "Cerca cliente",
                    placeholder="Inserisci nome, cognome o codice cliente...",
                    key="nbo_search"
                )

                if search_term:
                    search_lower = search_term.lower()
                    filtered_clients = [
                        c for c in nbo_data
                        if search_lower in c['codice_cliente'].lower() or
                           search_lower in c['anagrafica']['nome'].lower() or
                           search_lower in c['anagrafica']['cognome'].lower() or
                           search_lower in c['anagrafica']['citta'].lower()
                    ]
                else:
                    filtered_clients = nbo_data[:20]

                st.markdown(f"**{len(filtered_clients)}** clienti trovati")

                for client in filtered_clients[:20]:
                    meta = client['metadata']
                    best_rec = max(client['raccomandazioni'], key=lambda r: calculate_recommendation_score(r, st.session_state.nbo_weights))
                    best_score = calculate_recommendation_score(best_rec, st.session_state.nbo_weights)

                    col_info, col_btn = st.columns([5, 1])

                    with col_info:
                        st.markdown(f"""
                        <div class="glass-card" style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem;">
                            <div style="flex: 1; min-width: 200px;">
                                <h4 style="margin: 0; color: #1B3A5F; font-size: 1rem; font-weight: 600;">{client['anagrafica']['nome']} {client['anagrafica']['cognome']}</h4>
                                <p style="margin: 0.25rem 0; color: #64748B; font-size: 0.85rem;">
                                    {client['codice_cliente']} · {client['anagrafica']['citta']}
                                </p>
                            </div>
                            <div style="display: flex; gap: 1.5rem; align-items: center;">
                                <div style="text-align: center;">
                                    <p style="margin: 0; color: #94A3B8; font-size: 0.6rem; text-transform: uppercase;">Polizze</p>
                                    <p style="margin: 0; color: #1B3A5F; font-size: 1.1rem; font-weight: 600;">{meta['num_polizze_attuali']}</p>
                                </div>
                                <div style="text-align: center;">
                                    <p style="margin: 0; color: #94A3B8; font-size: 0.6rem; text-transform: uppercase;">CLV</p>
                                    <p style="margin: 0; color: #00A0B0; font-size: 1.1rem; font-weight: 600;">€{meta['clv_stimato']:,}</p>
                                </div>
                                <div style="text-align: center;">
                                    <p style="margin: 0; color: #94A3B8; font-size: 0.6rem; text-transform: uppercase;">Best Score</p>
                                    <p style="margin: 0; color: #10B981; font-size: 1.1rem; font-weight: 600;">{best_score:.1f}</p>
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                    with col_btn:
                        if st.button("Vedi", key=f"client_{client['codice_cliente']}", width="stretch"):
                            st.session_state.nbo_page = 'detail'
                            st.session_state.nbo_selected_client = client
                            st.session_state.nbo_selected_recommendation = best_rec
                            st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# FOOTER
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

# Footer - Light Theme
st.markdown(f"""
<div style="padding: 1.5rem 0; border-top: 1px solid #E2E8F0;">
    <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 2rem;">
        <div style="flex: 1; min-width: 200px;">
            <p style="font-family: 'Inter', sans-serif; font-size: 0.7rem; font-weight: 600; color: #1B3A5F; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.5rem;">Data Sources</p>
            <p style="font-family: 'Inter', sans-serif; font-size: 0.8rem; color: #64748B; line-height: 1.6; margin: 0;">
                🌍 INGV - Classificazione Sismica<br>
                💧 ISPRA - IdroGEO Platform<br>
                ☀️ EC PVGIS - Solar Potential
            </p>
        </div>
        <div style="flex: 1; min-width: 200px; text-align: center;">
            <div style="display: inline-flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
                <svg width="24" height="24" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
                    <defs>
                        <linearGradient id="footerGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                            <stop offset="0%" stop-color="#00A0B0"/>
                            <stop offset="100%" stop-color="#00C9D4"/>
                        </linearGradient>
                    </defs>
                    <circle cx="50" cy="50" r="20" fill="none" stroke="url(#footerGrad)" stroke-width="2"/>
                    <circle cx="50" cy="50" r="35" fill="none" stroke="url(#footerGrad)" stroke-width="1.5"/>
                    <line x1="50" y1="10" x2="50" y2="25" stroke="url(#footerGrad)" stroke-width="2"/>
                    <line x1="50" y1="75" x2="50" y2="90" stroke="url(#footerGrad)" stroke-width="2"/>
                    <line x1="10" y1="50" x2="25" y2="50" stroke="url(#footerGrad)" stroke-width="2"/>
                    <line x1="75" y1="50" x2="90" y2="50" stroke="url(#footerGrad)" stroke-width="2"/>
                </svg>
                <span style="font-family: 'Inter', sans-serif; font-size: 1rem; font-weight: 700; color: #1B3A5F;">HELIOS</span>
            </div>
            <p style="font-family: 'Inter', sans-serif; font-size: 0.75rem; color: #64748B; margin: 0;">
                Ecosistema Assicurativo Geo-Cognitivo
            </p>
            <p style="font-family: 'Inter', sans-serif; font-size: 0.7rem; color: #94A3B8; margin-top: 0.25rem;">
                Powered by <strong style="color: #1B3A5F;">Vita Sicura</strong> • Generali AI Challenge
            </p>
        </div>
        <div style="flex: 1; min-width: 200px; text-align: right;">
            <p style="font-family: 'Inter', sans-serif; font-size: 0.7rem; font-weight: 600; color: #1B3A5F; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.5rem;">Last Update</p>
            <p style="font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; color: #64748B; margin: 0;">
                {datetime.now().strftime('%d/%m/%Y %H:%M')}
            </p>
            <p style="font-family: 'Inter', sans-serif; font-size: 0.75rem; color: #94A3B8; margin-top: 0.25rem;">
                v2.0.0 Vita Sicura Edition
            </p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)
