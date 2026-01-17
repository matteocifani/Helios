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
import json
import folium
from streamlit_folium import folium_static
from dotenv import load_dotenv
import os

# Load environment variables (Mapbox API Key)
load_dotenv()

# Import from new src structure
from src.ada.chat import render_ada_chat
from src.config.constants import (
    DEFAULT_SEISMIC_ZONE,
    SEISMIC_ZONE_COLORS,
    ABITAZIONI_COLUMNS,
)
from src.data.db_utils import (
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
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Playfair+Display:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200&display=swap');

    /* Fix for Streamlit sidebar toggle button showing text instead of icon */
    [data-testid="collapsedControl"],
    [data-testid="stSidebarCollapsedControl"],
    [data-testid="stSidebarNavCollapseIcon"],
    button[kind="headerNoPadding"] {
        font-size: 0 !important;
        color: transparent !important;
        text-indent: -9999px !important;
        overflow: hidden !important;
    }
    [data-testid="collapsedControl"] *,
    [data-testid="stSidebarCollapsedControl"] *,
    button[kind="headerNoPadding"] * {
        font-size: 0 !important;
        color: transparent !important;
    }
    [data-testid="collapsedControl"] svg,
    [data-testid="stSidebarCollapsedControl"] svg,
    button[kind="headerNoPadding"] svg {
        width: 24px !important;
        height: 24px !important;
        visibility: visible !important;
        display: block !important;
        fill: #64748B !important;
        color: #64748B !important;
        font-size: 24px !important;
    }
    [data-testid="collapsedControl"]:hover svg,
    [data-testid="stSidebarCollapsedControl"]:hover svg,
    button[kind="headerNoPadding"]:hover svg {
        fill: #00A0B0 !important;
        color: #00A0B0 !important;
    }

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

    p, .stMarkdown p {
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
    from db_utils import fetch_abitazioni, fetch_clienti

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


@st.cache_data(ttl=300)
def _get_risk_stats_cached(risk_categories: tuple, risk_scores: tuple) -> dict:
    """Calculate risk distribution statistics (cached with hashable args)."""
    from collections import Counter
    stats = Counter(risk_categories)
    total = len(risk_categories)

    if total > 0:
        avg_score = sum(risk_scores) / total
        avg_score = round(avg_score, 1) if avg_score == avg_score else 0  # NaN check
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


def get_risk_stats(df):
    """Calculate risk distribution statistics."""
    return _get_risk_stats_cached(
        tuple(df['risk_category'].tolist()),
        tuple(df['risk_score'].tolist())
    )


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


@st.cache_data(ttl=300)
def _calculate_score_cached(
    retention_gain: float, redditivita: float, propensione: float,
    w_retention: float, w_redditivita: float, w_propensione: float
) -> float:
    """Calculate weighted score (cached version with primitive args)."""
    return (
        retention_gain * w_retention / 100 +
        redditivita * w_redditivita / 100 +
        propensione * w_propensione / 100
    )


def calculate_recommendation_score(rec, weights):
    """Calculate weighted score for a recommendation."""
    c = rec['componenti']
    return _calculate_score_cached(
        c['retention_gain'], c['redditivita'], c['propensione'],
        weights['retention'], weights['redditivita'], weights['propensione']
    )


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

# Dashboard mode - NEW NAVIGATION
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'azioni_giorno'  # Default landing page

# Client detail view state
if 'viewing_client' not in st.session_state:
    st.session_state.viewing_client = None

# NBO weights (still needed for score calculation)
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

# ═══════════════════════════════════════════════════════════════════════════════
# DATA LOADING (no sidebar - navigation moved to horizontal bar)
# ═══════════════════════════════════════════════════════════════════════════════

# Load data
df = load_data()
filtered_df = df.copy()

# Hide Streamlit default sidebar with CSS
st.markdown("""
<style>
    [data-testid="stSidebar"] {
        display: none;
    }
    [data-testid="stSidebarCollapsedControl"] {
        display: none;
    }
</style>
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

# Dynamic header content based on current page
PAGE_TITLES = {
    'azioni_giorno': ("Azioni del Giorno", "I tuoi clienti prioritari da contattare oggi"),
    'cerca_cliente': ("Cerca Cliente", "Ricerca e visualizza dettagli clienti"),
    'portafoglio': ("Il Mio Portafoglio", "Overview delle performance del tuo portafoglio"),
    'mappa': ("Mappa Territoriale", "Visualizzazione geografica clienti"),
    'satellite': ("Analisi Satellitare", "Estrai informazioni dalle immagini per pricing e rischio"),
    'client_detail': ("Scheda Cliente 360°", "Dettaglio completo del cliente")
}
page_title, page_description = PAGE_TITLES.get(st.session_state.current_page, ("HELIOS", "Dashboard"))

# Header with logo - centered layout
header_col1, header_col2 = st.columns([8, 2])

with header_col1:
    st.markdown(f"""
    <div style="text-align: center; padding-left: 10%;">
        <div style="display: flex; flex-direction: column; align-items: center; gap: 0.25rem;">
            <span style="font-family: 'Inter', sans-serif; font-size: 5rem; font-weight: 800; background: linear-gradient(135deg, #00A0B0 0%, #00C9D4 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; letter-spacing: -0.02em; line-height: 1;">HELIOS</span>
            <span style="font-family: 'Inter', sans-serif; font-size: 0.85rem; font-weight: 500; color: #64748B; letter-spacing: 0.15em; text-transform: uppercase;">Geo-Cognitive Intelligence</span>
        </div>
        <h1 style="font-family: 'Playfair Display', serif; font-size: 1.5rem; font-weight: 700; color: #1B3A5F; margin: 0.75rem 0 0; letter-spacing: -0.02em;">{page_title}</h1>
        <p style="font-family: 'Inter', sans-serif; font-size: 0.85rem; color: #64748B; margin-top: 0.25rem; font-weight: 400;">{page_description}</p>
    </div>
    """, unsafe_allow_html=True)

with header_col2:
    st.markdown("""
    <div style="display: flex; justify-content: flex-end; align-items: flex-start; padding-top: 0.5rem;">
        <div style="display: flex; align-items: center; gap: 0.5rem; padding: 0.5rem 1rem; background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.2); border-radius: 100px; font-family: 'Inter', sans-serif; font-size: 0.75rem; font-weight: 500; color: #10B981; white-space: nowrap;">
            <span style="width: 8px; height: 8px; background: #10B981; border-radius: 50%;"></span>
            Sistema Attivo
        </div>
    </div>
    """, unsafe_allow_html=True)

# Divider
st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# HORIZONTAL NAVIGATION BAR
# ═══════════════════════════════════════════════════════════════════════════════

nav_col1, nav_col2, nav_col3, nav_col4, nav_col5, settings_col = st.columns([1, 1, 1, 1, 1, 0.5])

with nav_col1:
    if st.button("📋 Azioni", use_container_width=True, 
                 type="primary" if st.session_state.current_page == 'azioni_giorno' else "secondary"):
        st.session_state.current_page = 'azioni_giorno'
        st.rerun()

with nav_col2:
    if st.button("🔍 Clienti", use_container_width=True,
                 type="primary" if st.session_state.current_page == 'cerca_cliente' else "secondary"):
        st.session_state.current_page = 'cerca_cliente'
        st.rerun()

with nav_col3:
    if st.button("📊 Portfolio", use_container_width=True,
                 type="primary" if st.session_state.current_page == 'portafoglio' else "secondary"):
        st.session_state.current_page = 'portafoglio'
        st.rerun()

with nav_col4:
    if st.button("🗺️ Mappa", use_container_width=True,
                 type="primary" if st.session_state.current_page == 'mappa' else "secondary"):
        st.session_state.current_page = 'mappa'
        st.rerun()

with nav_col5:
    if st.button("🛰️ Satellite", use_container_width=True,
                 type="primary" if st.session_state.current_page == 'satellite' else "secondary"):
        st.session_state.current_page = 'satellite'
        st.rerun()

with settings_col:
    with st.popover("⚙️", use_container_width=True):
        st.markdown("### ⚙️ Impostazioni")
        st.markdown("---")
        st.markdown("**Pesi Score NBO**")
        
        retention_weight = st.slider(
            "Retention Gain",
            min_value=0.0, max_value=1.0,
            value=st.session_state.nbo_weights['retention'],
            step=0.01, key="settings_retention"
        )
        
        redditivita_weight = st.slider(
            "Redditività",
            min_value=0.0, max_value=1.0,
            value=st.session_state.nbo_weights['redditivita'],
            step=0.01, key="settings_redditivita"
        )
        
        propensione_weight = st.slider(
            "Propensione",
            min_value=0.0, max_value=1.0,
            value=st.session_state.nbo_weights['propensione'],
            step=0.01, key="settings_propensione"
        )
        
        st.session_state.nbo_weights = {
            'retention': retention_weight,
            'redditivita': redditivita_weight,
            'propensione': propensione_weight
        }

st.markdown("<br>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE ROUTING BASED ON CURRENT_PAGE
# ═══════════════════════════════════════════════════════════════════════════════

# Load NBO data for pages that need it
nbo_data = load_nbo_data()


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 1: AZIONI DEL GIORNO (Home Page)
# ═══════════════════════════════════════════════════════════════════════════════

if st.session_state.current_page == 'azioni_giorno':
    
    # Greeting
    st.markdown(f"""
    <div style="margin-bottom: 1.5rem;">
        <h2 style="font-family: 'Inter', sans-serif; font-size: 1.5rem; font-weight: 600; color: #1B3A5F; margin: 0;">
            👋 Buongiorno, {st.session_state.user_name}!
        </h2>
        <p style="font-family: 'Inter', sans-serif; font-size: 0.9rem; color: #64748B; margin: 0.25rem 0 0;">
            📅 {datetime.now().strftime('%A %d %B %Y').title()}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    if nbo_data:
        # Get top recommendations
        all_recs = get_all_recommendations(nbo_data, st.session_state.nbo_weights)
        top5 = all_recs[:5]
        
        # TOP 5 Section
        st.markdown("### 🎯 Top 5 Clienti da Contattare")
        
        cols = st.columns(5)
        for i, rec in enumerate(top5):
            score_color = "#10B981" if rec['score'] >= 70 else "#F59E0B" if rec['score'] >= 50 else "#EF4444"
            with cols[i]:
                st.markdown(f"""
                <div style="background: white; border: 1px solid #E2E8F0; border-radius: 16px; padding: 1rem; text-align: center; min-height: 180px;">
                    <span style="background: linear-gradient(135deg, #F59E0B 0%, #FBBF24 100%); color: white; padding: 0.2rem 0.6rem; border-radius: 100px; font-size: 0.7rem; font-weight: 700;">TOP {i+1}</span>
                    <h4 style="margin: 0.5rem 0 0.25rem; font-size: 0.95rem; color: #1B3A5F; font-weight: 600;">{rec['nome']}<br>{rec['cognome'][:1]}.</h4>
                    <p style="margin: 0; color: {score_color}; font-size: 1.75rem; font-weight: 700; font-family: 'JetBrains Mono';">{rec['score']:.0f}</p>
                    <p style="margin: 0; color: #64748B; font-size: 0.7rem;">{rec['area_bisogno'].split()[0]}</p>
                </div>
                """, unsafe_allow_html=True)
                if st.button("📞 Chiama", key=f"call_top_{i}", use_container_width=True):
                    st.session_state.current_page = 'client_detail'
                    st.session_state.nbo_selected_client = rec['client_data']
                    st.session_state.nbo_selected_recommendation = rec['recommendation']
                    st.rerun()
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # KPI Row
        st.markdown("### 📊 Sintesi Rapida")
        kpi1, kpi2, kpi3 = st.columns(3)
        with kpi1:
            st.metric("📞 Azioni Oggi", f"{len(top5)}", "clienti prioritari")
        with kpi2:
            avg_score = sum(r['score'] for r in top5) / len(top5) if top5 else 0
            st.metric("📈 Score Medio Top 5", f"{avg_score:.1f}", "su 100")
        with kpi3:
            total_clv = sum(r['client_data']['metadata']['clv_stimato'] for r in top5) if top5 else 0
            st.metric("💎 CLV Potenziale", f"€{total_clv:,}", "Top 5 clienti")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Alert Section
        st.markdown("### ⚠️ Alert & Scadenze")
        st.info("🔔 Funzionalità in sviluppo: qui verranno mostrate polizze in scadenza, clienti ad alto churn e reclami aperti.")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Full Top 20 List
        with st.expander("📋 Visualizza Top 20 Completo", expanded=False):
            for i, rec in enumerate(all_recs[:20]):
                score_color = "#10B981" if rec['score'] >= 70 else "#F59E0B" if rec['score'] >= 50 else "#EF4444"
                col_card, col_btn = st.columns([5, 1])
                with col_card:
                    st.markdown(f"""
                    <div class="glass-card" style="display: flex; justify-content: space-between; align-items: center; padding: 0.75rem 1rem; margin-bottom: 0.5rem;">
                        <div>
                            <span style="background: linear-gradient(135deg, #00A0B0, #00C9D4); color: white; padding: 0.15rem 0.5rem; border-radius: 100px; font-size: 0.7rem; font-weight: 600;">#{i+1}</span>
                            <strong style="margin-left: 0.5rem; color: #1B3A5F;">{rec['nome']} {rec['cognome']}</strong>
                            <span style="color: #64748B; font-size: 0.85rem; margin-left: 0.5rem;">{rec['prodotto']}</span>
                        </div>
                        <span style="color: {score_color}; font-weight: 700; font-family: 'JetBrains Mono';">{rec['score']:.1f}</span>
                    </div>
                    """, unsafe_allow_html=True)
                with col_btn:
                    if st.button("Dettagli", key=f"detail_{i}"):
                        st.session_state.current_page = 'client_detail'
                        st.session_state.nbo_selected_client = rec['client_data']
                        st.session_state.nbo_selected_recommendation = rec['recommendation']
                        st.rerun()
    else:
        st.warning("⚠️ Impossibile caricare i dati NBO.")

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 2: CERCA CLIENTE
# ═══════════════════════════════════════════════════════════════════════════════

elif st.session_state.current_page == 'cerca_cliente':
    
    search_col1, search_col2 = st.columns([3, 1])
    with search_col1:
        search_term = st.text_input("🔎 Cerca cliente", placeholder="Nome, cognome, codice cliente o città...")
    with search_col2:
        sort_by = st.selectbox("Ordina per", ["Score ↓", "CLV ↓", "Nome A-Z"])
    
    if nbo_data:
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
            filtered_clients = nbo_data[:30]
        
        st.markdown(f"**{len(filtered_clients)}** clienti trovati")
        
        for client in filtered_clients[:20]:
            meta = client['metadata']
            best_rec = max(client['raccomandazioni'], key=lambda r: calculate_recommendation_score(r, st.session_state.nbo_weights))
            best_score = calculate_recommendation_score(best_rec, st.session_state.nbo_weights)
            score_color = "#10B981" if best_score >= 70 else "#F59E0B" if best_score >= 50 else "#EF4444"
            
            col_info, col_btn = st.columns([5, 1])
            with col_info:
                st.markdown(f"""
                <div class="glass-card" style="display: flex; justify-content: space-between; align-items: center; padding: 0.75rem 1rem;">
                    <div>
                        <h4 style="margin: 0; color: #1B3A5F; font-size: 1rem;">{client['anagrafica']['nome']} {client['anagrafica']['cognome']}</h4>
                        <p style="margin: 0; color: #64748B; font-size: 0.8rem;">{client['codice_cliente']} · {client['anagrafica']['citta']}</p>
                    </div>
                    <div style="display: flex; gap: 1.5rem; align-items: center;">
                        <div style="text-align: center;">
                            <p style="margin: 0; color: #94A3B8; font-size: 0.6rem;">CLV</p>
                            <p style="margin: 0; color: #00A0B0; font-weight: 600;">€{meta['clv_stimato']:,}</p>
                        </div>
                        <div style="text-align: center;">
                            <p style="margin: 0; color: #94A3B8; font-size: 0.6rem;">Score</p>
                            <p style="margin: 0; color: {score_color}; font-weight: 700;">{best_score:.1f}</p>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            with col_btn:
                if st.button("Vedi", key=f"view_{client['codice_cliente']}"):
                    st.session_state.current_page = 'client_detail'
                    st.session_state.nbo_selected_client = client
                    st.session_state.nbo_selected_recommendation = best_rec
                    st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 3: IL MIO PORTAFOGLIO
# ═══════════════════════════════════════════════════════════════════════════════

elif st.session_state.current_page == 'portafoglio':
    
    # Get stats
    stats = get_risk_stats(filtered_df)
    
    # KPI Row
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("👥 Clienti Attivi", f"{stats['total']:,}", "nel portafoglio")
    with col2:
        total_clv = filtered_df['clv'].sum()
        st.metric("💎 CLV Totale", f"€{total_clv:,.0f}", "lifetime value")
    with col3:
        avg_churn = filtered_df['churn_probability'].mean() * 100 if len(filtered_df) > 0 else 0
        st.metric("⚠️ Churn Risk", f"{avg_churn:.1f}%", "media portafoglio")
    with col4:
        st.metric("🔴 Alto Rischio", f"{stats['critico'] + stats['alto']:,}", f"{stats['high_risk_pct']}% del totale")
    with col5:
        st.metric("⚡ Risk Score", f"{stats['avg_score']:.1f}", "su scala 0-100")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Charts Row
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        st.markdown("### Distribuzione Rischio")
        risk_counts = filtered_df['risk_category'].value_counts()
        fig_donut = go.Figure(data=[go.Pie(
            labels=risk_counts.index,
            values=risk_counts.values,
            hole=0.65,
            marker_colors=['#DC2626', '#EA580C', '#CA8A04', '#16A34A']
        )])
        fig_donut.update_layout(height=300, margin=dict(t=20, b=20, l=20, r=20),
                                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_donut, use_container_width=True)
    
    with chart_col2:
        st.markdown("### Zone Sismiche")
        zone_counts = filtered_df['zona_sismica'].value_counts().sort_index()
        fig_bar = go.Figure(data=[go.Bar(
            x=[f"Zona {z}" for z in zone_counts.index],
            y=zone_counts.values,
            marker_color=['#DC2626', '#EA580C', '#CA8A04', '#16A34A'][:len(zone_counts)]
        )])
        fig_bar.update_layout(height=300, margin=dict(t=20, b=40, l=40, r=20),
                              paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_bar, use_container_width=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Clienti ad alto rischio churn
    st.markdown("### 🚨 Top 10 Clienti a Rischio Churn")
    
    high_churn = filtered_df.nlargest(10, 'churn_probability')[['id', 'codice_cliente', 'citta', 'churn_probability', 'clv', 'risk_score']]
    
    if not high_churn.empty:
        for _, row in high_churn.iterrows():
            churn_pct = row['churn_probability'] * 100
            churn_color = "#DC2626" if churn_pct > 70 else "#EA580C" if churn_pct > 50 else "#CA8A04"
            st.markdown(f"""
            <div style="display: flex; justify-content: space-between; align-items: center; padding: 0.5rem 1rem; background: white; border-left: 3px solid {churn_color}; border-radius: 4px; margin-bottom: 0.5rem;">
                <div>
                    <strong style="color: #1B3A5F;">{row['codice_cliente']}</strong>
                    <span style="color: #64748B; margin-left: 0.5rem;">{row['citta']}</span>
                </div>
                <div style="display: flex; gap: 1.5rem;">
                    <span style="color: {churn_color}; font-weight: 700;">{churn_pct:.1f}% churn</span>
                    <span style="color: #00A0B0;">€{row['clv']:,.0f} CLV</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Opportunità Cross-selling
    st.markdown("### 💡 Opportunità Cross-Selling")
    st.info("Clienti mono-polizza con alto CLV identificati dall'analisi NBO - integrazione in sviluppo")

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 4: MAPPA TERRITORIALE
# ═══════════════════════════════════════════════════════════════════════════════

elif st.session_state.current_page == 'mappa':
    
    # Prepare map data
    map_df = filtered_df[
        filtered_df['latitudine'].notna() & 
        filtered_df['longitudine'].notna()
    ].copy()
    
    mapbox_key = os.getenv("MAPBOX_TOKEN")
    
    if len(map_df) == 0:
        st.warning("⚠️ Nessuna abitazione con coordinate geografiche disponibile.")
    else:
        # Colors based on NBO or Risk (default to risk for now)
        NBO_COLOR_MAP = {
            'high': [16, 185, 129, 200],    # Green
            'medium': [245, 158, 11, 200],   # Yellow
            'low': [239, 68, 68, 200]        # Red
        }
        RISK_COLOR_MAP = {
            'Critico': [220, 38, 38, 200],
            'Alto': [234, 88, 12, 200],
            'Medio': [202, 138, 4, 180],
            'Basso': [22, 163, 74, 180]
        }
        
        map_df['color'] = map_df['risk_category'].apply(lambda x: RISK_COLOR_MAP.get(x, [22, 163, 74, 180]))
        
        view_state = pdk.ViewState(
            latitude=map_df['latitudine'].mean(),
            longitude=map_df['longitudine'].mean(),
            zoom=5.5,
            pitch=0,
        )
        
        scatter_layer = pdk.Layer(
            "ScatterplotLayer",
            data=map_df,
            get_position=['longitudine', 'latitudine'],
            get_fill_color='color',
            get_radius=5000,
            pickable=True,
            radius_min_pixels=4,
            radius_max_pixels=15,
        )
        
        st.pydeck_chart(pdk.Deck(
            map_style='mapbox://styles/mapbox/light-v10',
            api_keys={'mapbox': mapbox_key},
            initial_view_state=view_state,
            layers=[scatter_layer],
            tooltip={"html": "<b>Città:</b> {citta}<br/><b>Rischio:</b> {risk_category}<br/><b>Cliente:</b> {codice_cliente}"}
        ))
        
        st.markdown("""
        <div style="display: flex; gap: 2rem; justify-content: center; margin-top: 1rem;">
            <div style="display:flex; align-items:center; gap:0.5rem;"><span style="width:12px; height:12px; background:#DC2626; border-radius:50%;"></span> <span>Critico</span></div>
            <div style="display:flex; align-items:center; gap:0.5rem;"><span style="width:12px; height:12px; background:#EA580C; border-radius:50%;"></span> <span>Alto</span></div>
            <div style="display:flex; align-items:center; gap:0.5rem;"><span style="width:12px; height:12px; background:#CA8A04; border-radius:50%;"></span> <span>Medio</span></div>
            <div style="display:flex; align-items:center; gap:0.5rem;"><span style="width:12px; height:12px; background:#16A34A; border-radius:50%;"></span> <span>Basso</span></div>
        </div>
        """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 5: ANALISI SATELLITARE
# ═══════════════════════════════════════════════════════════════════════════════

elif st.session_state.current_page == 'satellite':
    
    st.markdown("""
    <div style="background: #EFF6FF; border-left: 4px solid #3B82F6; padding: 1rem; margin-bottom: 1.5rem; border-radius: 4px;">
        <p style="margin: 0; color: #1E40AF; font-size: 0.9rem;">
            🛰️ <strong>Computer Vision per Pricing</strong><br>
            Estrai caratteristiche delle abitazioni dalle immagini satellitari per migliorare la valutazione del rischio.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Search
    search_input = st.text_input("🔍 Cerca cliente o indirizzo", placeholder="Codice cliente o indirizzo...")
    
    if search_input and nbo_data:
        matching_clients = [c for c in nbo_data if search_input.lower() in c['codice_cliente'].lower() or 
                           search_input.lower() in c['anagrafica']['indirizzo'].lower()]
        if matching_clients:
            client = matching_clients[0]
            lat = client['anagrafica']['latitudine']
            lon = client['anagrafica']['longitudine']
            
            col_img, col_features = st.columns(2)
            
            with col_img:
                st.markdown("### 📷 Vista Satellitare")
                mapbox_token = os.getenv("MAPBOX_TOKEN")
                if mapbox_token:
                    sat_url = f"https://api.mapbox.com/styles/v1/mapbox/satellite-v9/static/{lon},{lat},18/400x300?access_token={mapbox_token}"
                    st.image(sat_url, caption=f"Lat: {lat:.4f}, Lon: {lon:.4f}")
                else:
                    st.warning("MAPBOX_TOKEN non configurato")
            
            with col_features:
                st.markdown("### ✓ Caratteristiche Rilevate")
                
                # Checklist manuale per ora
                piscina = st.checkbox("🏊 Piscina", key="feat_pool")
                pannelli = st.checkbox("☀️ Pannelli Solari", key="feat_solar")
                giardino = st.checkbox("🌳 Giardino Ampio", key="feat_garden")
                tetto_buono = st.checkbox("🏠 Tetto in buone condizioni", key="feat_roof")
                
                st.markdown("---")
                
                # Calcolo impatto pricing
                base_premium = 380  # Premio base Casa Serena
                impact = 0
                if piscina: impact += 0.08
                if pannelli: impact -= 0.05
                if not tetto_buono: impact += 0.04
                
                new_premium = int(base_premium * (1 + impact))
                delta_pct = int(impact * 100)
                
                st.markdown(f"""
                ### 📊 Impatto Pricing
                - **Premio base:** €{base_premium}
                - **Premio suggerito:** €{new_premium} ({'+' if delta_pct > 0 else ''}{delta_pct}%)
                """)
        else:
            st.warning("Nessun cliente trovato")
    else:
        st.info("Inserisci un codice cliente per analizzare l'abitazione")

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 6: SCHEDA CLIENTE 360° (Detail View)
# ═══════════════════════════════════════════════════════════════════════════════

elif st.session_state.current_page == 'client_detail' and st.session_state.nbo_selected_client:
    
    client_data = st.session_state.nbo_selected_client
    recommendation = st.session_state.nbo_selected_recommendation
    
    # Back button
    if st.button("← Torna alla pagina precedente", type="secondary"):
        st.session_state.current_page = 'azioni_giorno'
        st.session_state.nbo_selected_client = None
        st.session_state.nbo_selected_recommendation = None
        st.rerun()
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Client Header
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
                <p style="margin: 0; color: #94A3B8; font-size: 0.65rem; text-transform: uppercase;">CLV Stimato</p>
                <p style="margin: 0; color: #00A0B0; font-size: 1.75rem; font-weight: 700; font-family: 'JetBrains Mono';">
                    €{client_data['metadata']['clv_stimato']:,}
                </p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Tabs for 360° view
    tab_polizze, tab_rischio, tab_storico, tab_recs = st.tabs([
        "📋 Polizze", "⚠️ Rischio", "📅 Storico", "💡 Raccomandazioni"
    ])
    
    with tab_polizze:
        meta = client_data['metadata']
        st.markdown("### Prodotti Attivi")
        prodotti = meta.get('prodotti_posseduti', [])
        if prodotti:
            if isinstance(prodotti, str):
                prodotti = [prodotti]
            for p in prodotti:
                st.markdown(f"- ✅ {p}")
        else:
            st.info("Nessun prodotto attivo")
        
        st.markdown("---")
        st.markdown("### Dati Cliente")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Età:** {client_data['anagrafica']['eta']} anni")
            st.markdown(f"**Indirizzo:** {client_data['anagrafica']['indirizzo']}")
            st.markdown(f"**Regione:** {client_data['anagrafica']['regione']}")
        with col2:
            st.markdown(f"**Churn Attuale:** {meta['churn_attuale']:.4f}")
            st.markdown(f"**Cluster NBA:** {meta['cluster_nba']}")
            st.markdown(f"**Cluster Risposta:** {meta['cluster_risposta']}")
    
    with tab_rischio:
        st.markdown("### 🌍 Analisi Geo-Rischio")
        lat = client_data['anagrafica']['latitudine']
        lon = client_data['anagrafica']['longitudine']
        mapbox_token = os.getenv("MAPBOX_TOKEN")
        
        if mapbox_token and lat and lon:
            sat_url = f"https://api.mapbox.com/styles/v1/mapbox/satellite-v9/static/{lon},{lat},17/500x300?access_token={mapbox_token}"
            st.image(sat_url, caption=f"Vista satellitare - Lat: {lat:.4f}, Lon: {lon:.4f}")
            if st.button("🛰️ Analizza con AI", type="primary"):
                st.session_state.current_page = 'satellite'
                st.rerun()
        else:
            st.info("Coordinate o MAPBOX_TOKEN non disponibili")
        
        st.markdown("---")
        st.markdown("### Indicatori di Rischio")
        st.info("Zona sismica, rischio idrogeologico, e features CV - in sviluppo")
    
    with tab_storico:
        st.markdown("### 📅 Storico Interazioni")
        indicators = client_data.get('_interaction_indicators', {})
        st.markdown(f"- **Email ultimi 5 gg:** {'✅' if indicators.get('email_last_5_days') else '❌'}")
        st.markdown(f"- **Telefonata ultimi 10 gg:** {'✅' if indicators.get('call_last_10_days') else '❌'}")
        st.markdown(f"- **Nuova polizza ultimi 30 gg:** {'✅' if indicators.get('new_policy_last_30_days') else '❌'}")
        st.markdown(f"- **Reclamo aperto:** {'⚠️' if indicators.get('open_complaint') else '❌'}")
        st.markdown(f"- **Sinistro ultimi 60 gg:** {'⚠️' if indicators.get('claim_last_60_days') else '❌'}")
    
    with tab_recs:
        st.markdown("### 💡 Raccomandazioni NBO")
        if recommendation:
            score = calculate_recommendation_score(recommendation, st.session_state.nbo_weights)
            score_color = "#10B981" if score >= 70 else "#F59E0B" if score >= 50 else "#EF4444"
            st.markdown(f"""
            <div class="glass-card" style="border-left: 4px solid {score_color}; margin-bottom: 1rem;">
                <h4 style="margin: 0; color: #1B3A5F;">{recommendation['prodotto']}</h4>
                <p style="color: #64748B; margin: 0.25rem 0;">Area: {recommendation['area_bisogno']}</p>
                <p style="color: {score_color}; font-size: 1.5rem; font-weight: 700; margin: 0.5rem 0;">Score: {score:.1f}</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("### Tutte le Raccomandazioni")
        for rec in client_data['raccomandazioni']:
            rec_score = calculate_recommendation_score(rec, st.session_state.nbo_weights)
            st.markdown(f"- **{rec['prodotto']}** - Score: {rec_score:.1f}")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # AZIONI RAPIDE - Email Generation & Call Registration
    # ═══════════════════════════════════════════════════════════════════════════════
    
    st.markdown("### ⚡ Azioni Rapide")
    
    # Initialize states for this section
    if 'show_call_form' not in st.session_state:
        st.session_state.show_call_form = False
    if 'client_email_draft' not in st.session_state:
        st.session_state.client_email_draft = None
    if 'current_draft_client' not in st.session_state:
        st.session_state.current_draft_client = None
    if 'show_success_message' not in st.session_state:
        st.session_state.show_success_message = False
    
    action_col1, action_col2 = st.columns(2)
    
    # ─────────────────────────────────────────────────────────────────────────────
    # EMAIL GENERATION
    # ─────────────────────────────────────────────────────────────────────────────
    with action_col1:
        if st.button("✉️ Genera Email con A.D.A.", type="primary", use_container_width=True, key="gen_email_btn"):
            # Build context for email generation
            nome_completo = f"{client_data['anagrafica']['nome']} {client_data['anagrafica']['cognome']}"
            codice_cliente = client_data['codice_cliente']
            # Compute score safely
            rec_score = calculate_recommendation_score(recommendation, st.session_state.nbo_weights) if recommendation else 0
            
            client_context = f"""Cliente: {nome_completo}
Codice: {codice_cliente}
Città: {client_data['anagrafica']['citta']}, {client_data['anagrafica']['provincia']}
Età: {client_data['anagrafica']['eta']} anni
CLV Stimato: €{client_data['metadata']['clv_stimato']:,}
Churn Probability: {client_data['metadata']['churn_attuale']:.2%}
Prodotto Raccomandato: {recommendation['prodotto'] if recommendation else 'N/A'}
Area Bisogno: {recommendation['area_bisogno'] if recommendation else 'N/A'}
Score Raccomandazione: {rec_score:.1f}"""


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
2. Proponga il prodotto "{recommendation['prodotto'] if recommendation else 'prodotti assicurativi'}" evidenziandone i benefici
3. Usi un tono professionale ma cordiale
4. Includa una call-to-action chiara
5. Sia lunga 150-200 parole
6. Sia firmata da {st.session_state.user_name} di Vita Sicura
7. Includa i contatti dell'agente (email e telefono) nella firma

FORMATO RICHIESTO:
**Oggetto:** [scrivi qui l'oggetto]

---

[Corpo dell'email con saluti, contenuto e firma che include nome agente, "Vita Sicura", email e telefono]

GENERA L'EMAIL ORA senza usare tool."""

            with st.spinner("🤖 A.D.A. sta generando la bozza email..."):
                try:
                    from ada_chat_enhanced import init_ada_engine, get_ada_response
                    init_ada_engine()
                    result = get_ada_response(prompt)
                    
                    if result.get("success"):
                        st.session_state.client_email_draft = result.get("response")
                        st.session_state.current_draft_client = codice_cliente
                        st.success("✅ Bozza email generata!")
                        st.rerun()
                    else:
                        st.error("❌ Errore nella generazione. Riprova.")
                except Exception as e:
                    st.error(f"❌ Errore: {str(e)}")
    
    # ─────────────────────────────────────────────────────────────────────────────
    # CALL REGISTRATION
    # ─────────────────────────────────────────────────────────────────────────────
    with action_col2:
        if st.button("📞 Ho chiamato il cliente", type="secondary", use_container_width=True, key="call_btn"):
            st.session_state.show_call_form = True
            st.rerun()
    
    # Show success message if flag is set
    if st.session_state.show_success_message:
        st.success("✅ Chiamata registrata! Il cliente non sarà più visibile nel Top 20/Top 5.")
        st.session_state.show_success_message = False
    
    # ─────────────────────────────────────────────────────────────────────────────
    # EMAIL DRAFT DISPLAY
    # ─────────────────────────────────────────────────────────────────────────────
    if st.session_state.current_draft_client == client_data['codice_cliente'] and st.session_state.client_email_draft:
        st.markdown("---")
        st.markdown("### 📧 Bozza Email Generata")
        st.markdown(f"""
        <div style="background: #F0FDF4; border-left: 4px solid #10B981; padding: 1rem; border-radius: 8px; white-space: pre-wrap;">
            {st.session_state.client_email_draft}
        </div>
        """, unsafe_allow_html=True)
        
        # Modify email
        modify_col1, modify_col2 = st.columns([3, 1])
        with modify_col1:
            modify_prompt = st.text_input(
                "Modifica l'email",
                placeholder="es. 'rendila più formale', 'aggiungi urgenza'",
                key="email_modify_prompt"
            )
        with modify_col2:
            if st.button("🔄 Modifica", key="apply_mod") and modify_prompt:
                updated_prompt = f"""Modifica questa email secondo la richiesta.

EMAIL ATTUALE:
{st.session_state.client_email_draft}

RICHIESTA DI MODIFICA:
{modify_prompt}

Restituisci SOLO l'email modificata, nient'altro."""
                
                with st.spinner("🤖 Modificando..."):
                    try:
                        from ada_chat_enhanced import init_ada_engine, get_ada_response
                        init_ada_engine()
                        result = get_ada_response(updated_prompt)
                        if result.get("success"):
                            st.session_state.client_email_draft = result.get("response")
                            st.rerun()
                    except:
                        st.error("Errore nella modifica")
        
        if st.button("🗑️ Cancella bozza", key="clear_draft"):
            st.session_state.client_email_draft = None
            st.session_state.current_draft_client = None
            st.rerun()
    
    # ─────────────────────────────────────────────────────────────────────────────
    # CALL REGISTRATION FORM
    # ─────────────────────────────────────────────────────────────────────────────
    if st.session_state.show_call_form:
        st.markdown("---")
        st.markdown("### 📞 Registra Chiamata")
        
        # Get top recommendation
        top_rec = None
        if client_data.get('raccomandazioni'):
            recs_sorted = sorted(
                client_data['raccomandazioni'],
                key=lambda r: calculate_recommendation_score(r, st.session_state.nbo_weights),
                reverse=True
            )
            top_rec = recs_sorted[0] if recs_sorted else None
        
        # Available products
        available_products = [
            "Assicurazione Casa e Famiglia: Casa Serena",
            "Piano Individuale Pensionistico (PIP): Pensione Serenità",
            "Polizza Salute e Infortuni: Salute Protetta",
            "Polizza Vita a Premi Ricorrenti: Risparmio Costante",
            "Polizza Vita a Premio Unico: Futuro Sicuro"
        ]
        
        # Polizza proposta
        polizza_scelta = st.radio(
            "Polizza proposta *",
            options=["Sì (raccomandata)", "No", "Altra"],
            horizontal=True,
            key="polizza_radio"
        )
        
        polizza_proposta = None
        if polizza_scelta == "Sì (raccomandata)" and top_rec:
            polizza_proposta = top_rec['prodotto']
            st.info(f"💡 Polizza raccomandata: **{polizza_proposta}**")
        elif polizza_scelta == "Altra":
            polizza_proposta = st.selectbox("Seleziona polizza", available_products, key="polizza_select")
        else:
            polizza_proposta = "Nessuna proposta"
        
        # Esito
        esito = st.selectbox(
            "Esito della chiamata *",
            options=["Positivo", "Neutro", "Negativo"],
            key="esito_select"
        )
        
        # Note
        note_aggiuntive = st.text_area(
            "Note aggiuntive",
            placeholder="Inserisci eventuali note sulla chiamata...",
            key="call_notes"
        )
        
        form_col1, form_col2 = st.columns(2)
        with form_col1:
            if st.button("❌ Annulla", use_container_width=True, key="cancel_call"):
                st.session_state.show_call_form = False
                st.rerun()
        
        with form_col2:
            if st.button("✅ Registra", type="primary", use_container_width=True, key="submit_call"):
                # Build notes
                note_complete = f"Polizza proposta: {polizza_proposta}\nEsito: {esito}"
                if note_aggiuntive:
                    note_complete += f"\nNote: {note_aggiuntive}"
                
                # Save to database
                try:
                    success = insert_phone_call_interaction(
                        client_data['codice_cliente'],
                        polizza_proposta=polizza_proposta,
                        esito=esito.lower(),
                        note=note_complete
                    )
                    
                    if success:
                        # Update indicators
                        if '_interaction_indicators' not in client_data:
                            client_data['_interaction_indicators'] = {}
                        client_data['_interaction_indicators']['call_last_10_days'] = True
                        
                        st.session_state.show_call_form = False
                        st.session_state.show_success_message = True
                        st.rerun()
                    else:
                        st.error("❌ Errore nella registrazione. Riprova.")
                except Exception as e:
                    st.error(f"❌ Errore: {str(e)}")


# Fallback if no page matches
else:
    st.warning("Pagina non trovata. Torna alla home.")
    if st.button("🏠 Vai alla Home"):
        st.session_state.current_page = 'azioni_giorno'
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

# ═══════════════════════════════════════════════════════════════════════════════
# A.D.A. FLOATING ASSISTANT
# ═══════════════════════════════════════════════════════════════════════════════

# Initialize A.D.A. states
if 'ada_response' not in st.session_state:
    st.session_state.ada_response = None

# CSS for fixed floating button
st.markdown("""
<style>
    .ada-fixed-container {
        position: fixed;
        bottom: 24px;
        right: 24px;
        z-index: 9999;
    }
</style>
""", unsafe_allow_html=True)

# Create floating A.D.A. container using columns at the bottom
st.markdown("<br><br>", unsafe_allow_html=True)

ada_spacer, ada_button_col = st.columns([5, 1])

with ada_button_col:
    with st.popover("🤖 Chiedi ad A.D.A.", use_container_width=True):
        st.markdown("### 🤖 A.D.A. Assistente")
        st.markdown("*Assistente Digitale Agente*")
        st.markdown("---")
        
        # Context info
        if st.session_state.current_page == 'client_detail' and st.session_state.nbo_selected_client:
            client = st.session_state.nbo_selected_client
            st.info(f"📋 Cliente: **{client['anagrafica']['nome']} {client['anagrafica']['cognome']}**")
        else:
            page_names = {
                'azioni_giorno': 'Azioni del Giorno',
                'cerca_cliente': 'Cerca Cliente', 
                'portafoglio': 'Portafoglio',
                'mappa': 'Mappa Territoriale',
                'satellite': 'Analisi Satellitare'
            }
            st.caption(f"📍 Pagina: {page_names.get(st.session_state.current_page, 'Dashboard')}")
        
        # Input field
        user_query = st.text_area(
            "Cosa posso fare per te?",
            placeholder="Es: 'Genera una email per questo cliente'\n'Mostra clienti ad alto rischio'\n'Analizza il rischio di questa zona'",
            height=100,
            key="ada_input"
        )
        
        if st.button("🚀 Invia ad A.D.A.", type="primary", use_container_width=True) and user_query:
            with st.spinner("🤖 A.D.A. sta elaborando..."):
                try:
                    from ada_chat_enhanced import init_ada_engine, get_ada_response
                    init_ada_engine()
                    
                    # Build context
                    context_prompt = user_query
                    if st.session_state.current_page == 'client_detail' and st.session_state.nbo_selected_client:
                        client = st.session_state.nbo_selected_client
                        context_prompt = f"""Contesto: Cliente {client['anagrafica']['nome']} {client['anagrafica']['cognome']} ({client['codice_cliente']}).
CLV: €{client['metadata']['clv_stimato']:,}, Città: {client['anagrafica']['citta']}

Richiesta: {user_query}"""
                    
                    result = get_ada_response(context_prompt)
                    if result.get("success"):
                        st.session_state.ada_response = result.get("response")
                    else:
                        st.session_state.ada_response = "❌ Errore nella risposta."
                except Exception as e:
                    st.session_state.ada_response = f"❌ Errore: {str(e)}"
        
        # Show response
        if st.session_state.ada_response:
            st.markdown("---")
            st.markdown("**💬 Risposta:**")
            st.success(st.session_state.ada_response)
            
            if st.button("🗑️ Pulisci", key="clear_ada"):
                st.session_state.ada_response = None
                st.rerun()
