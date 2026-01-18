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
from src.config.constants import (
    DEFAULT_SEISMIC_ZONE,
    ABITAZIONI_COLUMNS,
    BOLOGNA_COORDINATES,
)
from src.data.db_utils import (
    fetch_abitazioni,
    fetch_clienti,
    check_client_interactions,
    is_client_eligible_for_top20,
    check_all_clients_interactions_batch,
    insert_phone_call_interaction,
    fetch_client_risk_data,
    fetch_client_active_policies
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
# CUSTOM CSS - Load from external file for better performance
# ═══════════════════════════════════════════════════════════════════════════════

def load_css():
    """Load CSS from external file for better caching and maintainability."""
    css_path = os.path.join(os.path.dirname(__file__), 'src', 'styles', 'helios.css')
    try:
        with open(css_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        # Fallback to minimal inline CSS if file not found
        return ""

# Load and inject CSS
css_content = load_css()
if css_content:
    st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)


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
    # STEP 1: Score ALL clients first (no DB queries, just JSON data)
    all_recs = []
    for client in data:
        codice_cliente = client['codice_cliente']
        # Initialize eligibility flags (will be updated later if filter_top20)
        client['_is_eligible_top20'] = True
        client['_interaction_indicators'] = {}

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

    # Sort by score descending
    all_recs.sort(key=lambda x: x['score'], reverse=True)

    # STEP 2: If filtering, only check interactions for top candidates
    # Check more than 20 to account for some being filtered out
    if filter_top20:
        # Get unique client codes from top 100 recommendations (covers edge cases)
        top_candidates = []
        seen_clients = set()
        for rec in all_recs:
            cc = rec['codice_cliente']
            if cc not in seen_clients:
                seen_clients.add(cc)
                top_candidates.append(cc)
                if len(top_candidates) >= 100:
                    break

        # Batch check only these candidates (3-6 queries instead of 336)
        batch_interactions = check_all_clients_interactions_batch(top_candidates)

        # Filter out ineligible clients and update their flags
        filtered_recs = []
        for rec in all_recs:
            cc = rec['codice_cliente']
            client = rec['client_data']

            if cc in batch_interactions:
                indicators = batch_interactions[cc]
                is_eligible = not any(indicators.values())
                client['_is_eligible_top20'] = is_eligible
                client['_interaction_indicators'] = indicators

                if is_eligible:
                    filtered_recs.append(rec)
            else:
                # Client wasn't in top candidates, include them (they're lower scored anyway)
                filtered_recs.append(rec)

        return filtered_recs

    return all_recs


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS - Score Display and Policy Icons
# ═══════════════════════════════════════════════════════════════════════════════

def get_score_display(score: float) -> dict:
    """
    Convert numeric score to visual display with label and color.

    Returns:
        dict with 'label', 'color', 'bg_color', 'percentage'
    """
    if score >= 75:
        return {
            'label': 'Eccellente',
            'color': '#10B981',
            'bg_color': '#DCFCE7',
            'percentage': min(score, 100)
        }
    elif score >= 60:
        return {
            'label': 'Alta',
            'color': '#00A0B0',
            'bg_color': '#E0F7FA',
            'percentage': score
        }
    elif score >= 45:
        return {
            'label': 'Media',
            'color': '#F59E0B',
            'bg_color': '#FEF3C7',
            'percentage': score
        }
    else:
        return {
            'label': 'Bassa',
            'color': '#94A3B8',
            'bg_color': '#F1F5F9',
            'percentage': score
        }


def render_opportunity_bar(score: float) -> str:
    """
    Generate HTML for opportunity progress bar with label.
    """
    display = get_score_display(score)

    return f'''
    <div class="opportunity-bar-container">
        <div class="opportunity-bar">
            <div class="opportunity-bar-fill" style="width: {display['percentage']}%; background: {display['color']};"></div>
        </div>
        <span class="opportunity-label" style="color: {display['color']};">{display['label']}</span>
    </div>
    '''


def render_policy_icons(policies: list) -> str:
    """
    Generate HTML for policy icons based on owned policies.
    Uses emoji icons for better Streamlit compatibility.

    Args:
        policies: List of policy names

    Returns:
        HTML string with emoji icons
    """
    # Emoji mapping for policies (more compatible than SVG)
    POLICY_EMOJI = {
        "Polizza Salute e Infortuni: Salute Protetta": ("❤️", "#EF4444", "Salute"),
        "Assicurazione Casa e Famiglia: Casa Serena": ("🏠", "#F59E0B", "Casa"),
        "Polizza Vita a Premio Unico: Futuro Sicuro": ("📈", "#10B981", "Invest"),
        "Polizza Vita a Premi Ricorrenti: Risparmio Costante": ("💰", "#3B82F6", "Risp"),
        "Piano Individuale Pensionistico (PIP): Pensione Serenità": ("🛡️", "#8B5CF6", "PIP"),
    }

    if not policies:
        return '<span style="color: #94A3B8; font-size: 0.75rem;">-</span>'

    icons_html = '<div style="display: flex; gap: 0.25rem; align-items: center;">'

    for policy in policies:
        if policy in POLICY_EMOJI:
            emoji, color, label = POLICY_EMOJI[policy]
            icons_html += f'<span title="{label}" style="font-size: 1rem; cursor: help;">{emoji}</span>'

    icons_html += '</div>'
    return icons_html


def get_premium_clients(nbo_data: list, weights: dict, top_n: int = 5) -> list:
    """
    Get top premium clients with high CLV and good NBO score.

    Strategy: Find clients that maximize revenue potential.
    - Considers all clients (not filtered by interactions)
    - Prioritizes high CLV clients with good opportunity scores
    - Returns unique clients (one recommendation per client)
    """
    # Get all recommendations WITHOUT filtering (we want to see all opportunities)
    all_recs = get_all_recommendations(nbo_data, weights, filter_top20=False)

    if not all_recs:
        return []

    # Get best recommendation per client (avoid duplicates)
    client_best_recs = {}
    for rec in all_recs:
        codice = rec['codice_cliente']
        if codice not in client_best_recs or rec['score'] > client_best_recs[codice]['score']:
            client_best_recs[codice] = rec

    unique_recs = list(client_best_recs.values())

    # Calculate combined score for premium ranking
    # CLV is key indicator, score is secondary
    clv_values = [rec['client_data']['metadata']['clv_stimato'] for rec in unique_recs]
    max_clv = max(clv_values) if clv_values else 1

    for rec in unique_recs:
        clv = rec['client_data']['metadata']['clv_stimato']
        normalized_clv = (clv / max_clv) * 100 if max_clv > 0 else 0
        # Premium score: 50% CLV, 50% opportunity score
        rec['combined_score'] = (normalized_clv * 0.5) + (rec['score'] * 0.5)

    # Sort by combined score and return top N
    unique_recs.sort(key=lambda x: x['combined_score'], reverse=True)

    return unique_recs[:top_n]


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

# ═══════════════════════════════════════════════════════════════════════════════
# AGENT PROFILE - Mario Rossi (Bologna)
# ═══════════════════════════════════════════════════════════════════════════════
if 'agent_profile' not in st.session_state:
    st.session_state.agent_profile = {
        'name': 'Mario Rossi',
        'initials': 'MR',
        'email': 'mario.rossi@vitasicura.com',
        'phone': '+39 051 234 5678',
        'city': 'Bologna',
        'region': 'Emilia Romagna',
        'lat': 44.4949,
        'lon': 11.3426
    }

# User info (legacy aliases for compatibility)
if 'user_name' not in st.session_state:
    st.session_state.user_name = st.session_state.agent_profile['name']
if 'user_email' not in st.session_state:
    st.session_state.user_email = st.session_state.agent_profile['email']
if 'user_phone' not in st.session_state:
    st.session_state.user_phone = st.session_state.agent_profile['phone']

# ═══════════════════════════════════════════════════════════════════════════════
# ACTIVE MODE (replaces dashboard_mode)
# ═══════════════════════════════════════════════════════════════════════════════
if 'active_mode' not in st.session_state:
    st.session_state.active_mode = 'policy_advisor'

# Dashboard mode (legacy - for compatibility during transition)
if 'dashboard_mode' not in st.session_state:
    st.session_state.dashboard_mode = 'Helios NBO'  # Default to NBO which becomes Policy Advisor

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
# TOP NAVIGATION BAR
# ═══════════════════════════════════════════════════════════════════════════════

# Load data early (needed for both modes)
df = load_data()

# Add CSS for top navigation
st.markdown("""
<style>
    /* Top Navigation Bar */
    .top-nav-container {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 1rem 0;
        margin-bottom: 1.5rem;
        border-bottom: 1px solid #E2E8F0;
    }

    .nav-left {
        display: flex;
        align-items: center;
        gap: 2rem;
    }

    .nav-logo {
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .nav-logo-text {
        font-family: 'Inter', sans-serif;
        font-size: 1.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, #00A0B0 0%, #00C9D4 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .nav-buttons {
        display: flex;
        gap: 0.5rem;
    }

    .nav-button {
        padding: 0.5rem 1.25rem;
        border-radius: 100px;
        font-family: 'Inter', sans-serif;
        font-size: 0.875rem;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s ease;
        text-decoration: none;
        border: none;
    }

    .nav-button-active {
        background: linear-gradient(135deg, #00A0B0 0%, #00C9D4 100%);
        color: white;
    }

    .nav-button-inactive {
        background: #F3F4F6;
        color: #64748B;
    }

    .nav-button-inactive:hover {
        background: #E2E8F0;
        color: #1B3A5F;
    }

    /* User Profile Section */
    .user-profile {
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }

    .avatar-circle {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        background: linear-gradient(135deg, #00A0B0 0%, #00C9D4 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        font-size: 0.875rem;
    }

    .user-info {
        display: flex;
        flex-direction: column;
        gap: 0.1rem;
    }

    .user-name {
        font-family: 'Inter', sans-serif;
        font-size: 0.875rem;
        font-weight: 600;
        color: #1B3A5F;
    }

    .user-location {
        font-family: 'Inter', sans-serif;
        font-size: 0.75rem;
        color: #64748B;
    }

    /* Opportunity Bar Styles */
    .opportunity-bar-container {
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .opportunity-bar {
        width: 80px;
        height: 8px;
        background: #E2E8F0;
        border-radius: 100px;
        overflow: hidden;
    }

    .opportunity-bar-fill {
        height: 100%;
        border-radius: 100px;
        transition: width 0.3s ease;
    }

    .opportunity-label {
        font-family: 'Inter', sans-serif;
        font-size: 0.75rem;
        font-weight: 600;
        min-width: 70px;
    }

    .opportunity-eccellente { color: #10B981; }
    .opportunity-alta { color: #00A0B0; }
    .opportunity-media { color: #F59E0B; }
    .opportunity-bassa { color: #94A3B8; }

    /* Policy Icons Container */
    .policy-icons {
        display: flex;
        gap: 0.25rem;
        align-items: center;
    }

    .policy-icon {
        width: 24px;
        height: 24px;
        display: flex;
        align-items: center;
        justify-content: center;
    }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# HEADER - Compact with prominent HELIOS branding
# ═══════════════════════════════════════════════════════════════════════════════

agent = st.session_state.agent_profile

# Header using Streamlit columns - HELIOS prominent on left, user on right
header_left, header_right = st.columns([4, 2])

with header_left:
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 0.75rem;">
        <span style="font-size: 2.25rem; line-height: 1;">☀️</span>
        <div>
            <p style="margin: 0; font-size: 2.25rem; font-weight: 800; background: linear-gradient(135deg, #00A0B0 0%, #00C9D4 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; letter-spacing: -0.02em; line-height: 1;">HELIOS</p>
            <p style="margin: 0; font-size: 0.65rem; color: #94A3B8; letter-spacing: 0.15em; text-transform: uppercase;">Geo-Cognitive Insurance Intelligence</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

with header_right:
    st.markdown(f"""
    <div style="display: flex; align-items: center; justify-content: flex-end; gap: 1rem;">
        <div style="display: flex; align-items: center; gap: 0.4rem; padding: 0.4rem 0.75rem; background: rgba(16, 185, 129, 0.1); border-radius: 100px;">
            <span style="width: 6px; height: 6px; background: #10B981; border-radius: 50%; display: inline-block;"></span>
            <span style="font-size: 0.7rem; color: #10B981; font-weight: 500;">Online</span>
        </div>
        <div style="display: flex; align-items: center; gap: 0.5rem; padding: 0.5rem 0.75rem; background: #F8FAFC; border-radius: 10px; border: 1px solid #E2E8F0;">
            <div style="width: 32px; height: 32px; border-radius: 50%; background: linear-gradient(135deg, #00A0B0 0%, #00C9D4 100%); display: flex; align-items: center; justify-content: center; color: white; font-weight: 600; font-size: 0.75rem;">{agent['initials']}</div>
            <div>
                <p style="margin: 0; font-size: 0.8rem; font-weight: 600; color: #1B3A5F;">{agent['name']}</p>
                <p style="margin: 0; font-size: 0.65rem; color: #64748B;">{agent['city']}</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# MODE SELECTOR - Modern glassmorphism pills
# ═══════════════════════════════════════════════════════════════════════════════

# Custom CSS for mode selector tabs
st.markdown("""
<style>
    .mode-selector-wrapper {
        display: flex;
        justify-content: center;
        margin: 0.75rem 0 1rem;
    }
    .mode-selector-pills {
        display: inline-flex;
        gap: 4px;
        background: rgba(255, 255, 255, 0.7);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(0, 160, 176, 0.15);
        border-radius: 50px;
        padding: 4px;
    }
    .mode-pill {
        padding: 10px 28px;
        border-radius: 46px;
        font-family: 'Inter', sans-serif;
        font-size: 0.875rem;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        border: none;
        background: transparent;
        color: #64748B;
        text-decoration: none;
    }
    .mode-pill:hover {
        background: rgba(255, 255, 255, 0.8);
        color: #1B3A5F;
    }
    .mode-pill.active {
        background: linear-gradient(135deg, #00A0B0 0%, #00C9D4 100%);
        color: white;
        font-weight: 600;
        box-shadow: 0 4px 15px rgba(0, 160, 176, 0.3);
    }
</style>
""", unsafe_allow_html=True)

# Render mode selector with visual feedback
mode_col1, mode_col2, mode_col3 = st.columns([1, 2, 1])

with mode_col2:
    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        if st.button(
            "📋 Policy Advisor",
            key="nav_policy_advisor",
            type="primary" if st.session_state.active_mode == 'policy_advisor' else "secondary",
            use_container_width=True
        ):
            st.session_state.active_mode = 'policy_advisor'
            st.session_state.dashboard_mode = 'Helios NBO'
            st.rerun()
    with btn_col2:
        if st.button(
            "📊 Analytics",
            key="nav_analytics",
            type="primary" if st.session_state.active_mode == 'analytics' else "secondary",
            use_container_width=True
        ):
            st.session_state.active_mode = 'analytics'
            st.session_state.dashboard_mode = 'Helios View'
            st.rerun()

# Set default filtered_df for analytics mode
filtered_df = df

# ═══════════════════════════════════════════════════════════════════════════════
# CONDITIONAL CONTENT BASED ON DASHBOARD MODE
# ═══════════════════════════════════════════════════════════════════════════════

if st.session_state.dashboard_mode == 'Helios View':
    # ═══════════════════════════════════════════════════════════════════════════════
    # ANALYTICS MODE CONTENT (formerly Helios View)
    # ═══════════════════════════════════════════════════════════════════════════════

    # Import coordinates for default map center
    from src.config.constants import BOLOGNA_COORDINATES

    # ═══════════════════════════════════════════════════════════════════════════════
    # UNIVERSAL FILTERS (no regional restrictions)
    # ═══════════════════════════════════════════════════════════════════════════════

    with st.expander("🔍 Filtri Analisi", expanded=False):
        filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)

        with filter_col1:
            # Universal city filter - all cities available
            all_cities = sorted(df['citta'].dropna().unique().tolist()) if 'citta' in df.columns else []
            cities_list = ['Tutte le città'] + all_cities
            selected_city = st.selectbox("🏙️ Città", cities_list, label_visibility="collapsed")

        with filter_col2:
            risk_options = ['Tutti i rischi', 'Critico', 'Alto', 'Medio', 'Basso']
            selected_risk = st.selectbox("⚠️ Categoria Rischio", risk_options, label_visibility="collapsed")

        with filter_col3:
            zone_options = ['Tutte le zone', 'Zona 1', 'Zona 2', 'Zona 3', 'Zona 4']
            selected_zone = st.selectbox("🌍 Zona Sismica", zone_options, label_visibility="collapsed")

        with filter_col4:
            # Show active filters summary
            active_filters = []
            if selected_city != 'Tutte le città':
                active_filters.append(selected_city)
            if selected_risk != 'Tutti i rischi':
                active_filters.append(selected_risk)
            if selected_zone != 'Tutte le zone':
                active_filters.append(selected_zone)

            filter_text = ", ".join(active_filters) if active_filters else "Nessun filtro"
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, rgba(0, 160, 176, 0.08) 0%, rgba(0, 201, 212, 0.05) 100%); border-radius: 8px; padding: 0.5rem; text-align: center;">
                <p style="margin: 0; color: #64748B; font-size: 0.7rem;">Filtri Attivi</p>
                <p style="margin: 0; color: #00A0B0; font-weight: 600; font-size: 0.8rem;">{filter_text}</p>
            </div>
            """, unsafe_allow_html=True)

    # Start with all data (no regional restrictions)
    filtered_df = df.copy()

    # Apply filters
    if selected_city != 'Tutte le città':
        filtered_df = filtered_df[filtered_df['citta'] == selected_city]
    if selected_risk != 'Tutti i rischi':
        filtered_df = filtered_df[filtered_df['risk_category'] == selected_risk]
    if selected_zone != 'Tutte le zone':
        zone_num = int(selected_zone.split()[-1])
        filtered_df = filtered_df[filtered_df['zona_sismica'] == zone_num]

    # Warning if no results match filters
    if len(filtered_df) == 0:
        st.warning("⚠️ Nessuna abitazione corrisponde ai filtri selezionati.")

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
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # UNIFIED ANALYTICS VIEW - Map + Charts side by side
    # ═══════════════════════════════════════════════════════════════════════════════

    tab1, tab2 = st.tabs([
        "📊 Analytics & Mappa",
        "🔍 Dettaglio Clienti"
    ])

    with tab1:
        # Prepare map data
        map_df = filtered_df[
            filtered_df['latitudine'].notna() &
            filtered_df['longitudine'].notna()
        ].copy()

        # Check for Mapbox Token
        mapbox_key = os.getenv("MAPBOX_TOKEN")

        # Two-column layout: Map (60%) | Charts (40%)
        map_col, charts_col = st.columns([3, 2])

        with map_col:
            st.markdown("#### 🗺️ Mappa Geo-Rischio")

            if not mapbox_key:
                st.warning("⚠️ MAPBOX_TOKEN mancante nel file .env.")

            if len(map_df) == 0:
                st.warning("⚠️ Nessuna abitazione con coordinate geografiche disponibile.")
            else:
                # Prepare Colors for PyDeck
                RISK_COLOR_MAP = {
                    'Critico': [220, 38, 38, 200],
                    'Alto':    [234, 88, 12, 200],
                    'Medio':   [202, 138, 4, 180],
                    'Basso':   [22, 163, 74, 180]
                }
                DEFAULT_COLOR = [22, 163, 74, 180]
                map_df['color'] = map_df['risk_category'].apply(lambda x: RISK_COLOR_MAP.get(x, DEFAULT_COLOR))

                # Calculate center based on data if available
                if len(map_df) > 0:
                    center_lat = map_df['latitudine'].mean()
                    center_lon = map_df['longitudine'].mean()
                else:
                    center_lat = BOLOGNA_COORDINATES['lat']
                    center_lon = BOLOGNA_COORDINATES['lon']

                view_state = pdk.ViewState(
                    latitude=center_lat,
                    longitude=center_lon,
                    zoom=6,  # Wider view to show all Italy
                    pitch=0,
                )

                heatmap_layer = pdk.Layer(
                    "HeatmapLayer",
                    data=map_df,
                    get_position=['longitudine', 'latitudine'],
                    get_weight="risk_score",
                    opacity=0.4,
                    radius_pixels=40,
                    intensity=1,
                    threshold=0.2
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
                    stroked=True,
                    get_line_color=[255, 255, 255, 100]
                )

                st.pydeck_chart(pdk.Deck(
                    map_style='mapbox://styles/mapbox/light-v10',
                    api_keys={'mapbox': mapbox_key},
                    initial_view_state=view_state,
                    layers=[heatmap_layer, scatter_layer],
                    tooltip={
                        "html": "<b>Città:</b> {citta}<br/><b>Rischio:</b> {risk_score}<br/><b>Categoria:</b> {risk_category}",
                        "style": {"backgroundColor": "steelblue", "color": "white"}
                    }
                ), height=450)

                # Compact legend
                st.markdown("""
                <div style="display: flex; gap: 1rem; justify-content: center; flex-wrap: wrap; opacity: 0.8; margin-top: 0.5rem;">
                    <div style="display:flex; align-items:center; gap:0.25rem;"><span style="width:10px; height:10px; background:#DC2626; border-radius:50%;"></span> <span style="font-size:0.7rem;">Critico</span></div>
                    <div style="display:flex; align-items:center; gap:0.25rem;"><span style="width:10px; height:10px; background:#EA580C; border-radius:50%;"></span> <span style="font-size:0.7rem;">Alto</span></div>
                    <div style="display:flex; align-items:center; gap:0.25rem;"><span style="width:10px; height:10px; background:#CA8A04; border-radius:50%;"></span> <span style="font-size:0.7rem;">Medio</span></div>
                    <div style="display:flex; align-items:center; gap:0.25rem;"><span style="width:10px; height:10px; background:#16A34A; border-radius:50%;"></span> <span style="font-size:0.7rem;">Basso</span></div>
                </div>
                """, unsafe_allow_html=True)

        with charts_col:
            st.markdown("#### 📈 Quick Analytics")

            # Risk Distribution Donut - Compact
            risk_counts = filtered_df['risk_category'].value_counts()

            fig_donut = go.Figure(data=[go.Pie(
                labels=risk_counts.index,
                values=risk_counts.values,
                hole=0.65,
                marker_colors=['#DC2626', '#EA580C', '#CA8A04', '#16A34A'],
                textinfo='percent',
                textfont=dict(family='Inter', size=10, color='#1B3A5F'),
                hovertemplate="<b>%{label}</b><br>%{value:,} abitazioni<extra></extra>"
            )])

            fig_donut.update_layout(
                title=dict(text="Distribuzione Rischio", font=dict(family='Inter', size=14, color='#1B3A5F'), x=0.5),
                paper_bgcolor='rgba(255,255,255,0)',
                plot_bgcolor='rgba(255,255,255,0)',
                showlegend=False,
                annotations=[dict(text=f"<b>{len(filtered_df):,}</b>", x=0.5, y=0.5, font=dict(family='JetBrains Mono', size=16, color='#1B3A5F'), showarrow=False)],
                height=200,
                margin=dict(t=40, b=20, l=10, r=10)
            )
            st.plotly_chart(fig_donut, use_container_width=True)

            # Seismic Zone Bar Chart - Compact
            zone_counts = filtered_df['zona_sismica'].value_counts().sort_index()

            fig_bar = go.Figure(data=[go.Bar(
                x=[f"Z{z}" for z in zone_counts.index],
                y=zone_counts.values,
                marker=dict(color=['#DC2626', '#EA580C', '#CA8A04', '#16A34A'][:len(zone_counts)]),
                text=zone_counts.values,
                textposition='outside',
                textfont=dict(family='JetBrains Mono', size=10, color='#1B3A5F'),
            )])

            fig_bar.update_layout(
                title=dict(text="Zone Sismiche", font=dict(family='Inter', size=14, color='#1B3A5F'), x=0.5),
                paper_bgcolor='rgba(255,255,255,0)',
                plot_bgcolor='rgba(255,255,255,0)',
                xaxis=dict(showgrid=False, tickfont=dict(size=10, color='#64748B')),
                yaxis=dict(showgrid=True, gridcolor='rgba(226, 232, 240, 0.5)', tickfont=dict(size=9, color='#64748B')),
                height=200,
                margin=dict(t=40, b=30, l=30, r=10)
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        # Critical Highlights below the main row
        st.markdown("#### 🚨 Focus Criticità")
        critical_df = map_df[map_df['risk_category'].isin(['Critico', 'Alto'])].sort_values('risk_score', ascending=False).head(4) if len(map_df) > 0 else pd.DataFrame()

        if not critical_df.empty:
            crit_cols = st.columns(len(critical_df))
            for idx, row in enumerate(critical_df.itertuples()):
                with crit_cols[idx]:
                    risk_color = "#DC2626" if row.risk_category == 'Critico' else "#EA580C"
                    st.markdown(f"""
                    <div style="background: white; border: 1px solid {risk_color}; border-left: 4px solid {risk_color}; border-radius: 8px; padding: 0.75rem;">
                        <p style="margin:0; font-size: 0.8rem; color: #64748B;">{row.citta}</p>
                        <p style="font-size: 1.5rem; font-weight: 700; color: #1B3A5F; margin: 0;">{row.risk_score}</p>
                        <span style="font-size: 0.65rem; color: {risk_color}; font-weight: 600;">{row.risk_category.upper()}</span>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("✅ Nessuna criticità elevata rilevata.")

        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

        # Full-width analytics row
        st.markdown("#### 📊 Analisi Dettagliata")
        analytics_col1, analytics_col2 = st.columns(2)

        with analytics_col1:
            # CLV vs Risk Score Scatter
            fig_scatter = px.scatter(
                filtered_df,
                x='risk_score',
                y='clv',
                color='risk_category',
                color_discrete_map={'Critico': '#DC2626', 'Alto': '#EA580C', 'Medio': '#CA8A04', 'Basso': '#16A34A'},
                size='churn_probability',
                hover_data=['citta'],
                labels={'risk_score': 'Risk Score', 'clv': 'CLV (€)', 'risk_category': 'Categoria'}
            )

            fig_scatter.update_layout(
                title=dict(text="CLV vs Risk Score", font=dict(family='Inter', size=16, color='#1B3A5F'), x=0.5),
                paper_bgcolor='rgba(255,255,255,0)',
                plot_bgcolor='rgba(255,255,255,0)',
                xaxis=dict(showgrid=True, gridcolor='rgba(226, 232, 240, 0.5)', linecolor='#E2E8F0'),
                yaxis=dict(showgrid=True, gridcolor='rgba(226, 232, 240, 0.5)', linecolor='#E2E8F0'),
                legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5, font=dict(size=10, color='#64748B')
                ),
                height=400,
                margin=dict(t=60, b=80, l=60, r=40)
            )
    
            st.plotly_chart(fig_scatter, use_container_width=True)

        with analytics_col2:
            # Churn Probability Distribution - Compact
            churn_bins = pd.cut(filtered_df['churn_probability'], bins=[0, 0.2, 0.4, 0.6, 0.8, 1.0],
                               labels=['Molto Basso', 'Basso', 'Medio', 'Alto', 'Molto Alto'])
            churn_counts = churn_bins.value_counts().sort_index()

            fig_churn = go.Figure(data=[go.Bar(
                y=churn_counts.index.astype(str),
                x=churn_counts.values,
                orientation='h',
                marker=dict(color=['#16A34A', '#00A0B0', '#CA8A04', '#EA580C', '#DC2626'][:len(churn_counts)]),
                text=churn_counts.values,
                textposition='outside',
                textfont=dict(family='JetBrains Mono', size=10, color='#1B3A5F'),
            )])

            fig_churn.update_layout(
                title=dict(text="Churn Probability", font=dict(family='Inter', size=16, color='#1B3A5F'), x=0.5),
                paper_bgcolor='rgba(255,255,255,0)',
                plot_bgcolor='rgba(255,255,255,0)',
                xaxis=dict(showgrid=True, gridcolor='rgba(226, 232, 240, 0.5)', tickfont=dict(size=10, color='#64748B')),
                yaxis=dict(showgrid=False, tickfont=dict(size=10, color='#64748B')),
                height=350,
                margin=dict(t=50, b=30, l=90, r=40)
            )
            st.plotly_chart(fig_churn, use_container_width=True)

        # City breakdown - Compact
        st.markdown("#### 🏙️ Top 10 Città per Rischio")

        city_risk = filtered_df.groupby('citta').agg({
            'risk_score': 'mean',
            'id': 'count',
            'clv': 'sum'
        }).rename(columns={'id': 'n_abitazioni', 'clv': 'clv_totale'}).reset_index()
        city_risk = city_risk.sort_values('risk_score', ascending=False).head(10)

        fig_city = go.Figure(data=[go.Bar(
            x=city_risk['citta'],
            y=city_risk['risk_score'],
            marker=dict(color=city_risk['risk_score'], colorscale=[[0, '#16A34A'], [0.5, '#CA8A04'], [1, '#DC2626']]),
            text=[f"{x:.0f}" for x in city_risk['risk_score']],
            textposition='outside',
            textfont=dict(family='JetBrains Mono', size=10, color='#1B3A5F'),
            hovertemplate="<b>%{x}</b><br>Risk: %{y:.1f}<extra></extra>"
        )])

        fig_city.update_layout(
            paper_bgcolor='rgba(255,255,255,0)',
            plot_bgcolor='rgba(255,255,255,0)',
            xaxis=dict(showgrid=False, tickfont=dict(size=9, color='#64748B'), tickangle=-45),
            yaxis=dict(showgrid=True, gridcolor='rgba(226, 232, 240, 0.5)', range=[0, 100], tickfont=dict(size=9, color='#64748B')),
            height=300,
            margin=dict(t=20, b=70, l=40, r=20)
        )
        st.plotly_chart(fig_city, use_container_width=True)


    # ═══════════════════════════════════════════════════════════════════════════════
    # TAB 2: CLIENT DETAIL (was tab3)
    # ═══════════════════════════════════════════════════════════════════════════════

    with tab2:
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

        # Display as cards - Light Theme (using itertuples for performance)
        for row in display_df.head(20).itertuples():
            risk_class = row.risk_category.lower()
            solar_info = f"☀️ {row.solar_potential_kwh:,} kWh/anno" if pd.notna(row.solar_potential_kwh) else "☀️ Non calcolato"

            st.markdown(f"""
            <div class="glass-card" style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem;">
                <div style="flex: 1; min-width: 200px;">
                    <h4 style="margin: 0; color: #1B3A5F; font-size: 1.1rem; font-weight: 600;">{row.id}</h4>
                    <p style="margin: 0.25rem 0; color: #64748B; font-size: 0.85rem;">
                        📍 {row.citta} · {row.codice_cliente}
                    </p>
                </div>
                <div style="display: flex; gap: 1.5rem; flex-wrap: wrap; align-items: center;">
                    <div style="text-align: center;">
                        <p style="margin: 0; color: #94A3B8; font-size: 0.65rem; text-transform: uppercase; letter-spacing: 0.05em; font-weight: 600;">Risk Score</p>
                        <p style="margin: 0; color: #1B3A5F; font-size: 1.5rem; font-weight: 700; font-family: 'JetBrains Mono', monospace;">{row.risk_score}</p>
                    </div>
                    <div style="text-align: center;">
                        <p style="margin: 0; color: #94A3B8; font-size: 0.65rem; text-transform: uppercase; letter-spacing: 0.05em; font-weight: 600;">Zona</p>
                        <p style="margin: 0; color: #1B3A5F; font-size: 1.5rem; font-weight: 700; font-family: 'JetBrains Mono', monospace;">{row.zona_sismica}</p>
                    </div>
                    <div style="text-align: center;">
                        <p style="margin: 0; color: #94A3B8; font-size: 0.65rem; text-transform: uppercase; letter-spacing: 0.05em; font-weight: 600;">CLV</p>
                        <p style="margin: 0; color: #00A0B0; font-size: 1.5rem; font-weight: 700; font-family: 'JetBrains Mono', monospace;">€{row.clv:,}</p>
                    </div>
                    <span class="risk-badge risk-{risk_class}">{row.risk_category}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        if len(display_df) > 20:
            st.info(f"📄 Mostrati i primi 20 risultati di {len(display_df):,}. Usa i filtri per restringere la ricerca.")
    
    
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
                    Questi sono i clienti con il punteggio piu alto per i quali e consigliato effettuare una chiamata
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
                    if st.button("Dettagli", key=f"top5_detail_{i}", use_container_width=True):
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
                    ADA puo aiutarti ad analizzare questi clienti prioritari e preparare comunicazioni personalizzate.
                </p>
            </div>
            """, unsafe_allow_html=True)

            # Prepare context for ADA about Top 5 clients
            top5_context = "I Top 5 clienti prioritari sono:\n\n"
            for i, rec in enumerate(top5_recs):
                top5_context += f"{i+1}. {rec['nome']} {rec['cognome']} ({rec['codice_cliente']}) - Score: {rec['score']:.1f} - Prodotto raccomandato: {rec['prodotto']}\n"

            # Button for mass email action
            if st.button("📧 Prepara Email Personalizzate", type="primary", use_container_width=True, key="mass_email_top5"):
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
                if st.button("← Torna alla Dashboard", type="secondary", use_container_width=True):
                    st.session_state.nbo_page = 'dashboard'
                    st.session_state.nbo_selected_client = None
                    st.session_state.nbo_selected_recommendation = None
                    st.rerun()

            with col_action:
                # Create a button instead of expander to avoid label issues
                if st.button("📞 Ho chiamato il cliente", type="primary", use_container_width=True, key="open_call_form"):
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
                        if st.button("❌ Annulla", use_container_width=True):
                            st.session_state.show_call_form = False
                            st.rerun()

                    with col_submit:
                        if st.button("✅ Registra chiamata", type="primary", use_container_width=True):
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
                                if '_interaction_indicators' not in client_data:
                                    client_data['_interaction_indicators'] = {}
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
                    st.success("✅ Esito registrato! Il cliente non sara piu visibile nel Top 20/Top 5.")
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

            # ═══════════════════════════════════════════════════════════════════
            # RISK CARDS SECTION
            # ═══════════════════════════════════════════════════════════════════
            st.markdown("### 🌍 Profilo di Rischio")
            
            # Fetch risk data for this client
            risk_data = fetch_client_risk_data(client_data['codice_cliente'])
            
            # Define risk colors
            def get_risk_color(level):
                colors = {
                    'Critico': ('#DC2626', '#FEE2E2'),
                    'Alto': ('#EA580C', '#FFEDD5'),
                    'Medio': ('#CA8A04', '#FEF9C3'),
                    'Basso': ('#16A34A', '#DCFCE7'),
                }
                return colors.get(level, ('#64748B', '#F1F5F9'))
            
            def get_seismic_level(zona):
                levels = {1: 'Critico', 2: 'Alto', 3: 'Medio', 4: 'Basso'}
                return levels.get(zona, 'Basso')
            
            def get_hydro_level(pct):
                if pct >= 10: return 'Critico'
                if pct >= 5: return 'Alto'
                if pct >= 2: return 'Medio'
                return 'Basso'
            
            # Create 3 columns for risk cards
            risk_col1, risk_col2, risk_col3 = st.columns(3)
            
            with risk_col1:
                seismic_level = get_seismic_level(risk_data['zona_sismica'])
                seismic_color, seismic_bg = get_risk_color(seismic_level)
                st.markdown(f"""
                <div style="background: {seismic_bg}; border-left: 4px solid {seismic_color}; border-radius: 12px; padding: 1rem; height: 100%;">
                    <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
                        <span style="font-size: 1.5rem;">🏔️</span>
                        <span style="color: #1B3A5F; font-weight: 600; font-size: 0.9rem;">Rischio Sismico</span>
                    </div>
                    <p style="margin: 0; font-family: 'JetBrains Mono', monospace; font-size: 1.75rem; font-weight: 700; color: {seismic_color};">
                        Zona {risk_data['zona_sismica']}
                    </p>
                    <span style="background: {seismic_color}; color: white; padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.7rem; font-weight: 600;">
                        {seismic_level}
                    </span>
                </div>
                """, unsafe_allow_html=True)
            
            with risk_col2:
                hydro_level = get_hydro_level(risk_data['hydro_risk_p3'])
                hydro_color, hydro_bg = get_risk_color(hydro_level)
                st.markdown(f"""
                <div style="background: {hydro_bg}; border-left: 4px solid {hydro_color}; border-radius: 12px; padding: 1rem; height: 100%;">
                    <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
                        <span style="font-size: 1.5rem;">🌊</span>
                        <span style="color: #1B3A5F; font-weight: 600; font-size: 0.9rem;">Rischio Idrogeologico</span>
                    </div>
                    <p style="margin: 0; font-family: 'JetBrains Mono', monospace; font-size: 1.75rem; font-weight: 700; color: {hydro_color};">
                        {risk_data['hydro_risk_p3']}%
                    </p>
                    <span style="background: {hydro_color}; color: white; padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.7rem; font-weight: 600;">
                        P3 - {hydro_level}
                    </span>
                </div>
                """, unsafe_allow_html=True)
            
            with risk_col3:
                flood_level = get_hydro_level(risk_data['flood_risk_p4'])
                flood_color, flood_bg = get_risk_color(flood_level)
                st.markdown(f"""
                <div style="background: {flood_bg}; border-left: 4px solid {flood_color}; border-radius: 12px; padding: 1rem; height: 100%;">
                    <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
                        <span style="font-size: 1.5rem;">🌧️</span>
                        <span style="color: #1B3A5F; font-weight: 600; font-size: 0.9rem;">Rischio Alluvione</span>
                    </div>
                    <p style="margin: 0; font-family: 'JetBrains Mono', monospace; font-size: 1.75rem; font-weight: 700; color: {flood_color};">
                        {risk_data['flood_risk_p4']}%
                    </p>
                    <span style="background: {flood_color}; color: white; padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.7rem; font-weight: 600;">
                        P4 - {flood_level}
                    </span>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # ═══════════════════════════════════════════════════════════════════
            # ACTIVE POLICIES SECTION
            # ═══════════════════════════════════════════════════════════════════
            st.markdown("### 📋 Polizze Attive")
            
            # Fetch active policies
            active_policies = fetch_client_active_policies(client_data['codice_cliente'])
            
            if active_policies:
                policy_cols = st.columns(min(len(active_policies), 3))
                for idx, policy in enumerate(active_policies[:3]):
                    with policy_cols[idx]:
                        # Determine expiry status
                        days = policy.get('days_to_expiry')
                        if days is not None and days <= 30:
                            expiry_color = '#DC2626'
                            expiry_bg = '#FEE2E2'
                            expiry_icon = '⚠️'
                        elif days is not None and days <= 90:
                            expiry_color = '#CA8A04'
                            expiry_bg = '#FEF9C3'
                            expiry_icon = '📅'
                        else:
                            expiry_color = '#16A34A'
                            expiry_bg = '#DCFCE7'
                            expiry_icon = '✅'
                        
                        premio = policy.get('premio_annuo', 0) or 0
                        st.markdown(f"""
                        <div class="glass-card" style="border-left: 4px solid #00A0B0;">
                            <p style="margin: 0 0 0.5rem 0; color: #1B3A5F; font-weight: 600; font-size: 0.9rem;">
                                {policy['nome_prodotto'][:40]}{'...' if len(policy['nome_prodotto']) > 40 else ''}
                            </p>
                            <p style="margin: 0; color: #00A0B0; font-family: 'JetBrains Mono', monospace; font-size: 1.25rem; font-weight: 700;">
                                €{premio:,.0f}/anno
                            </p>
                            <div style="margin-top: 0.5rem; background: {expiry_bg}; padding: 0.25rem 0.5rem; border-radius: 4px; display: inline-block;">
                                <span style="color: {expiry_color}; font-size: 0.75rem; font-weight: 600;">
                                    {expiry_icon} {f'{days} giorni alla scadenza' if days is not None else 'Scadenza N/D'}
                                </span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class="glass-card" style="text-align: center; padding: 2rem;">
                    <p style="color: #94A3B8; font-style: italic; margin: 0;">
                        📭 Nessuna polizza attiva
                    </p>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)

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
            st.markdown("""
            <h3 style="font-family: 'Inter', sans-serif; color: #1B3A5F; margin-bottom: 0.5rem;">
                🛰️ Cosa sappiamo dell'abitazione
            </h3>
            <p style="color: #64748B; font-size: 0.85rem; margin-bottom: 1rem;">
                Caratteristiche rilevate dall'analisi satellitare
            </p>
            """, unsafe_allow_html=True)

            # CV feature data (from database or simulated)
            import hashlib
            codice_cliente = client_data['codice_cliente']
            client_hash = int(hashlib.md5(codice_cliente.encode()).hexdigest(), 16)

            # CV detections with more detail
            cv_features = {
                'solar_panels': {
                    'detected': (client_hash % 3) == 0,
                    'label': 'Pannelli Solari',
                    'icon': '☀️',
                    'risk_note': 'Potenziale per polizza green energy'
                },
                'pool': {
                    'detected': (client_hash % 5) == 0,
                    'label': 'Piscina',
                    'icon': '🏊',
                    'risk_note': 'Richiede copertura aggiuntiva'
                },
                'garden': {
                    'detected': (client_hash % 2) == 0,
                    'label': 'Giardino',
                    'icon': '🌳',
                    'risk_note': 'Area esterna da considerare'
                },
                'trees_near_roof': {
                    'detected': (client_hash % 7) == 0,
                    'label': 'Alberi vicino al tetto',
                    'icon': '🌲',
                    'risk_note': 'Potenziale rischio danni'
                },
                'garage': {
                    'detected': (client_hash % 4) == 0,
                    'label': 'Garage',
                    'icon': '🚗',
                    'risk_note': 'Struttura aggiuntiva'
                }
            }

            # Two-column layout: Image + Features
            cv_col1, cv_col2 = st.columns([1, 1])

            with cv_col1:
                # Satellite image placeholder
                st.markdown(f"""
                <div class="glass-card" style="text-align: center; background: #F8FAFC; padding: 2rem; height: 280px; display: flex; flex-direction: column; justify-content: center;">
                    <p style="color: #94A3B8; font-size: 3rem; margin: 0;">🗺️</p>
                    <p style="color: #64748B; font-size: 0.85rem; margin-top: 0.5rem;">
                        Vista satellitare dell'abitazione
                    </p>
                    <p style="color: #94A3B8; font-size: 0.75rem; margin-top: 0.25rem;">
                        Lat: {lat:.4f}, Lon: {lon:.4f}
                    </p>
                </div>
                """, unsafe_allow_html=True)

            with cv_col2:
                st.markdown("""
                <div class="glass-card" style="padding: 1rem;">
                    <p style="color: #94A3B8; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.75rem; font-weight: 600;">
                        Caratteristiche rilevate
                    </p>
                """, unsafe_allow_html=True)

                for feature_key, feature in cv_features.items():
                    if feature['detected']:
                        icon = "✅"
                        color = "#10B981"
                        status = "Rilevato"
                    else:
                        icon = "—"
                        color = "#CBD5E1"
                        status = "Non rilevato"

                    # Special case for trees (warning)
                    if feature_key == 'trees_near_roof' and feature['detected']:
                        icon = "⚠️"
                        color = "#F59E0B"
                        status = "Attenzione"

                    st.markdown(f"""
                    <div style="display: flex; justify-content: space-between; align-items: center; padding: 0.5rem 0; border-bottom: 1px solid #F1F5F9;">
                        <span style="color: #1B3A5F; font-size: 0.85rem;">
                            {feature['icon']} {feature['label']}
                        </span>
                        <span style="color: {color}; font-size: 0.75rem; font-weight: 500;">
                            {icon} {status}
                        </span>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown("</div>", unsafe_allow_html=True)

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
            st.dataframe(df_recs, use_container_width=True, hide_index=True)

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
            codice_cliente_ada = client_data['codice_cliente']
            nome_completo = f"{client_data['anagrafica']['nome']} {client_data['anagrafica']['cognome']}"

            # Build context string
            client_context = f"""Cliente: {nome_completo} ({codice_cliente_ada})
CLV Stimato: €{client_data['metadata']['clv_stimato']:,}
Polizze Attuali: {client_data['metadata']['num_polizze_attuali']}
Prodotto Raccomandato: {recommendation['prodotto']}
Area Bisogno: {recommendation['area_bisogno']}
Score Raccomandazione: {calculate_recommendation_score(recommendation, st.session_state.nbo_weights):.1f}
Retention Gain: {recommendation['componenti']['retention_gain']:.1f}%
Propensione: {recommendation['componenti']['propensione']:.1f}%"""

            # Generate email draft button
            if st.button("✍️ Genera Bozza Email con ADA", type="primary", use_container_width=True, key="generate_email_draft"):
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
6. Sia firmata da {st.session_state.user_name} di Vita Sicura
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
                        st.session_state.current_draft_client = codice_cliente_ada
                        st.success("✅ Bozza email generata con successo!")
                        st.rerun()
                    else:
                        st.error("❌ Errore nella generazione della bozza email. Riprova.")

            # Show email draft if available
            if st.session_state.current_draft_client == codice_cliente_ada and st.session_state.client_email_draft:
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
                        placeholder="es. 'rendila piu formale', 'aggiungi urgenza'",
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
            # POLICY ADVISOR MAIN VIEW
            # ═══════════════════════════════════════════════════════════════════════════════

            # Get all recommendations with current weights
            all_recs = get_all_recommendations(nbo_data, st.session_state.nbo_weights)
            weights = st.session_state.nbo_weights

            # ═══════════════════════════════════════════════════════════════════════════════
            # STRATEGY HEADER CARD
            # ═══════════════════════════════════════════════════════════════════════════════

            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #F8FAFC 0%, #EFF6FF 100%); border: 1px solid #E2E8F0; border-radius: 12px; padding: 1rem 1.5rem; margin-bottom: 1.5rem; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem;">
                <div>
                    <p style="margin: 0; font-family: 'Inter', sans-serif; font-size: 0.7rem; font-weight: 600; color: #64748B; text-transform: uppercase; letter-spacing: 0.05em;">Strategia Attiva</p>
                    <p style="margin: 0.25rem 0 0; font-family: 'Playfair Display', serif; font-size: 1.25rem; font-weight: 600; color: #1B3A5F;">Q1 2026 - Focus Retention</p>
                </div>
                <div style="display: flex; gap: 1.5rem; align-items: center;">
                    <div style="text-align: center;">
                        <p style="margin: 0; font-size: 0.65rem; color: #94A3B8; text-transform: uppercase;">Retention</p>
                        <p style="margin: 0; font-family: 'JetBrains Mono', monospace; font-size: 1.1rem; font-weight: 600; color: #00A0B0;">{int(weights['retention']*100)}%</p>
                    </div>
                    <div style="width: 1px; height: 30px; background: #E2E8F0;"></div>
                    <div style="text-align: center;">
                        <p style="margin: 0; font-size: 0.65rem; color: #94A3B8; text-transform: uppercase;">Redditivita</p>
                        <p style="margin: 0; font-family: 'JetBrains Mono', monospace; font-size: 1.1rem; font-weight: 600; color: #F59E0B;">{int(weights['redditivita']*100)}%</p>
                    </div>
                    <div style="width: 1px; height: 30px; background: #E2E8F0;"></div>
                    <div style="text-align: center;">
                        <p style="margin: 0; font-size: 0.65rem; color: #94A3B8; text-transform: uppercase;">Propensione</p>
                        <p style="margin: 0; font-family: 'JetBrains Mono', monospace; font-size: 1.1rem; font-weight: 600; color: #8B5CF6;">{int(weights['propensione']*100)}%</p>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # ═══════════════════════════════════════════════════════════════════════════════
            # SECTION 1: TOP 5 PREMIUM CLIENTS
            # ═══════════════════════════════════════════════════════════════════════════════

            st.markdown("""
            <h2 style="font-family: 'Playfair Display', serif; color: #1B3A5F; font-size: 1.5rem; margin-bottom: 0.5rem;">
                I tuoi clienti piu preziosi
            </h2>
            <p style="color: #64748B; font-size: 0.9rem; margin-bottom: 1.5rem;">
                Clienti con alto valore e le migliori opportunita di vendita
            </p>
            """, unsafe_allow_html=True)

            # Get premium clients
            premium_clients = get_premium_clients(nbo_data, st.session_state.nbo_weights, top_n=5)

            if premium_clients:
                # Display as 5 horizontal cards using native Streamlit
                premium_cols = st.columns(5)

                for idx, rec in enumerate(premium_clients):
                    with premium_cols[idx]:
                        client = rec['client_data']
                        score_display = get_score_display(rec['score'])
                        clv = client['metadata']['clv_stimato']

                        # Get policies as HTML icons
                        policies = client['metadata'].get('prodotti_posseduti', [])
                        if isinstance(policies, str):
                            policies = [policies]
                        policy_icons = render_policy_icons(policies)

                        # Card container
                        with st.container():
                            st.markdown(f"**#{idx + 1}** 🏆")
                            st.markdown(f"**{rec['nome']} {rec['cognome']}**")

                            # Progress bar for score
                            score_pct = min(rec['score'] / 100, 1.0)
                            st.progress(score_pct, text=f"{score_display['label']} ({rec['score']:.0f})")

                            st.caption(f"💰 CLV: €{clv:,}")
                            st.markdown(f"📋 {policy_icons}", unsafe_allow_html=True)

                            if st.button("Dettagli", key=f"premium_{idx}", use_container_width=True):
                                st.session_state.nbo_page = 'detail'
                                st.session_state.nbo_selected_client = client
                                st.session_state.nbo_selected_recommendation = rec['recommendation']
                                st.rerun()
            else:
                st.info("Nessun cliente premium trovato con i criteri attuali.")

            st.divider()

            # ═══════════════════════════════════════════════════════════════════════════════
            # SECTION 2: TOP 20 OPPORTUNITIES
            # ═══════════════════════════════════════════════════════════════════════════════

            st.subheader("📋 Le migliori opportunità di vendita")
            st.caption("Raccomandazioni ordinate per potenziale, già filtrate per eleggibilità commerciale")

            st.info("ℹ️ Esclusi clienti con interazioni recenti (email, chiamate, polizze, reclami, sinistri)", icon="ℹ️")

            # Display Top 20 using native Streamlit components
            for i, rec in enumerate(all_recs[:20]):
                client = rec['client_data']
                score_display = get_score_display(rec['score'])

                # Get policies as HTML icons
                policies = client['metadata'].get('prodotti_posseduti', [])
                if isinstance(policies, str):
                    policies = [policies]
                policy_icons = render_policy_icons(policies)

                col_num, col_name, col_product, col_score, col_policies, col_btn = st.columns([0.5, 2, 2, 1.5, 1, 1])

                with col_num:
                    st.markdown(f"**{i+1}**")

                with col_name:
                    st.markdown(f"**{rec['nome']} {rec['cognome']}**")

                with col_product:
                    st.caption(rec['prodotto'])

                with col_score:
                    score_pct = min(rec['score'] / 100, 1.0)
                    st.progress(score_pct, text=score_display['label'])

                with col_policies:
                    st.markdown(policy_icons, unsafe_allow_html=True)

                with col_btn:
                    if st.button("👁️", key=f"top20_{i}", help="Vedi dettagli"):
                        st.session_state.nbo_page = 'detail'
                        st.session_state.nbo_selected_client = client
                        st.session_state.nbo_selected_recommendation = rec['recommendation']
                        st.rerun()

            # Count by area (for analytics tab)
            area_counts = {}
            for rec in all_recs:
                area = rec['area_bisogno']
                area_counts[area] = area_counts.get(area, 0) + 1

            total_clients = len(nbo_data)
            total_recs = len(all_recs)

            # Hidden tabs for Analytics and Search (keep functionality but collapse)
            with st.expander("📊 Analytics e Ricerca Avanzata", expanded=False):
                nbo_tab2, nbo_tab3 = st.tabs([
                    "📊 Analytics NBO",
                    "🔍 Ricerca Clienti"
                ])

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

                        st.plotly_chart(fig_area, use_container_width=True)

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

                        st.plotly_chart(fig_score, use_container_width=True)

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

                    st.plotly_chart(fig_products, use_container_width=True)

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
                            if st.button("Vedi", key=f"client_{client['codice_cliente']}", use_container_width=True):
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
