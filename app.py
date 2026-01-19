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
from src.iris.chat import render_iris_chat
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
    insert_phone_call_interaction,
    get_client_detail
)

import random
import hashlib

# ═══════════════════════════════════════════════════════════════════════════════
# FUNZIONE COEFFICIENTI ATTUARIALI (simulati ma realistici)
# ═══════════════════════════════════════════════════════════════════════════════

def genera_coefficienti_polizza(cliente_meta: dict, tipo_polizza: str, codice_cliente: str = None) -> dict | None:
    """
    Genera coefficienti attuariali realistici per polizze CASA e SALUTE.
    Usa un seed deterministico basato sul codice cliente per consistenza.

    Loss ratio target:
    - Casa: 65% (-10% rispetto a standard)
    - Salute: 24%

    Ritorna None per polizze non supportate (Vita, Pensione, etc.)
    """
    tipo_lower = tipo_polizza.lower()

    # Solo Casa e Salute sono supportate
    is_casa = 'casa' in tipo_lower or 'abitazione' in tipo_lower
    is_salute = 'salute' in tipo_lower or 'infortuni' in tipo_lower

    if not is_casa and not is_salute:
        return None

    # Seed deterministico per consistenza
    seed_str = f"{codice_cliente}_{tipo_polizza}" if codice_cliente else tipo_polizza
    seed = int(hashlib.md5(seed_str.encode()).hexdigest()[:8], 16)
    rng = random.Random(seed)

    # Estrai dati cliente
    eta = cliente_meta.get('eta', 45)
    if isinstance(eta, str):
        try:
            eta = int(eta)
        except:
            eta = 45

    metratura = cliente_meta.get('metratura', 100)
    if isinstance(metratura, str):
        try:
            metratura = int(metratura)
        except:
            metratura = 100

    zona_sismica = cliente_meta.get('zona_sismica', 3)
    if isinstance(zona_sismica, str):
        try:
            zona_sismica = int(zona_sismica)
        except:
            zona_sismica = 3

    # Loading standard
    loading = 0.30

    if is_casa:
        # Polizza Casa/Abitazione - Loss Ratio Target: 65%
        loss_ratio_target = 0.65
        loss_ratio_label = "65% (-10%)"

        # Frequenza base: 1.5% - 4% annuo
        freq_base = 0.015 + (metratura / 15000) + (4 - zona_sismica) * 0.005
        freq_base += rng.uniform(-0.005, 0.012)
        freq_base = max(0.008, min(0.06, freq_base))

        # Severità: €500 - €5000 per sinistro medio
        sev_base = 600 + metratura * 6 + (4 - zona_sismica) * 200
        sev_base += rng.uniform(-150, 400)
        sev_base = max(400, min(8000, sev_base))

    else:  # is_salute
        # Polizza Salute/Infortuni - Loss Ratio Target: 24%
        loss_ratio_target = 0.24
        loss_ratio_label = "24%"

        # Frequenza: 5% - 15% annuo (più frequente ma meno severa)
        freq_base = 0.05 + (eta / 1000)
        freq_base += rng.uniform(-0.02, 0.05)
        freq_base = max(0.03, min(0.20, freq_base))

        # Severità: €200 - €3000 per sinistro
        sev_base = 300 + eta * 15
        sev_base += rng.uniform(-100, 500)
        sev_base = max(150, min(5000, sev_base))

    # Calcoli premio
    premio_puro = freq_base * sev_base
    premio_tecnico = premio_puro * (1 + loading) / loss_ratio_target

    # Simula premio pagato (può essere sopra o sotto il tecnico)
    gap_factor = rng.uniform(-0.25, 0.35)  # -25% a +35%
    premio_pagato = premio_tecnico * (1 + gap_factor)

    gap_assoluto = premio_pagato - premio_tecnico
    gap_relativo = (gap_assoluto / premio_tecnico) * 100 if premio_tecnico > 0 else 0

    return {
        'premio_tecnico': premio_tecnico,
        'premio_pagato': premio_pagato,
        'gap_assoluto': gap_assoluto,
        'gap_relativo_perc': gap_relativo,
        'loss_ratio_label': loss_ratio_label,
        'tipo': 'casa' if is_casa else 'salute'
    }

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
        transform: translateY(-2px);
        box-shadow: var(--shadow-lg);
        border-color: var(--vs-border-accent);
    }

    [data-testid="stMetric"]:hover::before {
        opacity: 1;
    }

    /* ═══════════════════════════════════════════════════════════════════════
       UNIFIED HTML CARD STYLING & BUTTON HACKS
    ═══════════════════════════════════════════════════════════════════════ */

    /* Fix: Allinea colonne Streamlit in alto invece di stretch */
    [data-testid="stHorizontalBlock"] {
        align-items: flex-start !important;
    }

    /* Standard Card Definition */
    .standard-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 16px;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
        padding: 1.5rem;
        margin-bottom: 1rem;
        height: 100%; /* For grid uniformity */
        display: flex;
        flex-direction: column;
    }
    
    /* Card meant to have a button attached at bottom */
    .card-with-button {
        border-bottom-left-radius: 0 !important;
        border-bottom-right-radius: 0 !important;
        border-bottom: none !important;
        margin-bottom: 0 !important;
        padding-bottom: 2rem !important; /* Visual breathing room */
    }

    /* Target the button immediately following our custom card 
       Note: This is tricky in Streamlit. We will use a specific class wrapper or rely on adjacency.
       For now, we will use a specific hack: 
       If a button is inside a container that follows our card... 
       Actually, standard Streamlit buttons have margin. We need to override.
    */
    
    /* Specific overrides for "Attached" buttons */
    div[data-testid="stButton"] button.attached-button {
        border-top-left-radius: 0 !important;
        border-top-right-radius: 0 !important;
        border-top: 1px solid #E2E8F0 !important; /* Re-add border that was missing from card */
        margin-top: 0 !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); /* Restore shadow for the bottom part */
    }

    /* Helper utility for grid */
    .grid-box-content {
        flex: 1;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    
    /* Remove native container styling if we revert to HTML cards */
    [data-testid="stVerticalBlockBorderWrapper"] {
        border: none !important;
        box-shadow: none !important;
        background: transparent !important;
        padding: 0 !important;
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
        font-weight: 600 !important;
        font-size: 0.875rem !important;
        background: linear-gradient(135deg, var(--vs-teal) 0%, var(--vs-cyan) 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.75rem 1.5rem !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 0 4px 6px -1px rgba(0, 160, 176, 0.25) !important;
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow-lg), var(--glow-teal) !important;
        color: white !important;
    }

    .stButton > button:active {
        transform: translateY(0);
        color: white !important;
    }

    /* Primary button - ensure white text - FORCE override Streamlit defaults */
    .stButton > button[kind="primary"],
    .stButton > button[data-testid="stBaseButton-primary"],
    .stButton > button:not([kind="secondary"]):not([data-testid="stBaseButton-secondary"]) {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
    }
    .stButton > button[kind="primary"] p,
    .stButton > button[data-testid="stBaseButton-primary"] p,
    .stButton > button:not([kind="secondary"]):not([data-testid="stBaseButton-secondary"]) p {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
    }

    /* Secondary button style (ghost/link style) */
    .stButton > button[kind="secondary"],
    .stButton > button[data-testid="stBaseButton-secondary"] {
        background: transparent !important;
        color: var(--vs-text-secondary) !important;
        border: none !important;
        box-shadow: none !important;
        padding: 0.5rem 0 !important;
        font-weight: 500 !important;
    }
    .stButton > button[kind="secondary"]:hover,
    .stButton > button[data-testid="stBaseButton-secondary"]:hover {
        background: transparent !important;
        color: var(--vs-teal) !important;
        transform: none !important;
        box-shadow: none !important;
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

    /* ═══════════════════════════════════════════════════════════════════════
       CLIENT DETAIL REDESIGN - New Components
    ═══════════════════════════════════════════════════════════════════════ */

    /* Top Navigation Bar */
    .client-nav-bar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1.5rem;
        padding: 0;
    }

    /* Back Button - Secondary/Ghost style */
    .back-btn-link {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        color: var(--vs-text-secondary);
        font-size: 0.9rem;
        font-weight: 500;
        text-decoration: none;
        padding: 0.5rem 0;
        transition: all 0.2s ease;
        cursor: pointer;
        background: none;
        border: none;
    }
    .back-btn-link:hover {
        color: var(--vs-teal);
    }
    .back-btn-link .arrow {
        font-size: 1.1rem;
        transition: transform 0.2s ease;
    }
    .back-btn-link:hover .arrow {
        transform: translateX(-3px);
    }

    /* Call Action Button - Primary CTA */
    .call-action-btn {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        background: linear-gradient(135deg, var(--vs-teal) 0%, var(--vs-cyan) 100%);
        color: white;
        font-size: 0.9rem;
        font-weight: 600;
        padding: 0.75rem 1.25rem;
        border-radius: 12px;
        border: none;
        cursor: pointer;
        transition: all 0.2s ease;
        box-shadow: 0 2px 8px rgba(0, 160, 176, 0.25);
    }
    .call-action-btn:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0, 160, 176, 0.35);
    }

    /* Iris AI Assistant Card - Wrapper includes button visually */
    .iris-outer-wrapper {
        background: white;
        border: 1px solid var(--vs-teal);
        border-radius: 16px;
        margin: 1rem 0;
        overflow: hidden;
    }
    .iris-card-header {
        display: flex;
        align-items: center;
        gap: 1rem;
        padding: 1.25rem 1.5rem;
    }
    .iris-icon-wrapper {
        width: 44px;
        height: 44px;
        border-radius: 12px;
        background: linear-gradient(135deg, rgba(0, 160, 176, 0.1) 0%, rgba(0, 201, 212, 0.05) 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
    }
    .iris-icon-wrapper svg {
        width: 24px;
        height: 24px;
        color: var(--vs-teal);
    }
    .iris-content {
        flex: 1;
    }
    .iris-title {
        margin: 0;
        font-size: 0.95rem;
        font-weight: 600;
        color: var(--vs-navy);
    }
    .iris-subtitle {
        margin: 0.15rem 0 0 0;
        font-size: 0.8rem;
        color: var(--vs-text-secondary);
    }
    /* Style for button container inside iris wrapper */
    .iris-button-container {
        padding: 0 1.5rem 1.25rem 1.5rem;
    }
    .iris-button-container .stButton > button {
        border-radius: 12px !important;
        width: 100%;
    }

    /* Client Header Card - Better Alignment */
    .client-header-card {
        background: white;
        border: 1px solid var(--vs-border);
        border-radius: 20px;
        padding: 1.75rem 2rem;
        margin-bottom: 1.5rem;
        box-shadow: var(--shadow-md);
    }
    .client-header-top {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 1.5rem;
    }
    .client-header-left {
        flex: 1;
    }
    .client-header-right {
        text-align: right;
        flex-shrink: 0;
    }
    .client-name {
        margin: 0;
        font-size: 1.75rem;
        font-weight: 700;
        color: var(--vs-navy);
        line-height: 1.2;
    }
    .client-id-location {
        margin: 0.5rem 0 0 0;
        color: var(--vs-text-secondary);
        font-size: 0.9rem;
        display: flex;
        align-items: center;
        gap: 0.35rem;
    }
    .client-id-location .pin-icon {
        color: #EF4444;
    }
    .client-stats-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 1.5rem;
        margin-top: 1.5rem;
        padding-top: 1.5rem;
        border-top: 1px solid var(--vs-border);
    }

    /* ═══════════════════════════════════════════════════════════════════════
       POLICY ADVISOR REDESIGN
    ═══════════════════════════════════════════════════════════════════════ */

    /* Top 5 Cards Grid */
    .top5-grid {
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 1rem;
        margin-bottom: 2rem;
    }

    .top5-card {
        background: linear-gradient(180deg, #FFFFFF 0%, #FAFAFA 100%);
        border: 1px solid #E2E8F0;
        border-radius: 16px;
        padding: 1.25rem;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
        height: 100%;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }

    .top5-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
        border-color: #00A0B0;
    }

    .top5-rank {
        position: absolute;
        top: 0;
        right: 0;
        background: linear-gradient(135deg, #00A0B0 0%, #00C9D4 100%);
        color: white;
        padding: 0.25rem 0.75rem;
        border-bottom-left-radius: 12px;
        font-family: 'JetBrains Mono', monospace;
        font-weight: 700;
        font-size: 0.8rem;
    }

    .top5-header {
        margin-bottom: 1rem;
    }

    .top5-name {
        font-family: 'Inter', sans-serif;
        font-weight: 700;
        color: #1B3A5F;
        font-size: 1rem;
        line-height: 1.3;
        margin-bottom: 0.25rem;
        padding-right: 1.5rem; /* Space for rank */
    }

    .top5-client-code {
        color: #64748B;
        font-size: 0.75rem;
        font-family: 'JetBrains Mono', monospace;
    }

    .top5-stat {
        margin: 0.75rem 0;
        padding: 0.5rem;
        background: #F1F5F9;
        border-radius: 8px;
        text-align: center;
    }
    
    .top5-stat-label {
        font-size: 0.65rem;
        text-transform: uppercase;
        color: #64748B;
        font-weight: 600;
        letter-spacing: 0.05em;
    }
    
    .top5-stat-value {
        font-size: 1.1rem;
        font-weight: 700;
        color: #1B3A5F;
    }
    .client-stat-item {
        text-align: center;
    }
    .client-stat-label {
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: var(--vs-text-muted);
        margin: 0;
        font-weight: 500;
    }
    .client-stat-value {
        font-size: 1.35rem;
        font-weight: 700;
        color: var(--vs-navy);
        font-family: 'JetBrains Mono', monospace;
        margin: 0.35rem 0 0 0;
    }
    .client-stat-value.teal { color: var(--vs-teal); }
    .client-stat-value.success { color: #10B981; }
    .client-stat-value.warning { color: #F59E0B; }

    /* Info Grid */
    .info-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 0.75rem;
    }
    .info-item {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        padding: 0.75rem 1rem;
        background: var(--vs-gray-light);
        border-radius: 12px;
    }
    .info-icon {
        font-size: 1.1rem;
        width: 24px;
        text-align: center;
    }
    .info-label {
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 0.03em;
        color: var(--vs-text-muted);
        margin: 0;
    }
    .info-value {
        font-size: 0.9rem;
        font-weight: 600;
        color: var(--vs-navy);
        margin: 0;
    }

    /* Product Cards */
    .product-card {
        background: white;
        border: 1px solid var(--vs-border);
        border-radius: 16px;
        padding: 1rem 1.25rem;
        margin-bottom: 0.75rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
        transition: all 0.2s ease;
    }
    .product-card:hover {
        border-color: var(--vs-teal);
        box-shadow: var(--shadow-md);
    }
    .product-info {
        display: flex;
        align-items: center;
        gap: 1rem;
    }
    .product-icon {
        width: 40px;
        height: 40px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.25rem;
    }
    .product-icon.casa { background: #DBEAFE; }
    .product-icon.vita { background: #D1FAE5; }
    .product-icon.salute { background: #FCE7F3; }
    .product-icon.pensione { background: #FEF3C7; }
    .product-name {
        font-weight: 600;
        color: var(--vs-navy);
        font-size: 0.9rem;
        margin: 0;
    }
    .product-badge {
        background: #D1FAE5;
        color: #059669;
        padding: 0.25rem 0.75rem;
        border-radius: 100px;
        font-size: 0.7rem;
        font-weight: 600;
        text-transform: uppercase;
    }

    /* Recommendation Hero Card */
    .recommendation-hero {
        background: linear-gradient(135deg, rgba(0, 160, 176, 0.05) 0%, rgba(16, 185, 129, 0.03) 100%);
        border: 2px solid var(--vs-teal);
        border-radius: 20px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    .rec-product-badge {
        display: inline-block;
        background: linear-gradient(135deg, var(--vs-teal), var(--vs-cyan));
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 6px;
        font-size: 0.65rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.75rem;
    }
    .rec-product-name {
        font-size: 1.3rem;
        font-weight: 700;
        color: var(--vs-navy);
        margin: 0 0 0.25rem 0;
    }
    .rec-area {
        font-size: 0.85rem;
        color: var(--vs-text-secondary);
        margin: 0 0 1rem 0;
    }
    .score-bars {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 1rem;
    }
    .score-bar-item {
        background: white;
        border-radius: 12px;
        padding: 0.75rem 1rem;
    }
    .score-bar-label {
        font-size: 0.7rem;
        text-transform: uppercase;
        color: var(--vs-text-muted);
        margin: 0 0 0.5rem 0;
    }
    .score-bar-track {
        height: 8px;
        background: var(--vs-gray-light);
        border-radius: 100px;
        overflow: hidden;
    }
    .score-bar-fill {
        height: 100%;
        border-radius: 100px;
        background: linear-gradient(90deg, var(--vs-teal), var(--vs-cyan));
    }
    .score-bar-value {
        font-size: 0.85rem;
        font-weight: 700;
        color: var(--vs-navy);
        margin: 0.25rem 0 0 0;
    }

    /* Status Chips (Interactions) */
    .status-chips {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
    }
    .status-chip {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        padding: 0.4rem 0.75rem;
        border-radius: 100px;
        font-size: 0.75rem;
        font-weight: 500;
    }
    .status-chip.ok {
        background: #D1FAE5;
        color: #059669;
    }
    .status-chip.warning {
        background: #FEE2E2;
        color: #DC2626;
    }
    .status-chip-icon {
        font-size: 0.85rem;
    }

    /* CV Badges */
    .cv-badges {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
    }
    .cv-badge {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.6rem 1rem;
        border-radius: 12px;
        font-size: 0.85rem;
        font-weight: 500;
    }
    .cv-badge.detected {
        background: #D1FAE5;
        color: #059669;
        border: 1px solid #A7F3D0;
    }
    .cv-badge.not-detected {
        background: #F3F4F6;
        color: #6B7280;
        border: 1px solid #E5E7EB;
    }
    .cv-badge-icon {
        font-size: 1.1rem;
    }

    /* Recommendation Cards (List) */
    .rec-card {
        background: white;
        border: 1px solid var(--vs-border);
        border-radius: 16px;
        padding: 1rem 1.25rem;
        margin-bottom: 0.75rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
        transition: all 0.2s ease;
    }
    .rec-card:hover {
        border-color: var(--vs-teal);
        box-shadow: var(--shadow-md);
        transform: translateY(-1px);
    }
    .rec-rank {
        width: 32px;
        height: 32px;
        border-radius: 10px;
        background: linear-gradient(135deg, var(--vs-teal), var(--vs-cyan));
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        font-size: 0.85rem;
    }
    .rec-details {
        flex: 1;
        margin-left: 1rem;
    }
    .rec-product {
        font-weight: 600;
        color: var(--vs-navy);
        font-size: 0.9rem;
        margin: 0;
    }
    .rec-area-small {
        font-size: 0.75rem;
        color: var(--vs-text-muted);
        margin: 0.15rem 0 0 0;
    }
    .rec-score {
        text-align: right;
    }
    .rec-score-value {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.1rem;
        font-weight: 700;
    }
    .rec-score-value.high { color: #10B981; }
    .rec-score-value.medium { color: #F59E0B; }
    .rec-score-value.low { color: #EF4444; }
    .rec-score-label {
        font-size: 0.65rem;
        text-transform: uppercase;
        color: var(--vs-text-muted);
        margin: 0;
    }

    /* Section Headers */
    .section-header {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin: 1.5rem 0 0.75rem 0;
    }
    .section-icon {
        font-size: 1.1rem;
    }
    .section-title {
        margin: 0;
        font-size: 1.1rem;
        font-weight: 700;
        color: var(--vs-navy);
    }

    /* Uniform Glass Card for all sections */
    .glass-card {
        background: white;
        border: 1px solid var(--vs-border);
        border-radius: 16px;
        padding: 1.25rem;
        box-shadow: var(--shadow-sm);
    }

    /* Two Column Layout - Equal Heights */
    .column-section {
        display: flex;
        flex-direction: column;
        height: 100%;
    }
    .column-section .glass-card {
        flex: 1;
        margin-bottom: 0;
    }

    /* Abitazione Card - Flexible Layout for Variable Image Sizes */
    .abitazione-card {
        background: white;
        border: 1px solid var(--vs-border);
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: var(--shadow-sm);
    }
    .abitazione-layout {
        display: flex;
        gap: 2rem;
        align-items: stretch;
    }
    .satellite-container {
        flex: 0 0 300px;
        min-width: 200px;
    }
    .satellite-preview {
        background: var(--vs-gray-light);
        border-radius: 12px;
        padding: 2rem;
        text-align: center;
        min-height: 180px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
    }
    .satellite-preview.has-image {
        padding: 0;
        overflow: hidden;
        min-height: auto;
    }
    .satellite-preview.has-image img {
        width: 100%;
        height: auto;
        max-height: 250px;
        object-fit: cover;
        border-radius: 12px;
    }
    .satellite-preview .icon {
        font-size: 3.5rem;
        margin-bottom: 0.75rem;
    }
    .satellite-preview .label {
        font-size: 0.95rem;
        color: var(--vs-text-secondary);
        margin: 0;
        font-weight: 500;
    }
    .satellite-preview .coords {
        font-size: 0.75rem;
        color: var(--vs-text-muted);
        margin: 0.5rem 0 0 0;
        font-family: 'JetBrains Mono', monospace;
    }
    .cv-features {
        flex: 1;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    .cv-section-title {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: var(--vs-text-muted);
        margin: 0 0 1rem 0;
        font-weight: 600;
    }

    /* Recommendations List - Clearer Design */
    .recommendations-section {
        background: white;
        border: 1px solid var(--vs-border);
        border-radius: 16px;
        padding: 1.25rem;
        box-shadow: var(--shadow-sm);
    }
    .rec-list-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding-bottom: 0.75rem;
        border-bottom: 1px solid var(--vs-border);
        margin-bottom: 0.75rem;
    }
    .rec-list-title {
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: var(--vs-text-muted);
        margin: 0;
        font-weight: 500;
    }
    .rec-card {
        background: white;
        border: 1px solid var(--vs-border);
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 0.5rem;
        display: flex;
        align-items: center;
        gap: 1rem;
        transition: all 0.2s ease;
    }
    .rec-card:last-child {
        margin-bottom: 0;
    }
    .rec-card:hover {
        border-color: var(--vs-teal);
        background: rgba(0, 160, 176, 0.02);
    }

    /* Four Equal Boxes Grid */
    .four-box-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 1rem;
        margin: 1rem 0;
    }
    .grid-box {
        background: white;
        border: 1px solid var(--vs-border);
        border-radius: 16px;
        padding: 1.25rem;
        box-shadow: var(--shadow-sm);
        min-height: 200px;
        display: flex;
        flex-direction: column;
    }
    .box-header {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin-bottom: 1rem;
        padding-bottom: 0.75rem;
        border-bottom: 1px solid var(--vs-border);
    }
    .box-icon {
        font-size: 1.1rem;
    }
    .box-title {
        margin: 0;
        font-size: 1rem;
        font-weight: 600;
        color: var(--vs-navy);
    }
    .box-content {
        flex: 1;
    }
    .recommendation-content .rec-product-badge {
        margin-bottom: 0.5rem;
    }
    .recommendation-content .rec-product-name {
        font-size: 1rem;
        margin: 0.5rem 0 0.25rem 0;
    }
    .recommendation-content .rec-area {
        font-size: 0.8rem;
        margin-bottom: 0.75rem;
    }
    .recommendation-content .score-bars {
        gap: 0.5rem;
    }
    .recommendation-content .score-bar-item {
        padding: 0.5rem 0.75rem;
    }

    /* Responsive: Stack on mobile */
    @media (max-width: 768px) {
        .four-box-grid {
            grid-template-columns: 1fr;
        }
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
        retention_gain * w_retention +
        redditivita * w_redditivita +
        propensione * w_propensione
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
    
    Optimized to only check interactions for top-scoring candidates when filtering for Top 20,
    reducing DB queries from thousands to dozens.

    Args:
        data: Client data with recommendations
        weights: Scoring weights
        filter_top20: If True, filter out clients not eligible for Top 20

    Returns:
        List of recommendations sorted by score (descending)
    """
    # STEP 1: Score ALL clients first (no DB queries, just calculations)
    all_recs = []
    for client in data:
        codice_cliente = client['codice_cliente']
        # Initialize eligibility flags (updated later if filter_top20)
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
    
    # STEP 2: If filtering for Top 20, only check interactions for top candidates
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
                if len(top_candidates) >= 100:  # Check only top 100 clients instead of all 11k+
                    break
        
        # Batch check only these top candidates (3 queries for 100 clients instead of thousands)
        batch_interactions = check_all_clients_interactions_batch(top_candidates)
        
        # Filter out ineligible clients and update their flags
        filtered_recs = []
        for rec in all_recs:
            cc = rec['codice_cliente']
            client = rec['client_data']
            
            if cc in batch_interactions:
                indicators = batch_interactions[cc]
                is_eligible = not any(indicators.values())  # Eligible if NO interactions
                client['_is_eligible_top20'] = is_eligible
                client['_interaction_indicators'] = indicators
                
                if is_eligible:
                    filtered_recs.append(rec)
            else:
                # Client wasn't in top candidates, include them (they're lower scored anyway)
                filtered_recs.append(rec)
        
        return filtered_recs
    else:
        # No filtering needed
        return all_recs


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

# Iris integration
if 'iris_auto_prompt' not in st.session_state:
    st.session_state.iris_auto_prompt = None

# User info (for login - to be implemented)
if 'user_name' not in st.session_state:
    st.session_state.user_name = "Agente Vita Sicura"  # Default until login is implemented
if 'user_email' not in st.session_state:
    st.session_state.user_email = "agente@vitasicura.it"  # Default until login is implemented
if 'user_phone' not in st.session_state:
    st.session_state.user_phone = "+39 02 1234 5678"  # Default until login is implemented

# Dashboard mode (renamed: Helios View -> Analytics, Helios NBO -> Policy Advisor)
if 'dashboard_mode' not in st.session_state:
    st.session_state.dashboard_mode = 'Analytics'

# Initialize Analytics Sub-navigation
if 'analytics_page' not in st.session_state:
    st.session_state.analytics_page = 'dashboard'
if 'analytics_client_id' not in st.session_state:
    st.session_state.analytics_client_id = None

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
# LOAD DATA (needed before sidebar)
# ═══════════════════════════════════════════════════════════════════════════════
df = load_data()

# Initialize filter state if not exists (for Analytics mode)
if 'selected_city' not in st.session_state:
    st.session_state.selected_city = 'Tutte le città'
if 'selected_risk' not in st.session_state:
    st.session_state.selected_risk = 'Tutti i rischi'
if 'selected_zone' not in st.session_state:
    st.session_state.selected_zone = 'Tutte le zone'

# ═══════════════════════════════════════════════════════════════════════════════
# SIDEBAR - ADA CHAT (Always visible)
# ═══════════════════════════════════════════════════════════════════════════════

with st.sidebar:
    # Elegant brand header with full logo
    st.markdown("""
    <div style="text-align: center; padding: 1rem 0 0.75rem;">
        <div style="display: inline-flex; align-items: center; gap: 0.5rem;">
            <svg width="40" height="40" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
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
            <span style="font-family: 'Inter', sans-serif; font-size: 1.75rem; font-weight: 800; background: linear-gradient(135deg, #00A0B0 0%, #00C9D4 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">HELIOS</span>
        </div>
        <p style="font-family: 'Inter', sans-serif; font-size: 0.75rem; color: #94A3B8; letter-spacing: 0.08em; margin-top: 0.15rem; text-transform: uppercase;">Vita Sicura Intelligence</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""<div style="height: 1px; background: linear-gradient(90deg, transparent 0%, #E2E8F0 50%, transparent 100%); margin: 0.5rem 0;"></div>""", unsafe_allow_html=True)

    # Iris Chat Header - elegant card
    # Iris Chat Header - elegant card matching Client Detail aesthetic
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 0.75rem; padding: 0.85rem; background: #FFFFFF; border: 1px solid #00A0B0; border-radius: 16px; margin-bottom: 0.75rem; box-shadow: 0 4px 6px -1px rgba(27, 58, 95, 0.04);">
        <div style="width: 38px; height: 38px; min-width: 38px; min-height: 38px; background: linear-gradient(135deg, rgba(0, 160, 176, 0.1) 0%, rgba(0, 201, 212, 0.05) 100%); border-radius: 12px; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
            <!-- Sparkles Icon to match Client Detail and avoid double sun -->
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#00A0B0" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M12 3c.132 0 .263 0 .393 0a7.5 7.5 0 0 0 7.92 12.446a9 9 0 1 1 -8.313 -12.454z" opacity="0" /> <!-- Hidden sun for spacing if needed, but using sparkles instead -->
                <path d="M9.937 15.5A2 2 0 0 0 8.5 14.063l-6.135-1.582a.5.5 0 0 1 0-.962L8.5 9.936A2 2 0 0 0 9.937 8.5l1.582-6.135a.5.5 0 0 1 .963 0L14.063 8.5A2 2 0 0 0 15.5 9.937l6.135 1.581a.5.5 0 0 1 0 .964L15.5 14.063a2 2 0 0 0-1.437 1.437l-1.582 6.135a.5.5 0 0 1-.963 0z" />
                <path d="M20 3v4" />
                <path d="M22 5h-4" />
                <path d="M4 17v2" />
                <path d="M5 18H3" />
            </svg>
        </div>
        <div style="flex: 1; min-width: 0;">
            <p style="margin: 0; font-family: 'Inter', sans-serif; font-size: 1.05rem; font-weight: 700; color: #1B3A5F; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">Iris</p>
            <p style="margin: 0; font-family: 'Inter', sans-serif; font-size: 0.85rem; color: #64748B; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">Intelligent Advisor</p>
        </div>
        <div style="margin-left: auto; display: flex; align-items: center; gap: 0.35rem; padding: 0.25rem 0.6rem; background: rgba(16, 185, 129, 0.1); border-radius: 100px; flex-shrink: 0;">
            <span style="width: 6px; height: 6px; background: #10B981; border-radius: 50%; animation: pulse 2s infinite;"></span>
            <span style="font-family: 'Inter', sans-serif; font-size: 0.65rem; color: #10B981; font-weight: 600;">Online</span>
        </div>
    </div>
    <style>
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
    </style>
    """, unsafe_allow_html=True)

    # Render Iris chat in sidebar
    render_iris_chat()

    # Elegant footer
    st.markdown("""
    <div style="text-align: center; padding: 1rem 0; margin-top: 1rem; border-top: 1px solid #E2E8F0;">
        <p style="font-family: 'Inter', sans-serif; font-size: 0.65rem; color: #94A3B8; margin: 0;">
            Powered by <strong style="color: #1B3A5F;">Vita Sicura</strong>
        </p>
        <p style="font-family: 'Inter', sans-serif; font-size: 0.6rem; color: #CBD5E1; margin-top: 0.15rem;">
            Helios v2.0 • Generali AI Challenge
        </p>
    </div>
    """, unsafe_allow_html=True)

# Set default for filtered_df based on stored filter state
filtered_df = df.copy()
if st.session_state.selected_city != 'Tutte le città':
    filtered_df = filtered_df[filtered_df['citta'] == st.session_state.selected_city]
if st.session_state.selected_risk != 'Tutti i rischi':
    filtered_df = filtered_df[filtered_df['risk_category'] == st.session_state.selected_risk]
if st.session_state.selected_zone != 'Tutte le zone':
    zone_num = int(st.session_state.selected_zone.split()[-1])
    filtered_df = filtered_df[filtered_df['zona_sismica'] == zone_num]


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN CONTENT
# ═══════════════════════════════════════════════════════════════════════════════

# Dynamic header content based on mode
if st.session_state.dashboard_mode == 'Policy Advisor':
    page_title = "Policy Advisor"
    page_description = "Sistema intelligente di raccomandazioni prodotti per cross-selling e up-selling"
else:
    page_title = "Analytics Dashboard"
    page_description = "Monitoraggio in tempo reale del portafoglio assicurativo territoriale"

# Header with logo - centered layout (restored elegant original style)
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

# Elegant navigation using styled radio buttons
st.markdown("""
<style>
    /* Style the radio button container as elegant pills */
    div[data-testid="stHorizontalBlock"]:has(div[data-testid="stRadio"]) {
        display: flex;
        justify-content: center;
    }

    /* Hide the default radio label */
    div[data-testid="stRadio"] > label {
        display: none !important;
    }

    /* Style the radio options container */
    div[data-testid="stRadio"] > div {
        display: flex !important;
        flex-direction: row !important;
        gap: 0.5rem !important;
        background: #F8FAFC !important;
        padding: 0.35rem !important;
        border-radius: 100px !important;
        border: 1px solid #E2E8F0 !important;
    }

    /* Style each radio option as a pill */
    div[data-testid="stRadio"] > div > label {
        background: transparent !important;
        border: none !important;
        border-radius: 100px !important;
        padding: 0.6rem 1.5rem !important;
        margin: 0 !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 0.875rem !important;
        font-weight: 600 !important;
        color: #64748B !important;
        cursor: pointer !important;
        transition: all 0.2s ease !important;
    }

    /* Hover state for unselected pills */
    div[data-testid="stRadio"] > div > label:hover {
        background: rgba(0, 160, 176, 0.08) !important;
        color: #00A0B0 !important;
    }

    /* Selected/active pill */
    div[data-testid="stRadio"] > div > label[data-checked="true"],
    div[data-testid="stRadio"] > div > label:has(input:checked) {
        background: linear-gradient(135deg, #00A0B0 0%, #00C9D4 100%) !important;
        color: white !important;
        box-shadow: 0 4px 12px rgba(0, 160, 176, 0.25) !important;
    }

    /* Force all text elements inside selected pill to be white */
    div[data-testid="stRadio"] > div > label[data-checked="true"] *,
    div[data-testid="stRadio"] > div > label:has(input:checked) * {
        color: white !important;
    }

    /* Hide the actual radio input */
    div[data-testid="stRadio"] input {
        display: none !important;
    }

    /* Style the text inside radio options */
    div[data-testid="stRadio"] > div > label > div {
        display: flex !important;
        align-items: center !important;
        gap: 0.4rem !important;
    }

    div[data-testid="stRadio"] > div > label > div > p {
        margin: 0 !important;
        font-weight: 600 !important;
    }
</style>

<style>
    /* Active Strategy Card */
    .active-strategy-card {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: #F8FAFF;
        border: 1px solid #E6F0FF;
        border-radius: 16px;
        padding: 1.5rem 2rem;
        margin-bottom: 2rem;
        box-shadow: 0 4px 12px rgba(0, 160, 176, 0.05);
    }

    .strategy-info {
        flex: 1;
    }

    .strategy-label {
        font-size: 0.7rem;
        font-weight: 700;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.25rem;
    }

    .strategy-title {
        font-size: 1.5rem;
        font-weight: 800;
        color: #1B3A5F;
        letter-spacing: -0.01em;
    }

    .strategy-metrics {
        display: flex;
        align-items: center;
        gap: 2rem;
    }

    .metric-item {
        text-align: right;
        min-width: 90px;
    }

    .metric-label {
        font-size: 0.65rem;
        font-weight: 600;
        color: #94A3B8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.15rem;
    }

    .metric-value {
        font-size: 1.5rem;
        font-weight: 800;
        font-family: 'Inter', sans-serif;
    }

    .metric-divider {
        width: 1px;
        height: 40px;
        background: #E2E8F0;
    }
</style>
""", unsafe_allow_html=True)

# Centered navigation
nav_spacer1, nav_center, nav_spacer2 = st.columns([1, 2, 1])

with nav_center:
    dashboard_mode = st.radio(
        "Navigazione",
        ["🎯 Policy Advisor", "📊 Analytics"],
        index=0 if st.session_state.dashboard_mode == 'Policy Advisor' else 1,
        horizontal=True,
        label_visibility="collapsed",
        key="nav_radio"
    )

    # Update session state based on selection
    if "Policy Advisor" in dashboard_mode and st.session_state.dashboard_mode != 'Policy Advisor':
        st.session_state.dashboard_mode = 'Policy Advisor'
        st.rerun()
    elif "Analytics" in dashboard_mode and st.session_state.dashboard_mode != 'Analytics':
        st.session_state.dashboard_mode = 'Analytics'
        st.rerun()

# Divider
st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# CONDITIONAL CONTENT BASED ON DASHBOARD MODE
# ═══════════════════════════════════════════════════════════════════════════════

if st.session_state.dashboard_mode == 'Analytics':
    # ═══════════════════════════════════════════════════════════════════════════════
    # ANALYTICS DETAIL VIEW
    # ═══════════════════════════════════════════════════════════════════════════════
    if st.session_state.analytics_page == 'detail':
        if st.button("← Torna alla Dashboard", key="back_to_analytics", type="secondary"):
            st.session_state.analytics_page = 'dashboard'
            st.session_state.analytics_client_id = None
            st.rerun()
            
        if st.session_state.analytics_client_id:
            with st.spinner("Caricamento scheda cliente..."):
                detail_data = get_client_detail(st.session_state.analytics_client_id)
            
            if "error" in detail_data:
                st.error(f"Errore nel caricamento: {detail_data['error']}")
            else:
                c_info = detail_data.get('cliente', {})
                c_nome = f"{c_info.get('nome','')} {c_info.get('cognome','')}"
                
                st.markdown(f"""
                <div style="margin-bottom: 2rem;">
                    <h1 style="color: #1B3A5F; margin-bottom: 0.5rem;">{c_nome}</h1>
                    <p style="color: #64748B;">📍 {c_info.get('citta', 'N/D')} · {c_info.get('codice_cliente', 'N/D')}</p>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown("### 🌍 Profilo di Rischio")
                
                abitazioni = detail_data.get('abitazioni', [])
                if abitazioni:
                    for ab in abitazioni:
                        r_col1, r_col2, r_col3 = st.columns(3)
                        with r_col1:
                            st.markdown(f"""
                            <div class="glass-card" style="border-left: 4px solid #F59E0B; padding: 1.5rem;">
                                <h4 style="margin:0 0 0.5rem 0; color:#64748B; font-size:0.9rem;">Rischio Sismico</h4>
                                <p style="font-size:1.8rem; font-weight:700; color:#1B3A5F; margin:0;">Zona {ab.get('zona_sismica')}</p>
                                <p style="font-size:0.8rem; color:#94A3B8; margin-top:0.5rem;">Dato ISTAT aggiornato</p>
                            </div>
                            """, unsafe_allow_html=True)
                        with r_col2:
                            st.markdown(f"""
                            <div class="glass-card" style="border-left: 4px solid #3B82F6; padding: 1.5rem;">
                                <h4 style="margin:0 0 0.5rem 0; color:#64748B; font-size:0.9rem;">Idrogeologico</h4>
                                <p style="font-size:1.8rem; font-weight:700; color:#1B3A5F; margin:0;">{ab.get('hydro_risk_p3', 'N/D')}</p>
                                <p style="font-size:0.8rem; color:#94A3B8; margin-top:0.5rem;">Pericolosità P3 Frane</p>
                            </div>
                            """, unsafe_allow_html=True)
                        with r_col3:
                            st.markdown(f"""
                            <div class="glass-card" style="border-left: 4px solid #06B6D4; padding: 1.5rem;">
                                <h4 style="margin:0 0 0.5rem 0; color:#64748B; font-size:0.9rem;">Alluvione</h4>
                                <p style="font-size:1.8rem; font-weight:700; color:#1B3A5F; margin:0;">{ab.get('flood_risk_p3', 'N/D')}</p>
                                <p style="font-size:0.8rem; color:#94A3B8; margin-top:0.5rem;">Pericolosità P3 Alluvioni</p>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        st.markdown("---")
                else:
                    st.info("Nessuna abitazione associata.")

    # ═══════════════════════════════════════════════════════════════════════════════
    # ANALYTICS DASHBOARD VIEW
    # ═══════════════════════════════════════════════════════════════════════════════
    elif st.session_state.analytics_page == 'dashboard':


    # Inline filters - modern pill style
        st.markdown("""
        <style>
            .filter-container {
                background: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 16px;
                padding: 1rem 1.5rem;
                margin-bottom: 1.5rem;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
            }
            .filter-label {
                font-family: 'Inter', sans-serif;
                font-size: 0.65rem;
                font-weight: 600;
                color: #94A3B8;
                text-transform: uppercase;
                letter-spacing: 0.05em;
                margin-bottom: 0.25rem;
            }
        </style>
        """, unsafe_allow_html=True)
    
        # Filter row
        filter_col1, filter_col2, filter_col3, filter_col4 = st.columns([2, 2, 2, 1])
    
        with filter_col1:
            cities_list = ['Tutte le città'] + sorted(df['citta'].unique().tolist())
            selected_city = st.selectbox(
                "📍 Città",
                cities_list,
                index=cities_list.index(st.session_state.selected_city) if st.session_state.selected_city in cities_list else 0,
                key="filter_city"
            )
            if selected_city != st.session_state.selected_city:
                st.session_state.selected_city = selected_city
                st.rerun()
    
        with filter_col2:
            risk_options = ['Tutti i rischi', 'Critico', 'Alto', 'Medio', 'Basso']
            selected_risk = st.selectbox(
                "⚠️ Categoria Rischio",
                risk_options,
                index=risk_options.index(st.session_state.selected_risk) if st.session_state.selected_risk in risk_options else 0,
                key="filter_risk"
            )
            if selected_risk != st.session_state.selected_risk:
                st.session_state.selected_risk = selected_risk
                st.rerun()
    
        with filter_col3:
            zone_options = ['Tutte le zone', 'Zona 1', 'Zona 2', 'Zona 3', 'Zona 4']
            selected_zone = st.selectbox(
                "🌍 Zona Sismica",
                zone_options,
                index=zone_options.index(st.session_state.selected_zone) if st.session_state.selected_zone in zone_options else 0,
                key="filter_zone"
            )
            if selected_zone != st.session_state.selected_zone:
                st.session_state.selected_zone = selected_zone
                st.rerun()
    
        with filter_col4:
            # Quick stats
            st.markdown(f"""
            <div style="text-align: center; padding: 0.5rem;">
                <p style="font-family: 'JetBrains Mono', monospace; font-size: 1.5rem; font-weight: 700; background: linear-gradient(135deg, #00A0B0 0%, #00C9D4 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 0; line-height: 1;">{len(filtered_df):,}</p>
                <p style="font-family: 'Inter', sans-serif; font-size: 0.65rem; color: #94A3B8; margin: 0;">di {len(df):,}</p>
            </div>
            """, unsafe_allow_html=True)
    
        st.markdown("<br>", unsafe_allow_html=True)
    
        # Warning if no results match filters
        if len(filtered_df) == 0:
            st.warning("⚠️ Nessuna abitazione corrisponde ai filtri selezionati. Prova a modificare i criteri nella sidebar.")
    
        # Get stats
        stats = get_risk_stats(filtered_df)
        
        # ═══════════════════════════════════════════════════════════════════════════════
        # KPI METRICS ROW
        # ═══════════════════════════════════════════════════════════════════════════════
        
        col1, col2, col3, col4 = st.columns(4)
        
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
    
        tab1, tab2, tab3 = st.tabs([
            "🗺️ Mappa Geo-Rischio",
            "📈 Grafici",
            "🔍 Dettaglio Clienti"
        ])
        
        # ═══════════════════════════════════════════════════════════════════════════════
        # TAB 1: GEO-RISK MAP
        # ═══════════════════════════════════════════════════════════════════════════════
        
        with tab1:
            st.markdown("### 🌍 Mappa del Rischio Territoriale")
            
            # Map Mode Selector
            map_mode = st.radio(
                "Visualizza per",
                ["Rischio Composito", "Rischio Sismico", "Rischio Idrogeologico", "Rischio Alluvione"],
                horizontal=True,
                label_visibility="collapsed"
            )
            
            # Legend based on mode
            if map_mode == "Rischio Composito":
                st.caption("Visualizzazione basata sul Risk Score complessivo.")
            elif map_mode == "Rischio Sismico":
                st.caption("Visualizzazione basata su Zona Sismica (1=Alto, 4=Basso).")
            else:
                st.caption("Visualizzazione basata su livelli di pericolosità (P3/P4).")
    
            # Prepare map data
            map_df = filtered_df[
                filtered_df['latitudine'].notna() & 
                filtered_df['longitudine'].notna()
            ].copy()
    
            # Check for Mapbox Token
            mapbox_key = os.getenv("MAPBOX_TOKEN")
            if not mapbox_key:
                st.warning("⚠️ MAPBOX_TOKEN mancante nel file .env. La mappa potrebbe non mostrare lo sfondo.")
            
            if len(map_df) == 0:
                st.warning("⚠️ Nessuna abitazione con coordinate geografiche disponibile.")
            else:
                # 1. Prepare Colors based on Mode
                
                if map_mode == "Rischio Composito":
                    RISK_COLOR_MAP = {
                        'Critico': [220, 38, 38, 200],   # Red
                        'Alto':    [234, 88, 12, 200],   # Orange
                        'Medio':   [202, 138, 4, 180],   # Yellow
                        'Basso':   [22, 163, 74, 180]    # Green
                    }
                    DEFAULT_COLOR = [22, 163, 74, 180]
                    map_df['color'] = map_df['risk_category'].apply(lambda x: RISK_COLOR_MAP.get(x, DEFAULT_COLOR))
                    weight_col = "risk_score"
                    
                elif map_mode == "Rischio Sismico":
                    # Zone 1 (Red) -> Zone 4 (Green)
                    SEISMIC_COLORS = {
                        1: [220, 38, 38, 200],
                        2: [234, 88, 12, 200],
                        3: [202, 138, 4, 180],
                        4: [22, 163, 74, 180]
                    }
                    map_df['color'] = map_df['zona_sismica'].apply(lambda x: SEISMIC_COLORS.get(int(x) if pd.notna(x) else 4, [200, 200, 200, 100]))
                    weight_col = "zona_sismica" # Not perfect for heatmap but ok
                    
                elif map_mode == "Rischio Idrogeologico":
                    # P4/P3 = High, P2 = Med, P1 = Low
                    HYDRO_COLORS = {
                        'P4': [220, 38, 38, 200],
                        'P3': [234, 88, 12, 200],
                        'P2': [202, 138, 4, 180],
                        'P1': [22, 163, 74, 180]
                    }
                    # Check column name, usually hydro_risk_p3 contains the class string? Or float?
                    # DB scheme likely has string 'P3', 'P2' etc or just the value. Assuming string or mapped.
                    # If content is like "Molto Elevata (P4)", we might need parsing. 
                    # For now assume direct mapping or simple fallback.
                    map_df['color'] = map_df['hydro_risk_p3'].apply(lambda x: HYDRO_COLORS.get(str(x)[:2], [200, 200, 200, 100])) 
                    weight_col = "risk_score"
                
                else: # Flood
                    FLOOD_COLORS = {
                        'P3': [220, 38, 38, 200],
                        'P2': [234, 88, 12, 200],
                        'P1': [22, 163, 74, 180]
                    }
                    map_df['color'] = map_df['flood_risk_p3'].apply(lambda x: FLOOD_COLORS.get(str(x)[:2], [200, 200, 200, 100]))
                    weight_col = "risk_score"
    
                
                # 2. PyDeck Layers
                
                # View State (Initialize centered on data or Italy)
                view_state = pdk.ViewState(
                    latitude=map_df['latitudine'].mean() if len(map_df) > 0 else 41.8719,
                    longitude=map_df['longitudine'].mean() if len(map_df) > 0 else 12.5674,
                    zoom=5.5,
                    pitch=0,
                )
    
                # Layer 1: Heatmap (Density/Intensity)
                heatmap_layer = pdk.Layer(
                    "HeatmapLayer",
                    data=map_df,
                    get_position=['longitudine', 'latitudine'],
                    get_weight=weight_col,
                    opacity=0.4,
                    radius_pixels=40,
                    intensity=1,
                    threshold=0.2
                )
    
                # Layer 2: Scatterplot (Individual Points)
                scatter_layer = pdk.Layer(
                    "ScatterplotLayer",
                    data=map_df,
                    get_position=['longitudine', 'latitudine'],
                    get_fill_color='color',
                    get_radius=5000,  # Meters
                    pickable=True,
                    radius_min_pixels=4,
                    radius_max_pixels=15,
                    line_width_min_pixels=1,
                    stroked=True,
                    get_line_color=[255, 255, 255, 100]
                )
    
                # Render Chart
                st.pydeck_chart(pdk.Deck(
                    map_style='mapbox://styles/mapbox/light-v10',
                    api_keys={'mapbox': mapbox_key},
                    initial_view_state=view_state,
                    layers=[heatmap_layer, scatter_layer],
                    tooltip={
                        "html": "<b>Città:</b> {citta}<br/>"
                                "<b>Rischio:</b> {risk_score}<br/>"
                                "<b>Categoria:</b> {risk_category}<br/>"
                                "<b>Cliente:</b> {codice_cliente}",
                        "style": {"backgroundColor": "steelblue", "color": "white"}
                    }
                ))
    
                # 3. Critical Highlights Section (Replacing the big table)
                st.markdown("### 🚨 Focus Criticità")
                
                # Get top critical items
                critical_df = map_df[map_df['risk_category'].isin(['Critico', 'Alto'])].sort_values('risk_score', ascending=False).head(4)
                
                if not critical_df.empty:
                    cols = st.columns(len(critical_df))
                    for idx, row in enumerate(critical_df.itertuples()):
                        with cols[idx]:
                            # Card Styling
                            risk_color = "#DC2626" if row.risk_category == 'Critico' else "#EA580C"
                            st.markdown(f"""
                            <div style="
                                background: white;
                                border: 1px solid {risk_color};
                                border-left: 5px solid {risk_color};
                                border-radius: 8px;
                                padding: 1rem;
                                box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
                            ">
                                <h4 style="margin:0; font-size: 0.9rem; color: #64748B;">{row.citta}</h4>
                                <p style="font-size: 1.8rem; font-weight: 800; color: #1B3A5F; margin: 0;">{row.risk_score}</p>
                                <p style="font-size: 0.75rem; color: {risk_color}; font-weight: bold; margin:0;">
                                    {row.risk_category.upper()}
                                </p>
                                <p style="font-size: 0.7rem; color: #94A3B8; margin-top:0.5rem;">
                                    ID: {row.id}<br>Filtra mappa per zoom
                                </p>
                            </div>
                            """, unsafe_allow_html=True)
                else:
                    st.info("✅ Nessuna criticità elevata rilevata nei filtri correnti.")
    
                st.markdown("<br>", unsafe_allow_html=True)
    
                # 4. Collapsible full data table
                with st.expander("📋 Visualizza Elenco Completo Abitazioni", expanded=False):
                    # Display table with key columns
                    display_cols = ['id', 'citta', 'risk_score', 'risk_category', 'zona_sismica', 'codice_cliente']
                    display_df = map_df[[c for c in display_cols if c in map_df.columns]].copy()
                    display_df['risk_score'] = display_df['risk_score'].fillna(0).round(1)
                    
                    st.dataframe(
                        display_df,
                        use_container_width=True,
                        height=400,
                        column_config={
                            'id': st.column_config.TextColumn('ID'),
                            'citta': st.column_config.TextColumn('Città'),
                            'risk_score': st.column_config.ProgressColumn('Risk Score', min_value=0, max_value=100, format="%.1f"),
                            'risk_category': st.column_config.TextColumn('Categoria'),
                            'zona_sismica': st.column_config.NumberColumn('Zona Sism.'),
                            'codice_cliente': st.column_config.TextColumn('Cliente'),
                        }
                    )
            
            # Legend (Horizontal)
            st.markdown("""
            <div style="display: flex; gap: 2rem; justify-content: center; margin-top: 2rem; flex-wrap: wrap; opacity: 0.8;">
                <div style="display:flex; align-items:center; gap:0.5rem;"><span style="width:12px; height:12px; background:#DC2626; border-radius:50%;"></span> <span style="font-size:0.8rem;">Critico</span></div>
                <div style="display:flex; align-items:center; gap:0.5rem;"><span style="width:12px; height:12px; background:#EA580C; border-radius:50%;"></span> <span style="font-size:0.8rem;">Alto</span></div>
                <div style="display:flex; align-items:center; gap:0.5rem;"><span style="width:12px; height:12px; background:#CA8A04; border-radius:50%;"></span> <span style="font-size:0.8rem;">Medio</span></div>
                <div style="display:flex; align-items:center; gap:0.5rem;"><span style="width:12px; height:12px; background:#16A34A; border-radius:50%;"></span> <span style="font-size:0.8rem;">Basso</span></div>
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
        
                st.plotly_chart(fig_donut, use_container_width=True)
        
            with analytics_col2:
                # Risk Type Breakdown
                st.markdown("#### 🌍 Dettaglio Geo-Rischi")
                risk_chart_type = st.radio(
                    "Tipologia", 
                    ["Sismico", "Idrogeologico", "Alluvionale"], 
                    horizontal=True,
                    label_visibility="collapsed",
                    key="risk_chart_selector"
                )
    
                if risk_chart_type == "Sismico":
                    # Seismic Zone Bar Chart
                    zone_counts = filtered_df['zona_sismica'].value_counts().sort_index()
                    x_vals = [f"Zona {z}" for z in zone_counts.index]
                    y_vals = zone_counts.values
                    colors = ['#DC2626', '#EA580C', '#CA8A04', '#16A34A'][:len(zone_counts)]
                    title = "Abitazioni per Zona Sismica"
                    
                elif risk_chart_type == "Idrogeologico":
                    # Hydro Risk Bar Chart (P3/P4 etc)
                    if 'hydro_risk_p3' in filtered_df.columns:
                        hydro_counts = filtered_df['hydro_risk_p3'].astype(str).value_counts().sort_index()
                        x_vals = hydro_counts.index.tolist()
                        y_vals = hydro_counts.values
                        # Robust color mapping
                        colors = []
                        for x in x_vals:
                            s = str(x).upper()
                            if 'P4' in s or '4' in s: c = '#DC2626'
                            elif 'P3' in s or '3' in s: c = '#EA580C'
                            elif 'P2' in s or '2' in s: c = '#CA8A04'
                            elif 'P1' in s or '1' in s: c = '#16A34A'
                            else: c = '#94A3B8'
                            colors.append(c)
                        title = "Abitazioni per Rischio Idrogeologico"
                    else:
                        x_vals, y_vals, colors = [], [], []
                        title = "Dati Idrogeologici non disponibili"
    
                else: # Alluvionale
                     if 'flood_risk_p3' in filtered_df.columns:
                        flood_counts = filtered_df['flood_risk_p3'].astype(str).value_counts().sort_index()
                        x_vals = flood_counts.index.tolist()
                        y_vals = flood_counts.values
                        colors = []
                        for x in x_vals:
                            s = str(x).upper()
                            if 'P4' in s or '4' in s: c = '#DC2626'
                            elif 'P3' in s or '3' in s: c = '#EA580C'
                            elif 'P2' in s or '2' in s: c = '#CA8A04'
                            elif 'P1' in s or '1' in s: c = '#16A34A'
                            else: c = '#94A3B8'
                            colors.append(c)
                        title = "Abitazioni per Rischio Alluvione"
                     else:
                        x_vals, y_vals, colors = [], [], []
                        title = "Dati Alluvionali non disponibili"
    
                fig_bar = go.Figure(data=[go.Bar(
                    x=x_vals,
                    y=y_vals,
                    marker=dict(
                        color=colors,
                        line=dict(color='rgba(255,255,255,0.8)', width=1)
                    ),
                    text=y_vals,
                    textposition='outside',
                    textfont=dict(family='JetBrains Mono', size=12, color='#1B3A5F'),
                    hovertemplate="<b>%{x}</b><br>%{y:,} abitazioni<extra></extra>"
                )])
        
                fig_bar.update_layout(
                    title=dict(
                        text=title,
                        font=dict(family='Inter', size=16, color='#1B3A5F', weight=600),
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
        
                st.plotly_chart(fig_bar, use_container_width=True)
            
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
        
                st.plotly_chart(fig_scatter, use_container_width=True)
        
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
        
                st.plotly_chart(fig_churn, use_container_width=True)
            
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
        
            st.plotly_chart(fig_city, use_container_width=True)
        
        
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
    
            # Header for the list
            h_col1, h_col2, h_col3, h_col4 = st.columns([2, 1, 1, 0.5])
            with h_col1: st.markdown("**Cliente / Abitazione**")
            with h_col2: st.markdown("**Rischio**")
            with h_col3: st.markdown("**Valore**")
            
            st.divider()
    
            # Display as List with Button
            for i, row in enumerate(display_df.head(20).itertuples()):
                risk_class = row.risk_category.lower()
                
                # Extract client name if available
                client_name = "Cliente"
                if hasattr(row, 'clienti') and isinstance(row.clienti, dict):
                    client_name = f"{row.clienti.get('nome', '')} {row.clienti.get('cognome', '')}".strip()
                
                row_col1, row_col2, row_col3, row_col4 = st.columns([2, 1, 1, 0.5])
                
                with row_col1:
                    st.markdown(f"""
                    <div>
                        <h4 style="margin: 0; color: #1B3A5F; font-size: 0.95rem; font-weight: 600;">{client_name}</h4>
                        <p style="margin: 0; color: #64748B; font-size: 0.8rem;">📍 {row.citta}</p>
                        <p style="margin: 0; color: #94A3B8; font-size: 0.7rem;">ID: {row.codice_cliente}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                with row_col2:
                     st.markdown(f"""
                     <div>
                        <span class="risk-badge risk-{risk_class}" style="font-size:0.75rem;">{row.risk_category}</span>
                        <p style="margin: 0.2rem 0 0 0; color: #64748B; font-size: 0.75rem;">Score: <b>{row.risk_score}</b></p>
                     </div>
                     """, unsafe_allow_html=True)
    
                with row_col3:
                     st.markdown(f"""
                        <div>
                            <span style="font-size:1rem; font-weight:700; color:#00A0B0;">€{row.clv:,}</span>
                            <p style="margin: 0; color: #94A3B8; font-size: 0.7rem;">CLV Stimato</p>
                        </div>
                     """, unsafe_allow_html=True)
    
                with row_col4:
                    if st.button("👁️", key=f"det_{row.id}_{i}", help="Visualizza Dettagli"):
                        st.session_state.analytics_client_id = row.codice_cliente
                        st.session_state.analytics_page = 'detail'
                        st.rerun()
                
                st.divider()
    
            
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

            # Iris Section at the end of Top 5
            st.markdown("<br><br>", unsafe_allow_html=True)
            st.markdown("## 🤖 Iris – Sintesi e Azioni")
            st.markdown("""
            <div class="glass-card" style="border-left: 4px solid #00A0B0;">
                <p style="color: #64748B; font-size: 0.95rem; line-height: 1.6; margin-bottom: 1rem;">
                    Iris può aiutarti ad analizzare questi clienti prioritari e preparare comunicazioni personalizzate.
                </p>
            </div>
            """, unsafe_allow_html=True)

            # Prepare context for Iris about Top 5 clients
            top5_context = "I Top 5 clienti prioritari sono:\n\n"
            for i, rec in enumerate(top5_recs):
                top5_context += f"{i+1}. {rec['nome']} {rec['cognome']} ({rec['codice_cliente']}) - Score: {rec['score']:.1f} - Prodotto raccomandato: {rec['prodotto']}\n"

            # Button for mass email action
            if st.button("📧 Prepara Email Personalizzate", type="primary", use_container_width=True, key="mass_email_top5"):
                st.session_state.iris_auto_prompt = f"""Analizza questi {len(top5_recs)} clienti prioritari e crea una strategia di contatto:

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
            meta = client_data.get('metadata', {})
            ana = client_data.get('anagrafica', {})

            # ═══════════════════════════════════════════════════════════════════
            # TOP NAVIGATION BAR (Redesigned - Clear hierarchy)
            # ═══════════════════════════════════════════════════════════════════
            # Back button on the left, full width for proper alignment
            if st.button("← Torna alla Dashboard", key="back_btn", type="secondary"):
                st.session_state.nbo_page = 'dashboard'
                st.session_state.nbo_selected_client = None
                st.session_state.nbo_selected_recommendation = None
                st.rerun()

            # Show call form if open
            if st.session_state.get('show_call_form', False):
                st.markdown("---")
                st.markdown("##### 📞 Hai proposto la polizza raccomandata?")

                top_recommendation = None
                if client_data.get('raccomandazioni'):
                    recs_with_scores = []
                    for rec in client_data['raccomandazioni']:
                        score = calculate_recommendation_score(rec, st.session_state.nbo_weights)
                        recs_with_scores.append((score, rec))
                    recs_with_scores.sort(key=lambda x: x[0], reverse=True)
                    top_recommendation = recs_with_scores[0][1] if recs_with_scores else None

                available_products = [
                    "Assicurazione Casa e Famiglia: Casa Serena",
                    "Piano Individuale Pensionistico (PIP): Pensione Serenità",
                    "Polizza Salute e Infortuni: Salute Protetta",
                    "Polizza Vita a Premi Ricorrenti: Risparmio Costante",
                    "Polizza Vita a Premio Unico: Futuro Sicuro"
                ]

                polizza_scelta = st.radio("Polizza proposta *", options=["Sì", "No", "Altre"], horizontal=True)
                polizza_proposta = None
                if polizza_scelta == "Sì" and top_recommendation:
                    polizza_proposta = top_recommendation['prodotto']
                    st.info(f"💡 Polizza raccomandata: **{polizza_proposta}**")
                elif polizza_scelta == "Altre":
                    polizza_proposta = st.selectbox("Seleziona polizza", options=available_products)
                elif polizza_scelta == "No":
                    polizza_proposta = "Nessuna proposta"

                esito = st.selectbox("Esito della chiamata *", options=["Positivo", "Neutro", "Negativo"])
                note_aggiuntive = st.text_area("Note aggiuntive", placeholder="Inserisci eventuali note...")

                col_cancel, col_submit = st.columns(2)
                with col_cancel:
                    if st.button("❌ Annulla", use_container_width=True):
                        st.session_state.show_call_form = False
                        st.rerun()
                with col_submit:
                    if st.button("✅ Registra chiamata", type="primary", use_container_width=True):
                        codice_cliente = client_data['codice_cliente']
                        note_complete = f"Polizza proposta: {polizza_proposta}\nEsito: {esito}"
                        if note_aggiuntive and note_aggiuntive.strip():
                            note_complete += f"\nNote: {note_aggiuntive}"
                        success = insert_phone_call_interaction(codice_cliente, polizza_proposta=polizza_proposta, esito=esito.lower(), note=note_complete)
                        if success:
                            if '_interaction_indicators' not in client_data:
                                client_data['_interaction_indicators'] = {}
                            client_data['_interaction_indicators']['call_last_10_days'] = True
                            client_data['_is_eligible_top20'] = False
                            st.session_state.show_call_form = False
                            st.session_state.show_success_message = True
                            st.rerun()
                        else:
                            st.error("❌ Errore nella registrazione della chiamata.")
                st.markdown("---")

            if st.session_state.get('show_success_message', False):
                st.success("✅ Esito registrato! Il cliente non sara più visibile nel Top 20/Top 5.")
                st.session_state.show_success_message = False

            # ═══════════════════════════════════════════════════════════════════
            # CLIENT HEADER CARD (HTML Standard)
            # ═══════════════════════════════════════════════════════════════════
            churn = meta.get('churn_attuale', 0)
            churn_class = 'success' if churn < 0.1 else 'warning' if churn < 0.3 else 'teal'
            num_polizze = meta.get('num_polizze_attuali', 0)
            clv = meta.get('clv_stimato', 0)
            cluster = meta.get('cluster_risposta', 'N/D')

            st.markdown(f"""
            <div class="standard-card card-with-button">
                <div class="client-header-top">
                    <div class="client-header-left">
                        <h2 class="client-name">{ana.get('nome', 'N/D')} {ana.get('cognome', 'N/D')}</h2>
                        <p class="client-id-location"><span class="pin-icon">📍</span> {client_data.get('codice_cliente', 'N/D')} · {ana.get('citta', 'N/D')}</p>
                    </div>
                    <div class="client-header-right">
                        <span class="rec-product-badge">PRODOTTO CONSIGLIATO</span>
                        <p style="margin: 0.5rem 0 0 0; font-size: 0.95rem; font-weight: 600; color: #1B3A5F; max-width: 280px;">{recommendation['prodotto'] if recommendation else 'N/D'}</p>
                    </div>
                </div>
                <div class="client-stats-grid">
                    <div class="client-stat-item">
                        <p class="client-stat-label">CLV Stimato</p>
                        <p class="client-stat-value teal">€{clv:,.0f}</p>
                    </div>
                    <div class="client-stat-item">
                        <p class="client-stat-label">Polizze Attive</p>
                        <p class="client-stat-value">{num_polizze}</p>
                    </div>
                    <div class="client-stat-item">
                        <p class="client-stat-label">Rischio Churn</p>
                        <p class="client-stat-value {churn_class}">{churn:.1%}</p>
                    </div>
                    <div class="client-stat-item">
                        <p class="client-stat-label">Cluster</p>
                        <p class="client-stat-value">{cluster.replace('_', ' ').split()[0] if cluster != 'N/D' else 'N/D'}</p>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Registra Chiamata button - "Attached" style
            # We use a container to apply specific styling if possible, but here we rely on the CSS targeting stButton
            st.markdown("""
            <style>
                /* Hack to target the specific button using adjacency or N-th child is hard.
                   We will inject a specific style block just for this button if possible.
                   Actually, we updated the global CSS to handle 'card-with-button' followed by button? 
                   No, CSS next-sibling selector doesn't work well with Streamlit's wrapping divs.
                   We will use a negative margin here to force it. */
                div[data-testid="column"] > div > div > div > div > button {
                    /* This is too generic. We'll rely on the margin-top: 0 from the code block below. */
                }
            </style>
            <!-- Zero Gap Spacer -->
            <div style="margin-top: -16px;"></div>
            """, unsafe_allow_html=True)

            if st.button("📞 Registra Chiamata", type="primary", key="open_call_form", use_container_width=True):
                st.session_state.show_call_form = True

            # ═══════════════════════════════════════════════════════════════════
            # IRIS AI SECTION (HTML Standard - AI Theme)
            # ═══════════════════════════════════════════════════════════════════
            
            # Separation from Header
            st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)

            if 'client_email_draft' not in st.session_state:
                st.session_state.client_email_draft = None
            if 'current_draft_client' not in st.session_state:
                st.session_state.current_draft_client = None

            codice_cliente_ada = client_data['codice_cliente']
            nome_completo = f"{ana.get('nome', '')} {ana.get('cognome', '')}"

            client_context = f"""Cliente: {nome_completo} ({codice_cliente_ada})
CLV Stimato: €{clv:,}
Polizze Attuali: {num_polizze}
Prodotto Raccomandato: {recommendation['prodotto'] if recommendation else 'N/D'}
Area Bisogno: {recommendation['area_bisogno'] if recommendation else 'N/D'}
Score Raccomandazione: {(calculate_recommendation_score(recommendation, st.session_state.nbo_weights) if recommendation else 0):.1f}
Retention Gain: {(recommendation['componenti']['retention_gain'] if recommendation else 0):.1f}%
Propensione: {(recommendation['componenti']['propensione'] if recommendation else 0):.1f}%"""

            # Iris Card - AI Style (Blue Border)
            st.markdown("""
            <div class="standard-card card-with-button" style="border: 2px solid #00A0B0; background: #F0FDFA; display: flex; flex-direction: row; gap: 1.5rem; align-items: center;">
                <div class="iris-icon-wrapper" style="width: 56px; height: 56px; border-radius: 16px; background: #FFFFFF; box-shadow: 0 2px 4px rgba(0,160,176,0.1); display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" style="width: 32px; height: 32px; color: #00A0B0;">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 00-2.456 2.456zM16.894 20.567L16.5 21.75l-.394-1.183a2.25 2.25 0 00-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 001.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 001.423 1.423l1.183.394-1.183.394a2.25 2.25 0 00-1.423 1.423z" />
                    </svg>
                </div>
                <div class="iris-content" style="flex: 1;">
                    <p class="iris-title" style="margin: 0; font-weight: 700; color: #1B3A5F; font-size: 1.1rem;">Iris – Assistente AI</p>
                    <p class="iris-subtitle" style="margin: 0.25rem 0 0 0; font-size: 0.9rem; color: #475569;">Genera comunicazioni personalizzate e sfrutta l'intelligenza artificiale per supportare questo cliente.</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Genera Email Button - Attached
            st.markdown("<div style='margin-top: -16px;'></div>", unsafe_allow_html=True)
            email_btn_clicked = st.button("📧 Genera Email Personalizzata", type="primary", use_container_width=True, key="generate_email_draft")

            if email_btn_clicked:
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
2. Proponga il prodotto "{recommendation['prodotto'] if recommendation else ''}" evidenziandone i benefici
3. Usi un tono professionale ma cordiale
4. Includa una call-to-action chiara
5. Sia lunga 150-200 parole
6. Sia firmata da {st.session_state.user_name} di Vita Sicura
7. Includa i contatti dell'agente nella firma

FORMATO:
**Oggetto:** [scrivi qui l'oggetto]

---

[Corpo dell'email]

GENERA L'EMAIL ORA senza usare tool."""

                with st.spinner("Iris sta generando la bozza email..."):
                    from src.iris.chat import init_iris_engine, get_iris_response
                    init_iris_engine()
                    result = get_iris_response(prompt)
                    if result.get("success"):
                        st.session_state.client_email_draft = result.get("response")
                        st.session_state.current_draft_client = codice_cliente_ada
                        st.success("Bozza email generata!")
                        st.rerun()
                    else:
                        st.error("Errore nella generazione. Riprova.")

            if st.session_state.current_draft_client == codice_cliente_ada and st.session_state.client_email_draft:
                st.markdown("""<div class="section-header"><span class="section-icon">📧</span><h3 class="section-title">Bozza Email Generata</h3></div>""", unsafe_allow_html=True)
                st.markdown(f"""<div class="glass-card" style="background: #F0FDF4; border-left: 4px solid #10B981;">{st.session_state.client_email_draft}</div>""", unsafe_allow_html=True)

                col1, col2 = st.columns(2)
                with col1:
                    modify_prompt = st.text_input("Modifica l'email", placeholder="es. 'rendila più formale'", key="email_modify_prompt")
                with col2:
                    if st.button("🔄 Applica Modifica", key="apply_email_modification") and modify_prompt:
                        updated_prompt = f"""Modifica l'email seguente: {st.session_state.client_email_draft}

Richiesta: {modify_prompt}

Mantieni formato **Oggetto:** e corpo email. GENERA ORA senza tool."""
                        with st.spinner("🤖 Modificando..."):
                            from src.iris.chat import get_iris_response
                            result = get_iris_response(updated_prompt)
                            if result.get("success"):
                                st.session_state.client_email_draft = result.get("response")
                                st.success("✅ Email modificata!")
                                st.rerun()
                            else:
                                st.error("❌ Errore nella modifica.")

            st.markdown("<br>", unsafe_allow_html=True)

            # ═══════════════════════════════════════════════════════════════════
            # GRID LAYOUT - 2 colonne con card impilate verticalmente
            # ═══════════════════════════════════════════════════════════════════

            # Prepare data
            indicators = client_data.get('_interaction_indicators', {})
            prodotti = meta.get('prodotti_posseduti', [])
            if prodotti and isinstance(prodotti, str):
                prodotti = [prodotti]

            # Build polizze html con coefficienti attuariali (solo Casa e Salute)
            polizze_html = ""
            if prodotti:
                for p in prodotti:
                    prod_lower = p.lower()
                    if 'casa' in prod_lower: icon = '🏠'
                    elif 'vita' in prod_lower: icon = '💚'
                    elif 'salute' in prod_lower: icon = '🏥'
                    elif 'pension' in prod_lower: icon = '🎯'
                    else: icon = '📋'

                    # Genera coefficienti attuariali (solo per Casa e Salute)
                    coeff = genera_coefficienti_polizza(ana, p, codice_cliente_ada)

                    if coeff:
                        # Polizza con coefficienti (Casa o Salute)
                        gap_color = "#059669" if coeff['gap_relativo_perc'] >= 0 else "#DC2626"
                        gap_sign = "+" if coeff['gap_relativo_perc'] >= 0 else ""

                        polizze_html += f"""
                        <div style='margin-bottom:1rem; padding:0.75rem; background:#F8FAFC; border-radius:8px; border:1px solid #E2E8F0;'>
                            <div style='display:flex; justify-content:space-between; align-items:center;'>
                                <span>{icon} <strong>{p}</strong></span>
                                <span style='background:#D1FAE5;color:#059669;padding:2px 8px;border-radius:12px;font-size:0.7rem;'>Attiva</span>
                            </div>
                            <div style='font-size:0.7rem; color:#94A3B8; margin:0.25rem 0 0.5rem 0;'>Loss Ratio Target: {coeff['loss_ratio_label']}</div>
                            <div style='display:grid; grid-template-columns:1fr 1fr; gap:0.5rem; font-size:0.8rem;'>
                                <div style='background:#FFF; padding:0.4rem; border-radius:6px; border:1px solid #E2E8F0;'>
                                    <div style='color:#64748B; font-size:0.7rem;'>Premio Pagato</div>
                                    <div style='color:#1B3A5F; font-weight:600;'>€{coeff['premio_pagato']:,.0f}</div>
                                </div>
                                <div style='background:#FFF; padding:0.4rem; border-radius:6px; border:1px solid #E2E8F0;'>
                                    <div style='color:#64748B; font-size:0.7rem;'>Premio Tecnico</div>
                                    <div style='color:#1B3A5F; font-weight:600;'>€{coeff['premio_tecnico']:,.0f}</div>
                                </div>
                            </div>
                            <div style='margin-top:0.5rem; padding:0.4rem; background:{gap_color}15; border-radius:6px; display:flex; justify-content:space-between; align-items:center;'>
                                <span style='font-size:0.75rem; color:#64748B;'>Scarto: <strong style="color:{gap_color}">€{coeff['gap_assoluto']:+,.0f}</strong></span>
                                <span style='font-size:0.85rem; font-weight:700; color:{gap_color};'>{gap_sign}{coeff['gap_relativo_perc']:.1f}%</span>
                            </div>
                        </div>"""
                    else:
                        # Polizza senza coefficienti (Vita, Pensione, etc.)
                        polizze_html += f"""
                        <div style='margin-bottom:0.5rem; padding:0.5rem 0.75rem; background:#F8FAFC; border-radius:8px; border:1px solid #E2E8F0; display:flex; justify-content:space-between; align-items:center;'>
                            <span>{icon} <strong>{p}</strong></span>
                            <span style='background:#D1FAE5;color:#059669;padding:2px 8px;border-radius:12px;font-size:0.7rem;'>Attiva</span>
                        </div>"""
            else:
                polizze_html = "<em style='color:#94A3B8;'>Nessuna polizza attiva</em>"

            # Build chip html for interactions
            chip_html = "<div style='display: flex; flex-direction: column; gap: 0.75rem;'>"
            chip_data = [
                ("Email (5gg)", indicators.get('email_last_5_days', False), "✉️"),
                ("Chiamata (10gg)", indicators.get('call_last_10_days', False), "📞"),
                ("Polizza (30gg)", indicators.get('new_policy_last_30_days', False), "📋"),
                ("Reclamo Aperto", indicators.get('open_complaint', False), "⚠️"),
                ("Sinistro (60gg)", indicators.get('claim_last_60_days', False), "🚗")
            ]

            for label, value, icon in chip_data:
                status_text = "Sì" if value else "No"
                status_bg = "#EF4444" if value and "Reclamo" in label else "#10B981" if value else "#94A3B8"

                chip_html += f"""<div style="display: flex; align-items: center; justify-content: space-between; padding: 0.5rem 0.75rem; background: #F8FAFC; border-radius: 8px; border: 1px solid #E2E8F0;">
    <div style="display: flex; align-items: center; gap: 0.5rem;">
        <span>{icon}</span>
        <span style="font-size: 0.85rem; font-weight: 500; color: #334155;">{label}</span>
    </div>
    <span style="font-size: 0.75rem; font-weight: 600; color: {status_bg};">{status_text}</span>
</div>"""
            chip_html += "</div>"

            # Build rec html
            rec_html = "<em>Nessuna raccomandazione</em>"
            if recommendation:
                comp = recommendation['componenti']
                rec_html = f"""<div>
    <span style='background:linear-gradient(135deg,#00A0B0,#00C9D4);color:white;padding:4px 12px;border-radius:6px;font-size:0.7rem;font-weight:700;'>RACCOMANDAZIONE AI</span>
    <p style='margin:0.5rem 0; font-weight:700;'>{recommendation['prodotto']}</p>
    <p style='margin:0 0 1rem 0; font-size:0.85rem; color:#64748B;'>📌 {recommendation['area_bisogno']}</p>
    <div style='display:grid; grid-template-columns: 1fr 1fr; gap:0.5rem;'>
        <div><small>🔄 RETENTION</small><div style='height:6px;width:100%;background:#F3F4F6;border-radius:10px;'><div style='height:100%;width:{min(comp['retention_gain'], 100)}%;background:#00A0B0;border-radius:10px;'></div></div><small><strong>{comp['retention_gain']:.1f}%</strong></small></div>
        <div><small>💰 REDDITIVITÀ</small><div style='height:6px;width:100%;background:#F3F4F6;border-radius:10px;'><div style='height:100%;width:{min(comp['redditivita'], 100)}%;background:#00A0B0;border-radius:10px;'></div></div><small><strong>{comp['redditivita']:.1f}%</strong></small></div>
        <div><small>🎯 PROPENSIONE</small><div style='height:6px;width:100%;background:#F3F4F6;border-radius:10px;'><div style='height:100%;width:{min(comp['propensione'], 100)}%;background:#00A0B0;border-radius:10px;'></div></div><small><strong>{comp['propensione']:.1f}%</strong></small></div>
        <div><small>👥 AFFINITÀ</small><div style='height:6px;width:100%;background:#F3F4F6;border-radius:10px;'><div style='height:100%;width:{min(comp['affinita_cluster'], 100)}%;background:#00A0B0;border-radius:10px;'></div></div><small><strong>{comp['affinita_cluster']:.1f}%</strong></small></div>
    </div>
</div>"""

            # 2 colonne con card impilate verticalmente
            col_left, col_right = st.columns(2, gap="medium")

            with col_left:
                # Colonna sinistra: Anagrafica + Stato Interazioni
                st.markdown(f"""
                <div class="standard-card">
                     <h5 style="margin-bottom: 1rem;">👤 Anagrafica</h5>
                     <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; flex: 1;">
                        <div>
                            <p style="margin:0; font-size:0.9rem;"><strong>🎂 Età:</strong> {ana.get('eta', 'N/D')} anni</p>
                            <p style="margin:0.5rem 0 0 0; font-size:0.9rem;"><strong>🏙️ Città:</strong> {ana.get('citta', 'N/D')}</p>
                        </div>
                        <div>
                            <p style="margin:0; font-size:0.9rem;"><strong>🏠 Indirizzo:</strong> {ana.get('indirizzo', 'N/D')}</p>
                            <p style="margin:0.5rem 0 0 0; font-size:0.9rem;"><strong>📍 Provincia:</strong> {ana.get('provincia', 'N/D')}</p>
                        </div>
                     </div>
                </div>
                <div class="standard-card">
                    <h5 style="margin-bottom: 1rem;">📋 Stato Interazioni</h5>
                    <div style="flex: 1;">{chip_html}</div>
                </div>
                """, unsafe_allow_html=True)

            with col_right:
                # Colonna destra: Polizze Attive + Prodotto Consigliato
                st.markdown(f"""
                <div class="standard-card">
                    <h5 style="margin-bottom: 1rem;">📦 Polizze Attive</h5>
                    <div style="flex: 1;">{polizze_html}</div>
                </div>
                <div class="standard-card">
                    <h5 style="margin-bottom: 1rem;">🎯 Prodotto Consigliato</h5>
                    <div style="flex: 1;">{rec_html}</div>
                </div>
                """, unsafe_allow_html=True)
                
            # Spacing before expander
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Expander for details
            with st.expander("📊 Dettagli Avanzati", expanded=False):
                 st.markdown(f"**Churn:** {meta.get('churn_attuale', 0):.4f} | **Cluster NBA:** {meta.get('cluster_nba', 'N/D')}")

            # ═══════════════════════════════════════════════════════════════════
            # ABITAZIONE CLIENT (HTML Standard + Fix Overflow)
            # ═══════════════════════════════════════════════════════════════════
            st.markdown("##### 📍 Abitazione Cliente")
            
            lat = ana.get('latitudine', 0)
            lon = ana.get('longitudine', 0)
            
            # Mapbox static image or placeholder - Using Placeholder for now as requested
            # Use pure HTML for container and image
            
            # Need to get CV data
            import hashlib
            client_hash = int(hashlib.md5(str(client_data.get('codice_cliente', '')).encode()).hexdigest(), 16)
            has_solar_panels = (client_hash % 3) == 0
            has_pool = (client_hash % 5) == 0
            has_garden = (client_hash % 2) == 0

            # Combined content for Abitazione
            # We can use st columns for layout but standard cards for content
            ac1, ac2 = st.columns([1, 2], gap="medium")
            
            with ac1:
                 # Satellite image card
                 st.markdown(f"""
                 <div class="standard-card" style="padding: 0; overflow: hidden; position: relative; height: 100%; min-height: 200px; display: flex; align-items: center; justify-content: center; background: #F3F4F6;">
                    <div style="text-align: center; z-index: 2;">
                        <span style="font-size: 3rem;">🛰️</span>
                        <p style="margin:0; font-weight:600; color:#64748B;">Vista Satellitare</p>
                        <small style="color:#94A3B8;">{lat:.4f}, {lon:.4f}</small>
                    </div>
                 </div>
                 """, unsafe_allow_html=True)
                 
            with ac2:
                # Features card - HEIGHT 100% enforced
                st.markdown(f"""
                <div class="standard-card" style="height: 100%; display: flex; flex-direction: column;">
                    <h5 style="margin-bottom: 1rem;">Caratteristiche Rilevate (CV)</h5>
                    <div style="display: flex; gap: 1rem; flex-wrap: wrap; align-items: center; flex: 1;">
                         <div style="flex: 1; min-width: 120px; padding: 1rem; border-radius: 12px; background: {'#D1FAE5' if has_solar_panels else '#F3F4F6'}; color: {'#059669' if has_solar_panels else '#6B7280'}; text-align: center;">{'✅' if has_solar_panels else '❌'} Pannelli Solari</div>
                         <div style="flex: 1; min-width: 120px; padding: 1rem; border-radius: 12px; background: {'#D1FAE5' if has_pool else '#F3F4F6'}; color: {'#059669' if has_pool else '#6B7280'}; text-align: center;">{'✅' if has_pool else '❌'} Piscina</div>
                         <div style="flex: 1; min-width: 120px; padding: 1rem; border-radius: 12px; background: {'#D1FAE5' if has_garden else '#F3F4F6'}; color: {'#059669' if has_garden else '#6B7280'}; text-align: center;">{'✅' if has_garden else '❌'} Giardino</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
            # ═══════════════════════════════════════════════════════════════════
            # RECOMMENDATIONS (HTML Standard)
            # ═══════════════════════════════════════════════════════════════════
            st.markdown("##### 📊 Tutte le Raccomandazioni")
            
            recs_with_scores = []
            for rec in client_data.get('raccomandazioni', []):
                score = calculate_recommendation_score(rec, st.session_state.nbo_weights)
                recs_with_scores.append((score, rec))
            recs_with_scores.sort(key=lambda x: x[0], reverse=True)
            
            rec_rows_html = ""
            for i, (score, rec) in enumerate(recs_with_scores):
                score_color = "#10B981" if score >= 0.7 else "#F59E0B" if score >= 0.5 else "#EF4444"
                border_style = "border-bottom: 1px solid #E2E8F0;" if i < len(recs_with_scores) - 1 else ""
                
                rec_rows_html += f"""<div style="display: flex; align-items: center; padding: 1rem 0; {border_style}">
    <div style="width: 36px; height: 36px; border-radius: 10px; background: linear-gradient(135deg,#00A0B0,#00C9D4); color: white; display: flex; align-items: center; justify-content: center; font-weight: 700; margin-right: 1rem; flex-shrink: 0;">{i+1}</div>
    <div style="flex: 1;">
        <p style="margin: 0; font-weight: 600; color: #1B3A5F;">{rec['prodotto']}</p>
        <p style="margin: 0; font-size: 0.8rem; color: #64748B;">{rec['area_bisogno']}</p>
    </div>
    <div style="text-align: right;">
        <p style="margin: 0; font-weight: 700; color: {score_color}; font-size: 1.2rem;">{score:.1f}</p>
        <p style="margin: 0; font-size: 0.65rem; color: #94A3B8; text-transform: uppercase;">SCORE</p>
    </div>
</div>"""
                
            st.markdown(f"""
            <div class="standard-card">
                {rec_rows_html}
            </div>
            """, unsafe_allow_html=True)


        else:
            # ═══════════════════════════════════════════════════════════════════════════════
            # POLICY ADVISOR MAIN DASHBOARD VIEW (formerly NBO)
            # ═══════════════════════════════════════════════════════════════════════════════

            # Get all recommendations with current weights
            all_recs = get_all_recommendations(nbo_data, st.session_state.nbo_weights, filter_top20=True)

            # ═══════════════════════════════════════════════════════════════════════════════
            # STRATEGIA ATTIVA (Always Visible)
            # ═══════════════════════════════════════════════════════════════════════════════
            
            w_ret = st.session_state.nbo_weights['retention']
            w_red = st.session_state.nbo_weights['redditivita']
            w_pro = st.session_state.nbo_weights['propensione']

            st.markdown(f"""
            <div class="active-strategy-card" style="margin-bottom: 0;">
                <div class="strategy-info">
                    <div class="strategy-label">STRATEGIA ATTIVA</div>
                    <div class="strategy-title">Q1 2026 - Focus Retention</div>
                </div>
                <div class="strategy-metrics" style="gap: 3rem;">
                    <div class="metric-item">
                        <div class="metric-label">key driver</div>
                        <div class="metric-value" style="color: #00A0B0;">RETENTION</div>
                    </div>
                    <div class="metric-divider"></div>
                     <div class="metric-item">
                        <div class="metric-label">Retention</div>
                        <div class="metric-value">{w_ret:.0%}</div>
                    </div>
                    <div class="metric-divider"></div>
                    <div class="metric-item">
                        <div class="metric-label">Redditività</div>
                        <div class="metric-value">{w_red:.0%}</div>
                    </div>
                    <div class="metric-divider"></div>
                    <div class="metric-item">
                        <div class="metric-label">Propensione</div>
                        <div class="metric-value">{w_pro:.0%}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)


            st.markdown("<br>", unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # ═══════════════════════════════════════════════════════════════════════════════
            # TOP 5 CLIENTS GRID
            # ═══════════════════════════════════════════════════════════════════════════════
            st.markdown("### 🌟 Top 5 Clienti ad Alto Potenziale")
            
            top5_recs = all_recs[:5]
            
            # Create 5 columns for the cards
            cols = st.columns(5)
            
            for i, rec in enumerate(top5_recs):
                with cols[i]:
                    # Standardize color to dashboard Teal for consistency
                    score_color = "#00A0B0" 
                    
                    # HTML Card Visuals - FLATTENED STRING without indentation to prevent code block rendering
                    st.markdown(f"""<div class="top5-card" style="box-shadow: 0 4px 20px rgba(0,0,0,0.05); border: 1px solid #E2E8F0; border-radius: 16px; overflow: hidden; height: 100%; display: flex; flex-direction: column; justify-content: space-between;"><div style="background: linear-gradient(135deg, {score_color}15 0%, #FFFFFF 100%); padding: 1.25rem; border-bottom: 1px solid #F1F5F9; position: relative;"><div style="position: absolute; top: 0; right: 0; background: {score_color}; color: white; padding: 0.25rem 0.6rem; border-bottom-left-radius: 12px; font-weight: 700; font-size: 0.8rem;">#{i+1}</div><h4 style="margin: 0; color: #1B3A5F; font-size: 1.1rem; font-weight: 700; line-height: 1.2;">{rec['nome']}<br>{rec['cognome']}</h4><p style="margin: 0.25rem 0 0 0; color: #64748B; font-size: 0.75rem; font-family: 'JetBrains Mono', monospace;">{rec['codice_cliente']}</p></div><div style="padding: 1.25rem; flex: 1;"><div style="margin-bottom: 1rem;"><p style="margin: 0; font-size: 0.65rem; text-transform: uppercase; color: #94A3B8; letter-spacing: 0.05em; font-weight: 600;">Prodotto Consigliato</p><p style="margin: 0.25rem 0 0 0; font-size: 0.9rem; color: #334155; line-height: 1.4; font-weight: 500;">{rec['prodotto']}</p></div><div style="display: flex; align-items: flex-end; justify-content: space-between;"><div><p style="margin: 0; font-size: 0.65rem; text-transform: uppercase; color: #94A3B8; letter-spacing: 0.05em; font-weight: 600;">Score</p><p style="margin: 0; font-size: 1.5rem; font-weight: 700; color: {score_color}; line-height: 1;">{rec['score']:.1f}</p></div><div style="width: 40px; height: 40px; border-radius: 50%; background: {score_color}15; display: flex; align-items: center; justify-content: center;"><span style="font-size: 1.2rem;">⚡</span></div></div></div></div>""", unsafe_allow_html=True)
                    
                    # Attached Button Style
                    st.markdown("<div style='margin-top: -16px;'></div>", unsafe_allow_html=True)
                    
                    # Single "Dettagli" Button - Attached
                    if st.button("Dettagli", key=f"det_{i}", type="secondary", use_container_width=True):
                        st.session_state.nbo_page = 'detail'
                        st.session_state.nbo_selected_client = rec['client_data']
                        st.session_state.nbo_selected_recommendation = rec['recommendation']
                        st.rerun()

            st.markdown("<br><hr><br>", unsafe_allow_html=True)

            # ═══════════════════════════════════════════════════════════════════════════════
            # LEADERBOARD (NEXT 20)
            # ═══════════════════════════════════════════════════════════════════════════════
            st.markdown("### 📋 Leaderboard Opportunità (Top 6-25)")
            
            top20_recs = all_recs[5:25]
            
            # LET'S REDO THE LOOP WITH COLUMNS FOR BETTER ALIGNMENT
            st.markdown("""
            <div style="display: grid; grid-template-columns: 0.5fr 2fr 2fr 1fr 1.5fr; gap: 1rem; padding: 1rem 1.5rem; background: #FFFFFF; border-radius: 12px; margin-bottom: 0.75rem; border: 1px solid #F1F5F9; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                <div style="color: #64748B; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em;">Rank</div>
                <div style="color: #64748B; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em;">Cliente</div>
                <div style="color: #64748B; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em;">Prodotto</div>
                <div style="color: #64748B; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em;">Score</div>
                <div style="color: #64748B; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; text-align: right;">Azioni</div>
            </div>
            """, unsafe_allow_html=True)

            for i, rec in enumerate(top20_recs):
                rank = i + 6
                # Row Container using Columns
                c1, c2, c3, c4, c5 = st.columns([0.5, 2, 2, 1, 1.5])
                
                with c1:
                    st.markdown(f"<p style='margin: 0.6rem 0; font-weight: 700; color: #94A3B8;'>#{rank}</p>", unsafe_allow_html=True)
                with c2:
                    st.markdown(f"<p style='margin: 0.6rem 0; font-weight: 600; color: #1B3A5F;'>{rec['nome']} {rec['cognome']}</p>", unsafe_allow_html=True)
                with c3:
                    st.markdown(f"<p style='margin: 0.6rem 0; color: #64748B; font-size: 0.9rem;'>{rec['prodotto']}</p>", unsafe_allow_html=True)
                with c4:
                    st.markdown(f"<p style='margin: 0.6rem 0; font-weight: 700; color: #00A0B0; font-family: \"JetBrains Mono\", monospace;'>{rec['score']:.1f}</p>", unsafe_allow_html=True)
                with c5:

                    if st.button("Dettagli", key=f"lb_det_{i}", type="secondary", use_container_width=True):
                        st.session_state.nbo_page = 'detail'
                        st.session_state.nbo_selected_client = rec['client_data']
                        st.session_state.nbo_selected_recommendation = rec['recommendation']
                        st.rerun()
                
                st.markdown("<div style='height: 1px; background: #F1F5F9; margin: 0.25rem 0;'></div>", unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # ═══════════════════════════════════════════════════════════════════════════════
            # MASS ACTION
            # ═══════════════════════════════════════════════════════════════════════════════
            st.markdown("""
            <div class="standard-card card-with-button" style="border: 2px solid #00A0B0; background: #F0FDFA; display: flex; flex-direction: row; gap: 1.5rem; align-items: center;">
                <div class="iris-icon-wrapper" style="width: 56px; height: 56px; border-radius: 16px; background: #FFFFFF; box-shadow: 0 2px 4px rgba(0,160,176,0.1); display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" style="width: 32px; height: 32px; color: #00A0B0;">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 00-2.456 2.456zM16.894 20.567L16.5 21.75l-.394-1.183a2.25 2.25 0 00-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 001.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 001.423 1.423l1.183.394-1.183.394a2.25 2.25 0 00-1.423 1.423z" />
                    </svg>
                </div>
                <div class="iris-content" style="flex: 1;">
                    <p class="iris-title" style="margin: 0; font-weight: 700; color: #1B3A5F; font-size: 1.1rem;">Azioni Massive con Iris</p>
                    <p class="iris-subtitle" style="margin: 0.25rem 0 0 0; font-size: 0.9rem; color: #475569;">Richiedi ad Iris di analizzare tutti i 20 clienti della leaderboard e preparare una bozza di email personalizzata per ciascuno.</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Genera Email Massive Button - Attached
            st.markdown("<div style='margin-top: -16px;'></div>", unsafe_allow_html=True)
            if st.button("✨ Genera Email Massive per Leaderboard (20 Clienti)", type="primary", use_container_width=True):
                    # Prepare Context
                    leaderboard_context = "Analizza i seguenti 20 clienti della leaderboard:\n\n"
                    for i, rec in enumerate(top20_recs):
                        leaderboard_context += f"{i+6}. {rec['nome']} {rec['cognome']} - Prodotto: {rec['prodotto']} - Score: {rec['score']:.1f}\n"

                    st.session_state.iris_auto_prompt = f"""Analizza questi 20 clienti della leaderboard e crea una strategia di contatto massiva ma personalizzata:
                    
{leaderboard_context}

Per ciascuno, genera una breve bozza di email (2-3 frasi chiave) focalizzata sul loro prodotto raccomandato.
Formatta la risposta come una lista chiara."""
                    st.success("Richiesta inviata ad Iris!")
                    
                    with st.spinner("Iris sta elaborando le strategie..."):
                         from src.iris.chat import get_iris_response, init_iris_engine
                         init_iris_engine()
                         res = get_iris_response(st.session_state.iris_auto_prompt)
                         if res.get('success'):
                             st.session_state.mass_email_result = res.get('response')
                             st.rerun()
                         else:
                             st.error("Errore Iris.")
            
            if 'mass_email_result' in st.session_state and st.session_state.mass_email_result:
                with st.expander("📬 Risultato Campagna Massiva", expanded=True):
                    st.write(st.session_state.mass_email_result)
                    if st.button("Chiudi Risultati", type="secondary"):
                        del st.session_state.mass_email_result
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
