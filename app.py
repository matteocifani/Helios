"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                         🌞 PROGETTO HELIOS                                     ║
║              Ecosistema Assicurativo Geo-Cognitivo                            ║
║                     Dashboard FluidView v1.0                                   ║
╚═══════════════════════════════════════════════════════════════════════════════╝
"""

import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from ada_chat_enhanced import render_ada_chat

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
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&family=Playfair+Display:wght@400;500;600;700&display=swap');
    
    /* ═══════════════════════════════════════════════════════════════════════
       CSS VARIABLES - Aurora Palette
    ═══════════════════════════════════════════════════════════════════════ */
    :root {
        --helios-sun: #FF6B35;
        --helios-amber: #F7C948;
        --helios-coral: #FF8C61;
        --aurora-cyan: #00E5CC;
        --aurora-blue: #0A84FF;
        --aurora-purple: #5E5CE6;
        --deep-space: #0D1117;
        --space-gray: #161B22;
        --nebula-gray: #21262D;
        --star-white: #F0F6FC;
        --comet-gray: #8B949E;
        
        --risk-critical: #FF453A;
        --risk-high: #FF9F0A;
        --risk-medium: #FFD60A;
        --risk-low: #30D158;
        
        --glass-bg: rgba(22, 27, 34, 0.85);
        --glass-border: rgba(240, 246, 252, 0.1);
        --glow-sun: 0 0 40px rgba(255, 107, 53, 0.3);
        --glow-aurora: 0 0 30px rgba(0, 229, 204, 0.2);
    }
    
    /* ═══════════════════════════════════════════════════════════════════════
       GLOBAL STYLES
    ═══════════════════════════════════════════════════════════════════════ */
    .stApp {
        background: linear-gradient(135deg, 
            var(--deep-space) 0%, 
            var(--space-gray) 50%,
            #0F1419 100%);
        background-attachment: fixed;
    }
    
    .stApp::before {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: 
            radial-gradient(ellipse at 20% 20%, rgba(255, 107, 53, 0.08) 0%, transparent 50%),
            radial-gradient(ellipse at 80% 80%, rgba(0, 229, 204, 0.06) 0%, transparent 50%),
            radial-gradient(ellipse at 50% 50%, rgba(94, 92, 230, 0.04) 0%, transparent 70%);
        pointer-events: none;
        z-index: 0;
    }
    
    /* Typography */
    h1, h2, h3, h4, h5, h6, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        font-family: 'Outfit', sans-serif !important;
        color: var(--star-white) !important;
        letter-spacing: -0.02em;
    }
    
    p, span, div, .stMarkdown p {
        font-family: 'Outfit', sans-serif !important;
        color: var(--comet-gray);
    }
    
    code, .stCode {
        font-family: 'JetBrains Mono', monospace !important;
    }
    
    /* ═══════════════════════════════════════════════════════════════════════
       SIDEBAR STYLING
    ═══════════════════════════════════════════════════════════════════════ */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, 
            var(--space-gray) 0%, 
            var(--deep-space) 100%) !important;
        border-right: 1px solid var(--glass-border);
    }
    
    [data-testid="stSidebar"] .stMarkdown h1 {
        background: linear-gradient(135deg, var(--helios-sun) 0%, var(--helios-amber) 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 800;
        font-size: 2rem;
        text-align: center;
        padding: 1rem 0;
    }
    
    /* ═══════════════════════════════════════════════════════════════════════
       METRIC CARDS
    ═══════════════════════════════════════════════════════════════════════ */
    [data-testid="stMetric"] {
        background: var(--glass-bg);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid var(--glass-border);
        border-radius: 16px;
        padding: 1.5rem;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    
    [data-testid="stMetric"]::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, var(--helios-sun), var(--aurora-cyan));
        opacity: 0;
        transition: opacity 0.3s ease;
    }
    
    [data-testid="stMetric"]:hover {
        transform: translateY(-4px);
        box-shadow: var(--glow-sun);
        border-color: rgba(255, 107, 53, 0.3);
    }
    
    [data-testid="stMetric"]:hover::before {
        opacity: 1;
    }
    
    [data-testid="stMetricLabel"] {
        font-family: 'Outfit', sans-serif !important;
        font-weight: 500;
        color: var(--comet-gray) !important;
        text-transform: uppercase;
        font-size: 0.75rem !important;
        letter-spacing: 0.1em;
    }
    
    [data-testid="stMetricValue"] {
        font-family: 'Outfit', sans-serif !important;
        font-weight: 700;
        color: var(--star-white) !important;
        font-size: 2rem !important;
    }
    
    [data-testid="stMetricDelta"] {
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.85rem !important;
    }
    
    /* ═══════════════════════════════════════════════════════════════════════
       CUSTOM COMPONENTS
    ═══════════════════════════════════════════════════════════════════════ */
    .hero-header {
        text-align: center;
        padding: 2rem 0 3rem;
        position: relative;
    }
    
    .hero-title {
        font-family: 'Playfair Display', serif !important;
        font-size: 3.5rem !important;
        font-weight: 700 !important;
        background: linear-gradient(135deg, 
            var(--helios-sun) 0%, 
            var(--helios-amber) 40%,
            var(--aurora-cyan) 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.5rem;
        letter-spacing: -0.03em;
        animation: shimmer 3s ease-in-out infinite;
    }
    
    @keyframes shimmer {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.85; }
    }
    
    .hero-subtitle {
        font-family: 'Outfit', sans-serif !important;
        font-size: 1.1rem !important;
        color: var(--comet-gray) !important;
        font-weight: 400;
        letter-spacing: 0.2em;
        text-transform: uppercase;
    }
    
    .glass-card {
        background: var(--glass-bg);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid var(--glass-border);
        border-radius: 20px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    
    .risk-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem 1rem;
        border-radius: 100px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.8rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    .risk-critical { 
        background: rgba(255, 69, 58, 0.15); 
        color: var(--risk-critical);
        border: 1px solid rgba(255, 69, 58, 0.3);
    }
    .risk-high { 
        background: rgba(255, 159, 10, 0.15); 
        color: var(--risk-high);
        border: 1px solid rgba(255, 159, 10, 0.3);
    }
    .risk-medium { 
        background: rgba(255, 214, 10, 0.15); 
        color: var(--risk-medium);
        border: 1px solid rgba(255, 214, 10, 0.3);
    }
    .risk-low { 
        background: rgba(48, 209, 88, 0.15); 
        color: var(--risk-low);
        border: 1px solid rgba(48, 209, 88, 0.3);
    }
    
    .stat-highlight {
        font-family: 'Outfit', sans-serif;
        font-size: 4rem;
        font-weight: 800;
        background: linear-gradient(135deg, var(--helios-sun), var(--helios-amber));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        line-height: 1;
    }
    
    .section-divider {
        height: 1px;
        background: linear-gradient(90deg, 
            transparent 0%, 
            var(--glass-border) 20%,
            var(--helios-sun) 50%,
            var(--glass-border) 80%,
            transparent 100%);
        margin: 2rem 0;
    }
    
    /* ═══════════════════════════════════════════════════════════════════════
       BUTTONS & INTERACTIONS
    ═══════════════════════════════════════════════════════════════════════ */
    .stButton > button {
        font-family: 'Outfit', sans-serif !important;
        font-weight: 600;
        background: linear-gradient(135deg, var(--helios-sun) 0%, var(--helios-coral) 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.75rem 2rem;
        transition: all 0.3s ease;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: var(--glow-sun);
    }
    
    /* Select boxes */
    .stSelectbox > div > div {
        background: var(--glass-bg) !important;
        border: 1px solid var(--glass-border) !important;
        border-radius: 12px !important;
        color: var(--star-white) !important;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
        background: var(--glass-bg);
        padding: 0.5rem;
        border-radius: 16px;
        border: 1px solid var(--glass-border);
    }
    
    .stTabs [data-baseweb="tab"] {
        font-family: 'Outfit', sans-serif !important;
        font-weight: 500;
        color: var(--comet-gray);
        border-radius: 12px;
        padding: 0.75rem 1.5rem;
        transition: all 0.3s ease;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, var(--helios-sun) 0%, var(--helios-coral) 100%) !important;
        color: white !important;
    }
    
    /* DataFrame styling */
    .stDataFrame {
        border-radius: 16px;
        overflow: hidden;
        border: 1px solid var(--glass-border);
    }
    
    /* Progress bar */
    .stProgress > div > div {
        background: linear-gradient(90deg, var(--helios-sun), var(--aurora-cyan));
        border-radius: 100px;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        font-family: 'Outfit', sans-serif !important;
        font-weight: 600;
        background: var(--glass-bg);
        border: 1px solid var(--glass-border);
        border-radius: 12px;
    }
    
    /* ═══════════════════════════════════════════════════════════════════════
       ANIMATIONS
    ═══════════════════════════════════════════════════════════════════════ */
    @keyframes pulse-glow {
        0%, 100% { box-shadow: 0 0 20px rgba(255, 107, 53, 0.3); }
        50% { box-shadow: 0 0 40px rgba(255, 107, 53, 0.5); }
    }
    
    @keyframes float {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-10px); }
    }
    
    .floating {
        animation: float 6s ease-in-out infinite;
    }
    
    /* ═══════════════════════════════════════════════════════════════════════
       RESPONSIVE ADJUSTMENTS
    ═══════════════════════════════════════════════════════════════════════ */
    @media (max-width: 768px) {
        .hero-title { font-size: 2.5rem !important; }
        .stat-highlight { font-size: 2.5rem; }
    }
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# DATA SIMULATION (Replace with Supabase connection)
# ═══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=300)
def load_data():
    """
    Simulated data based on Helios project specifications.
    In production, replace with Supabase queries.
    """
    np.random.seed(42)
    n_abitazioni = 3634
    
    # Italian cities with coordinates (weighted distribution)
    cities = {
        'Milano': (45.4642, 9.1900, 2), 'Roma': (41.9028, 12.4964, 2),
        'Napoli': (40.8518, 14.2681, 1), 'Torino': (45.0703, 7.6869, 3),
        'Palermo': (38.1157, 13.3615, 2), 'Genova': (44.4056, 8.9463, 3),
        'Bologna': (44.4949, 11.3426, 3), 'Firenze': (43.7696, 11.2558, 2),
        'Bari': (41.1171, 16.8719, 3), 'Catania': (37.5079, 15.0830, 1),
        'Venezia': (45.4408, 12.3155, 4), 'Verona': (45.4384, 10.9916, 3),
        'Messina': (38.1938, 15.5540, 1), "L'Aquila": (42.3498, 13.3995, 1),
        'Amatrice': (42.6286, 13.2868, 1), 'Norcia': (42.7931, 13.0927, 1)
    }
    
    city_names = list(cities.keys())
    weights = [0.15, 0.18, 0.12, 0.08, 0.06, 0.05, 0.07, 0.06, 0.05, 0.04, 
               0.03, 0.03, 0.02, 0.02, 0.02, 0.02]
    
    selected_cities = np.random.choice(city_names, n_abitazioni, p=weights)
    
    data = []
    for i, city in enumerate(selected_cities):
        lat, lon, zona_sismica = cities[city]
        # Add jitter for realistic distribution
        lat += np.random.normal(0, 0.05)
        lon += np.random.normal(0, 0.05)
        
        # Risk calculation based on seismic zone and random factors
        base_risk = (5 - zona_sismica) * 20  # Zone 1 = high risk
        hydro_risk = np.random.choice([0, 10, 25, 40], p=[0.5, 0.25, 0.15, 0.1])
        risk_score = min(100, base_risk + hydro_risk + np.random.randint(-10, 20))
        
        # Risk category
        if risk_score >= 80:
            risk_category = 'Critico'
        elif risk_score >= 60:
            risk_category = 'Alto'
        elif risk_score >= 40:
            risk_category = 'Medio'
        else:
            risk_category = 'Basso'
        
        # Hydrogeological risk
        hydro_labels = ['Nessuno', 'Alluvione P1', 'Alluvione P2/P3', 'Frana']
        hydro_idx = np.random.choice([0, 1, 2, 3], p=[0.55, 0.2, 0.15, 0.1])
        
        data.append({
            'id': f'HAB{str(i+1).zfill(5)}',
            'codice_cliente': f'CLI{str(np.random.randint(1000, 9999))}',
            'citta': city,
            'latitudine': lat,
            'longitudine': lon,
            'zona_sismica': zona_sismica,
            'rischio_idrogeologico': hydro_labels[hydro_idx],
            'risk_score': risk_score,
            'risk_category': risk_category,
            'solar_potential_kwh': np.random.randint(2800, 4500) if np.random.random() > 0.3 else None,
            'premio_attuale': np.random.randint(280, 650),
            'clv': np.random.randint(5000, 45000),
            'churn_probability': round(np.random.uniform(0.05, 0.45), 2)
        })
    
    return pd.DataFrame(data)


def get_risk_stats(df):
    """Calculate risk distribution statistics."""
    stats = df['risk_category'].value_counts()
    return {
        'critico': stats.get('Critico', 0),
        'alto': stats.get('Alto', 0),
        'medio': stats.get('Medio', 0),
        'basso': stats.get('Basso', 0),
        'total': len(df),
        'avg_score': round(df['risk_score'].mean(), 1),
        'high_risk_pct': round((stats.get('Critico', 0) + stats.get('Alto', 0)) / len(df) * 100, 1)
    }


# ═══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("# ☀️ HELIOS")
    st.markdown("---")
    
    st.markdown("### 🎯 Filtri Analisi")
    
    # Load data
    df = load_data()
    
    # City filter
    cities_list = ['Tutte le città'] + sorted(df['citta'].unique().tolist())
    selected_city = st.selectbox("📍 Città", cities_list)
    
    # Risk category filter
    risk_options = ['Tutti i rischi', 'Critico', 'Alto', 'Medio', 'Basso']
    selected_risk = st.selectbox("⚠️ Categoria Rischio", risk_options)
    
    # Seismic zone filter
    zone_options = ['Tutte le zone', 'Zona 1', 'Zona 2', 'Zona 3', 'Zona 4']
    selected_zone = st.selectbox("🌍 Zona Sismica", zone_options)
    
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
    
    # Quick stats in sidebar
    st.markdown("### 📊 Quick Stats")
    st.markdown(f"""
    <div class="glass-card">
        <p style="color: var(--comet-gray); margin: 0; font-size: 0.8rem;">ABITAZIONI FILTRATE</p>
        <p class="stat-highlight" style="font-size: 2.5rem; margin: 0.5rem 0;">{len(filtered_df):,}</p>
        <p style="color: var(--comet-gray); margin: 0; font-size: 0.8rem;">di {len(df):,} totali</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### 🔗 Connessioni")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("🟢 **Supabase**")
        st.markdown("🟢 **n8n**")
    with col2:
        st.markdown("🟢 **INGV**")
        st.markdown("🟢 **ISPRA**")
    
    st.markdown("---")
    st.markdown(
        "<p style='text-align: center; color: var(--comet-gray); font-size: 0.75rem;'>"
        "Progetto Helios v1.0<br>Generali AI Challenge 2024"
        "</p>",
        unsafe_allow_html=True
    )


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN CONTENT
# ═══════════════════════════════════════════════════════════════════════════════

# Hero Header
st.markdown("""
<div class="hero-header">
    <h1 class="hero-title">Progetto Helios</h1>
    <p class="hero-subtitle">Ecosistema Assicurativo Geo-Cognitivo</p>
</div>
""", unsafe_allow_html=True)

# Divider
st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

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
    st.metric(
        label="☀️ Potenziale Solare",
        value=f"{solar_coverage:,}",
        delta=f"{round(solar_coverage/len(filtered_df)*100)}% analizzati"
    )

with col5:
    avg_clv = filtered_df['clv'].mean()
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
        "<p style='color: var(--comet-gray);'>"
        "Visualizzazione geospaziale del portafoglio con indicatori di rischio sismico e idrogeologico. "
        "Ogni punto rappresenta un'abitazione assicurata."
        "</p>",
        unsafe_allow_html=True
    )
    
    # Map controls
    map_col1, map_col2, map_col3 = st.columns([2, 2, 1])
    
    with map_col1:
        map_style = st.selectbox(
            "Stile Mappa",
            ["Dark", "Satellite", "Light"],
            index=0
        )
    
    with map_col2:
        color_by = st.selectbox(
            "Colorazione per",
            ["Risk Score", "Zona Sismica", "CLV", "Churn Probability"],
            index=0
        )
    
    with map_col3:
        point_size = st.slider("Dimensione", 50, 300, 150)
    
    # Prepare map data
    map_df = filtered_df.copy()
    
    # Color mapping based on selection
    if color_by == "Risk Score":
        map_df['color_r'] = (map_df['risk_score'] * 2.55).astype(int)
        map_df['color_g'] = ((100 - map_df['risk_score']) * 2.55).astype(int)
        map_df['color_b'] = 50
    elif color_by == "Zona Sismica":
        zone_colors = {1: [255, 69, 58], 2: [255, 159, 10], 3: [255, 214, 10], 4: [48, 209, 88]}
        map_df['color_r'] = map_df['zona_sismica'].map(lambda x: zone_colors[x][0])
        map_df['color_g'] = map_df['zona_sismica'].map(lambda x: zone_colors[x][1])
        map_df['color_b'] = map_df['zona_sismica'].map(lambda x: zone_colors[x][2])
    elif color_by == "CLV":
        clv_norm = (map_df['clv'] - map_df['clv'].min()) / (map_df['clv'].max() - map_df['clv'].min())
        map_df['color_r'] = (255 * (1 - clv_norm)).astype(int)
        map_df['color_g'] = (215 * clv_norm).astype(int)
        map_df['color_b'] = 100
    else:  # Churn
        map_df['color_r'] = (map_df['churn_probability'] * 255).astype(int)
        map_df['color_g'] = ((1 - map_df['churn_probability']) * 200).astype(int)
        map_df['color_b'] = 100
    
    # Map style
    map_styles = {
        "Dark": "mapbox://styles/mapbox/dark-v10",
        "Satellite": "mapbox://styles/mapbox/satellite-v9",
        "Light": "mapbox://styles/mapbox/light-v10"
    }
    
    # Create PyDeck map
    view_state = pdk.ViewState(
        latitude=filtered_df['latitudine'].mean(),
        longitude=filtered_df['longitudine'].mean(),
        zoom=5.5,
        pitch=45,
        bearing=0
    )
    
    scatter_layer = pdk.Layer(
        "ScatterplotLayer",
        data=map_df,
        get_position=['longitudine', 'latitudine'],
        get_color=['color_r', 'color_g', 'color_b', 180],
        get_radius=point_size,
        pickable=True,
        auto_highlight=True,
        highlight_color=[255, 107, 53, 255]
    )
    
    # Heatmap layer (optional)
    heatmap_layer = pdk.Layer(
        "HeatmapLayer",
        data=map_df[map_df['risk_category'].isin(['Critico', 'Alto'])],
        get_position=['longitudine', 'latitudine'],
        get_weight='risk_score',
        aggregation='MEAN',
        opacity=0.3,
        radiusPixels=60
    )
    
    deck = pdk.Deck(
        layers=[heatmap_layer, scatter_layer],
        initial_view_state=view_state,
        map_style=map_styles[map_style],
        tooltip={
            "html": """
                <div style="font-family: Outfit; padding: 10px; background: rgba(13,17,23,0.95); border-radius: 8px; border: 1px solid rgba(255,107,53,0.3);">
                    <b style="color: #FF6B35; font-size: 14px;">{citta}</b><br>
                    <span style="color: #8B949E;">ID: {id}</span><br>
                    <hr style="border-color: rgba(255,255,255,0.1); margin: 8px 0;">
                    <span style="color: #F0F6FC;">🎯 Risk Score: <b>{risk_score}</b></span><br>
                    <span style="color: #F0F6FC;">🌍 Zona Sismica: <b>{zona_sismica}</b></span><br>
                    <span style="color: #F0F6FC;">💧 Idrogeo: {rischio_idrogeologico}</span><br>
                    <span style="color: #F0F6FC;">💎 CLV: €{clv}</span>
                </div>
            """,
            "style": {"backgroundColor": "transparent", "color": "white"}
        }
    )
    
    st.pydeck_chart(deck, use_container_width=True)
    
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
        # Risk Distribution Donut
        risk_counts = filtered_df['risk_category'].value_counts()
        
        fig_donut = go.Figure(data=[go.Pie(
            labels=risk_counts.index,
            values=risk_counts.values,
            hole=0.65,
            marker_colors=['#FF453A', '#FF9F0A', '#FFD60A', '#30D158'],
            textinfo='percent+label',
            textfont=dict(family='Outfit', size=12, color='white'),
            hovertemplate="<b>%{label}</b><br>%{value:,} abitazioni<br>%{percent}<extra></extra>"
        )])
        
        fig_donut.update_layout(
            title=dict(
                text="Distribuzione Rischio",
                font=dict(family='Outfit', size=18, color='#F0F6FC'),
                x=0.5
            ),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#8B949E'),
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.2,
                xanchor="center",
                x=0.5,
                font=dict(family='Outfit', size=11)
            ),
            annotations=[dict(
                text=f"<b>{len(filtered_df):,}</b><br>Totale",
                x=0.5, y=0.5,
                font=dict(family='Outfit', size=20, color='#F0F6FC'),
                showarrow=False
            )],
            height=400,
            margin=dict(t=60, b=60, l=20, r=20)
        )
        
        st.plotly_chart(fig_donut, use_container_width=True)
    
    with analytics_col2:
        # Seismic Zone Bar Chart
        zone_counts = filtered_df['zona_sismica'].value_counts().sort_index()
        
        fig_bar = go.Figure(data=[go.Bar(
            x=[f"Zona {z}" for z in zone_counts.index],
            y=zone_counts.values,
            marker=dict(
                color=['#FF453A', '#FF9F0A', '#FFD60A', '#30D158'][:len(zone_counts)],
                line=dict(color='rgba(255,255,255,0.2)', width=1)
            ),
            text=zone_counts.values,
            textposition='outside',
            textfont=dict(family='JetBrains Mono', size=12, color='#F0F6FC'),
            hovertemplate="<b>%{x}</b><br>%{y:,} abitazioni<extra></extra>"
        )])
        
        fig_bar.update_layout(
            title=dict(
                text="Distribuzione Zone Sismiche",
                font=dict(family='Outfit', size=18, color='#F0F6FC'),
                x=0.5
            ),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#8B949E'),
            xaxis=dict(
                showgrid=False,
                tickfont=dict(family='Outfit', size=12)
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor='rgba(255,255,255,0.05)',
                tickfont=dict(family='JetBrains Mono', size=11)
            ),
            height=400,
            margin=dict(t=60, b=40, l=40, r=40)
        )
        
        st.plotly_chart(fig_bar, use_container_width=True)
    
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    
    # Second row of charts
    analytics_col3, analytics_col4 = st.columns(2)
    
    with analytics_col3:
        # CLV vs Risk Score Scatter
        fig_scatter = px.scatter(
            filtered_df,
            x='risk_score',
            y='clv',
            color='risk_category',
            color_discrete_map={
                'Critico': '#FF453A',
                'Alto': '#FF9F0A',
                'Medio': '#FFD60A',
                'Basso': '#30D158'
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
                font=dict(family='Outfit', size=18, color='#F0F6FC'),
                x=0.5
            ),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#8B949E', family='Outfit'),
            xaxis=dict(
                showgrid=True,
                gridcolor='rgba(255,255,255,0.05)',
                title_font=dict(size=12)
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor='rgba(255,255,255,0.05)',
                title_font=dict(size=12)
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.3,
                xanchor="center",
                x=0.5
            ),
            height=400,
            margin=dict(t=60, b=80, l=60, r=40)
        )
        
        st.plotly_chart(fig_scatter, use_container_width=True)
    
    with analytics_col4:
        # Hydrogeological Risk Breakdown
        hydro_counts = filtered_df['rischio_idrogeologico'].value_counts()
        
        fig_hydro = go.Figure(data=[go.Bar(
            y=hydro_counts.index,
            x=hydro_counts.values,
            orientation='h',
            marker=dict(
                color=['#30D158', '#0A84FF', '#5E5CE6', '#FF453A'][:len(hydro_counts)],
                line=dict(color='rgba(255,255,255,0.2)', width=1)
            ),
            text=hydro_counts.values,
            textposition='outside',
            textfont=dict(family='JetBrains Mono', size=11, color='#F0F6FC'),
            hovertemplate="<b>%{y}</b><br>%{x:,} abitazioni<extra></extra>"
        )])
        
        fig_hydro.update_layout(
            title=dict(
                text="Rischio Idrogeologico",
                font=dict(family='Outfit', size=18, color='#F0F6FC'),
                x=0.5
            ),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#8B949E'),
            xaxis=dict(
                showgrid=True,
                gridcolor='rgba(255,255,255,0.05)',
                tickfont=dict(family='JetBrains Mono', size=11)
            ),
            yaxis=dict(
                showgrid=False,
                tickfont=dict(family='Outfit', size=12)
            ),
            height=400,
            margin=dict(t=60, b=40, l=120, r=60)
        )
        
        st.plotly_chart(fig_hydro, use_container_width=True)
    
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    
    # City breakdown
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
            colorscale=[[0, '#30D158'], [0.5, '#FFD60A'], [1, '#FF453A']],
            line=dict(color='rgba(255,255,255,0.2)', width=1)
        ),
        text=[f"{x:.0f}" for x in city_risk['risk_score']],
        textposition='outside',
        textfont=dict(family='JetBrains Mono', size=11, color='#F0F6FC'),
        hovertemplate="<b>%{x}</b><br>Risk Score: %{y:.1f}<br>Abitazioni: %{customdata[0]:,}<br>CLV Totale: €%{customdata[1]:,.0f}<extra></extra>",
        customdata=city_risk[['n_abitazioni', 'clv_totale']].values
    )])
    
    fig_city.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#8B949E', family='Outfit'),
        xaxis=dict(
            showgrid=False,
            tickfont=dict(size=11),
            tickangle=-45
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='rgba(255,255,255,0.05)',
            title="Risk Score Medio",
            title_font=dict(size=12),
            range=[0, 100]
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
    
    # Display as cards
    for idx, row in display_df.head(20).iterrows():
        risk_class = row['risk_category'].lower()
        solar_info = f"☀️ {row['solar_potential_kwh']:,} kWh/anno" if pd.notna(row['solar_potential_kwh']) else "☀️ Non calcolato"
        
        st.markdown(f"""
        <div class="glass-card" style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem;">
            <div style="flex: 1; min-width: 200px;">
                <h4 style="margin: 0; color: var(--star-white); font-size: 1.1rem;">{row['id']}</h4>
                <p style="margin: 0.25rem 0; color: var(--comet-gray); font-size: 0.85rem;">
                    📍 {row['citta']} · {row['codice_cliente']}
                </p>
            </div>
            <div style="display: flex; gap: 1.5rem; flex-wrap: wrap; align-items: center;">
                <div style="text-align: center;">
                    <p style="margin: 0; color: var(--comet-gray); font-size: 0.7rem; text-transform: uppercase;">Risk Score</p>
                    <p style="margin: 0; color: var(--star-white); font-size: 1.5rem; font-weight: 700;">{row['risk_score']}</p>
                </div>
                <div style="text-align: center;">
                    <p style="margin: 0; color: var(--comet-gray); font-size: 0.7rem; text-transform: uppercase;">Zona</p>
                    <p style="margin: 0; color: var(--star-white); font-size: 1.5rem; font-weight: 700;">{row['zona_sismica']}</p>
                </div>
                <div style="text-align: center;">
                    <p style="margin: 0; color: var(--comet-gray); font-size: 0.7rem; text-transform: uppercase;">CLV</p>
                    <p style="margin: 0; color: var(--star-white); font-size: 1.5rem; font-weight: 700;">€{row['clv']:,}</p>
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


# ═══════════════════════════════════════════════════════════════════════════════
# FOOTER
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

footer_col1, footer_col2, footer_col3 = st.columns(3)

with footer_col1:
    st.markdown("""
    <p style="color: var(--comet-gray); font-size: 0.8rem;">
    <strong>Data Sources:</strong><br>
    🌍 INGV - Classificazione Sismica<br>
    💧 ISPRA - IdroGEO Platform<br>
    ☀️ EC PVGIS - Solar Potential
    </p>
    """, unsafe_allow_html=True)

with footer_col2:
    st.markdown("""
    <p style="text-align: center; color: var(--comet-gray); font-size: 0.8rem;">
    <strong>Progetto Helios</strong><br>
    Ecosistema Assicurativo Geo-Cognitivo<br>
    Generali AI Challenge 2024
    </p>
    """, unsafe_allow_html=True)

with footer_col3:
    st.markdown(f"""
    <p style="text-align: right; color: var(--comet-gray); font-size: 0.8rem;">
    <strong>Last Update:</strong><br>
    {datetime.now().strftime('%d/%m/%Y %H:%M')}<br>
    v1.0.0 FluidView
    </p>
    """, unsafe_allow_html=True)
