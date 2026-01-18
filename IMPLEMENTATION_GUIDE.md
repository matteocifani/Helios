# Helios Dashboard - Guida Completa all'Implementazione UX/UI

## Panoramica

Questa guida descrive passo per passo come trasformare la dashboard Helios attuale in una dashboard personalizzata per l'agente **Mario Rossi** di **Bologna, Emilia Romagna**.

### Riepilogo delle Modifiche Principali

| Area | Stato Attuale | Nuovo Stato |
|------|---------------|-------------|
| Navigazione | Sidebar con radio buttons | Menu orizzontale in alto |
| Modalità | "Helios View" / "Helios NBO" | "Policy Advisor" / "Analytics" |
| Profilo Utente | Generico "Agente Vita Sicura" | Mario Rossi con avatar (top-right) |
| Visualizzazione Clienti | Tecnica (mostra codice_cliente, score numerico) | User-friendly con icone polizze e barre visive |
| Icone Polizze | Emoji generiche | Icone SVG custom per ogni polizza |
| Score | Numerico (es. "87.3") | Barra progresso + etichetta (Eccellente/Alta/Media/Bassa) |
| Focus Regionale | Tutta Italia | Emilia Romagna (pre-filtrato) |

---

## File da Modificare

1. **`app.py`** - File principale (~2750 righe)
2. **`src/config/constants.py`** - Costanti e icone

---

## STEP 1: Aggiungere Icone SVG Polizze in constants.py

**File:** `src/config/constants.py`

**Posizione:** Dopo la riga `DEFAULT_SEISMIC_ZONE: int = 4` (circa riga 57), aggiungere:

```python
# ═══════════════════════════════════════════════════════════════════════════════
# POLICY ICONS - Custom SVG Icons for Insurance Products
# ═══════════════════════════════════════════════════════════════════════════════

POLICY_ICONS = {
    "Polizza Salute e Infortuni: Salute Protetta": {
        "svg": '''<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z" fill="#EF4444"/>
            <path d="M12 8v4m-2-2h4" stroke="white" stroke-width="1.5" stroke-linecap="round"/>
        </svg>''',
        "color": "#EF4444",
        "label": "Salute",
        "short": "Salute"
    },
    "Assicurazione Casa e Famiglia: Casa Serena": {
        "svg": '''<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" stroke="#F59E0B" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>''',
        "color": "#F59E0B",
        "label": "Casa",
        "short": "Casa"
    },
    "Polizza Vita a Premio Unico: Futuro Sicuro": {
        "svg": '''<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" stroke="#10B981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <circle cx="7" cy="17" r="2" fill="#10B981"/>
        </svg>''',
        "color": "#10B981",
        "label": "Investimento",
        "short": "Invest"
    },
    "Polizza Vita a Premi Ricorrenti: Risparmio Costante": {
        "svg": '''<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2z" fill="#3B82F6" fill-opacity="0.2"/>
            <path d="M12 6v6l4 2" stroke="#3B82F6" stroke-width="2" stroke-linecap="round"/>
            <path d="M17 12a5 5 0 11-10 0 5 5 0 0110 0z" stroke="#3B82F6" stroke-width="1.5"/>
            <circle cx="12" cy="12" r="1.5" fill="#3B82F6"/>
        </svg>''',
        "color": "#3B82F6",
        "label": "Risparmio",
        "short": "Risp"
    },
    "Piano Individuale Pensionistico (PIP): Pensione Serenità": {
        "svg": '''<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 2L2 8.5V12c0 5.55 4.27 10.74 10 12 5.73-1.26 10-6.45 10-12V8.5L12 2z" fill="#8B5CF6" fill-opacity="0.2" stroke="#8B5CF6" stroke-width="1.5"/>
            <path d="M12 8v4m0 4h.01" stroke="#8B5CF6" stroke-width="2" stroke-linecap="round"/>
        </svg>''',
        "color": "#8B5CF6",
        "label": "Pensione",
        "short": "PIP"
    }
}

# ═══════════════════════════════════════════════════════════════════════════════
# EMILIA ROMAGNA PROVINCES (for regional filtering)
# ═══════════════════════════════════════════════════════════════════════════════

EMILIA_ROMAGNA_PROVINCES = [
    'Bologna', 'Modena', 'Reggio Emilia', 'Parma',
    'Piacenza', 'Ferrara', 'Ravenna', 'Forlì-Cesena', 'Rimini'
]

# Bologna coordinates (for map centering)
BOLOGNA_COORDINATES = {
    'lat': 44.4949,
    'lon': 11.3426
}
```

---

## STEP 2: Modificare Session State in app.py

**File:** `app.py`

**Posizione:** Righe 762-786 (sezione SESSION STATE INITIALIZATION)

**Sostituire le righe 762-786 con:**

```python
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
```

---

## STEP 3: Rimuovere la Sidebar e Aggiungere Top Navigation

**File:** `app.py`

### 3.1 Nascondere la Sidebar con CSS

**Posizione:** Nella sezione CSS (riga ~55), dopo `@import url(...)` aggiungere:

```css
/* Hide sidebar completely for new navigation */
[data-testid="stSidebar"] {
    display: none !important;
}
[data-testid="stSidebarNav"] {
    display: none !important;
}
.css-1d391kg {
    display: none !important;
}
```

### 3.2 Eliminare il Blocco Sidebar

**Posizione:** Eliminare TUTTO il blocco `with st.sidebar:` dalle righe 792-1018.

**ELIMINA da riga 792:**
```python
with st.sidebar:
    # ... tutto il contenuto ...
```

**FINO a riga 1018** (fine del blocco sidebar).

### 3.3 Aggiungere Top Navigation Bar

**Posizione:** Dopo la sezione SESSION STATE (dopo riga ~786 modificata), aggiungere:

```python
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

# Create top navigation columns
nav_col1, nav_col2, nav_col3, nav_col4, nav_col5 = st.columns([2, 2, 2, 3, 2])

with nav_col1:
    st.markdown("""
    <div class="nav-logo">
        <svg width="32" height="32" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
            <defs>
                <linearGradient id="navTealGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stop-color="#00A0B0"/>
                    <stop offset="100%" stop-color="#00C9D4"/>
                </linearGradient>
            </defs>
            <circle cx="50" cy="50" r="20" fill="none" stroke="url(#navTealGrad)" stroke-width="2"/>
            <circle cx="50" cy="50" r="35" fill="none" stroke="url(#navTealGrad)" stroke-width="1.5"/>
            <g stroke="url(#navTealGrad)" stroke-width="2">
                <line x1="50" y1="10" x2="50" y2="25"/>
                <line x1="50" y1="75" x2="50" y2="90"/>
                <line x1="10" y1="50" x2="25" y2="50"/>
                <line x1="75" y1="50" x2="90" y2="50"/>
            </g>
        </svg>
        <span class="nav-logo-text">HELIOS</span>
    </div>
    """, unsafe_allow_html=True)

with nav_col2:
    if st.button(
        "Policy Advisor",
        key="nav_policy_advisor",
        type="primary" if st.session_state.active_mode == 'policy_advisor' else "secondary",
        use_container_width=True
    ):
        st.session_state.active_mode = 'policy_advisor'
        st.session_state.dashboard_mode = 'Helios NBO'  # Map to legacy mode
        st.rerun()

with nav_col3:
    if st.button(
        "Analytics",
        key="nav_analytics",
        type="primary" if st.session_state.active_mode == 'analytics' else "secondary",
        use_container_width=True
    ):
        st.session_state.active_mode = 'analytics'
        st.session_state.dashboard_mode = 'Helios View'  # Map to legacy mode
        st.rerun()

with nav_col4:
    pass  # Spacer

with nav_col5:
    # User profile
    agent = st.session_state.agent_profile
    st.markdown(f"""
    <div class="user-profile">
        <div class="avatar-circle">{agent['initials']}</div>
        <div class="user-info">
            <span class="user-name">{agent['name']}</span>
            <span class="user-location">{agent['city']}, {agent['region']}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
```

---

## STEP 4: Aggiungere Helper Functions per Score e Icone

**File:** `app.py`

**Posizione:** Dopo la funzione `get_all_recommendations` (riga ~738), aggiungere:

```python
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

    Args:
        policies: List of policy names

    Returns:
        HTML string with SVG icons
    """
    from src.config.constants import POLICY_ICONS

    icons_html = '<div class="policy-icons">'

    for policy in policies:
        if policy in POLICY_ICONS:
            icon_data = POLICY_ICONS[policy]
            icons_html += f'<div class="policy-icon" title="{icon_data["label"]}">{icon_data["svg"]}</div>'

    icons_html += '</div>'
    return icons_html


def get_premium_clients(nbo_data: list, weights: dict, top_n: int = 5) -> list:
    """
    Get top premium clients with BOTH high CLV and high NBO score.

    Criteria:
    - CLV in top 25% (top quartile)
    - NBO Score > 60
    - Sorted by combined ranking
    """
    # Get all recommendations with scores
    all_recs = get_all_recommendations(nbo_data, weights, filter_top20=True)

    # Calculate CLV threshold (top 25%)
    clv_values = [rec['client_data']['metadata']['clv_stimato'] for rec in all_recs]
    if not clv_values:
        return []

    clv_threshold = sorted(clv_values, reverse=True)[len(clv_values) // 4] if len(clv_values) > 4 else min(clv_values)

    # Filter for premium clients
    premium_clients = []
    for rec in all_recs:
        clv = rec['client_data']['metadata']['clv_stimato']
        if clv >= clv_threshold and rec['score'] >= 60:
            premium_clients.append(rec)

    # Sort by combined score (CLV weight + NBO score)
    # Normalize CLV to 0-100 scale for fair comparison
    if premium_clients:
        max_clv = max(r['client_data']['metadata']['clv_stimato'] for r in premium_clients)
        for rec in premium_clients:
            normalized_clv = (rec['client_data']['metadata']['clv_stimato'] / max_clv) * 100
            rec['combined_score'] = (normalized_clv * 0.4) + (rec['score'] * 0.6)

        premium_clients.sort(key=lambda x: x['combined_score'], reverse=True)

    return premium_clients[:top_n]
```

---

## STEP 5: Modificare Policy Advisor Mode (ex NBO Dashboard)

**File:** `app.py`

**Posizione:** Sostituire la sezione NBO MAIN DASHBOARD VIEW (righe 2396-2693) con:

```python
        else:
            # ═══════════════════════════════════════════════════════════════════════════════
            # POLICY ADVISOR MAIN VIEW
            # ═══════════════════════════════════════════════════════════════════════════════

            # Get all recommendations with current weights
            all_recs = get_all_recommendations(nbo_data, st.session_state.nbo_weights)

            # ═══════════════════════════════════════════════════════════════════════════════
            # SECTION 1: TOP 5 PREMIUM CLIENTS
            # ═══════════════════════════════════════════════════════════════════════════════

            st.markdown("""
            <h2 style="font-family: 'Playfair Display', serif; color: #1B3A5F; font-size: 1.5rem; margin-bottom: 0.5rem;">
                I tuoi clienti più preziosi
            </h2>
            <p style="color: #64748B; font-size: 0.9rem; margin-bottom: 1.5rem;">
                Clienti con alto valore e le migliori opportunità di vendita
            </p>
            """, unsafe_allow_html=True)

            # Get premium clients
            premium_clients = get_premium_clients(nbo_data, st.session_state.nbo_weights, top_n=5)

            if premium_clients:
                # Display as 5 horizontal cards
                premium_cols = st.columns(5)

                for idx, rec in enumerate(premium_clients):
                    with premium_cols[idx]:
                        client = rec['client_data']
                        score_display = get_score_display(rec['score'])
                        clv = client['metadata']['clv_stimato']

                        # Get policy icons
                        policies = client['metadata'].get('prodotti_posseduti', [])
                        if isinstance(policies, str):
                            policies = [policies]
                        policy_icons = render_policy_icons(policies)

                        st.markdown(f"""
                        <div class="glass-card" style="text-align: center; padding: 1.25rem; height: 100%;">
                            <div style="display: flex; align-items: center; justify-content: center; gap: 0.5rem; margin-bottom: 0.75rem;">
                                <span style="background: linear-gradient(135deg, #F59E0B 0%, #FBBF24 100%); color: white; padding: 0.2rem 0.5rem; border-radius: 100px; font-size: 0.7rem; font-weight: 700;">#{idx + 1}</span>
                            </div>
                            <h4 style="margin: 0; color: #1B3A5F; font-size: 0.95rem; font-weight: 600; line-height: 1.3;">
                                {rec['nome']} {rec['cognome']}
                            </h4>

                            <div style="margin: 1rem 0;">
                                {render_opportunity_bar(rec['score'])}
                            </div>

                            <p style="margin: 0.5rem 0; color: #64748B; font-size: 0.8rem;">
                                CLV: <span style="color: #00A0B0; font-weight: 600;">€{clv:,}</span>
                            </p>

                            <div style="margin: 0.75rem 0; display: flex; justify-content: center;">
                                {policy_icons}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                        if st.button("Vedi dettagli", key=f"premium_{idx}", use_container_width=True):
                            st.session_state.nbo_page = 'detail'
                            st.session_state.nbo_selected_client = client
                            st.session_state.nbo_selected_recommendation = rec['recommendation']
                            st.rerun()
            else:
                st.info("Nessun cliente premium trovato con i criteri attuali.")

            st.markdown("<br><br>", unsafe_allow_html=True)

            # ═══════════════════════════════════════════════════════════════════════════════
            # SECTION 2: TOP 20 OPPORTUNITIES
            # ═══════════════════════════════════════════════════════════════════════════════

            st.markdown("""
            <h2 style="font-family: 'Playfair Display', serif; color: #1B3A5F; font-size: 1.5rem; margin-bottom: 0.5rem;">
                Le migliori opportunità di vendita per te
            </h2>
            <p style="color: #64748B; font-size: 0.9rem; margin-bottom: 1rem;">
                Raccomandazioni ordinate per potenziale, già filtrate per eleggibilità commerciale
            </p>
            """, unsafe_allow_html=True)

            # Info box about filtering (subtle)
            st.markdown("""
            <div style="background: #F8FAFC; border: 1px solid #E2E8F0; padding: 0.5rem 1rem; margin-bottom: 1rem; border-radius: 8px; display: inline-block;">
                <p style="margin: 0; color: #64748B; font-size: 0.75rem;">
                    ℹ️ Esclusi clienti con interazioni recenti (email, chiamate, polizze, reclami, sinistri)
                </p>
            </div>
            """, unsafe_allow_html=True)

            # Display Top 20 as compact list
            for i, rec in enumerate(all_recs[:20]):
                client = rec['client_data']
                score_display = get_score_display(rec['score'])

                # Get policy icons
                policies = client['metadata'].get('prodotti_posseduti', [])
                if isinstance(policies, str):
                    policies = [policies]
                policy_icons = render_policy_icons(policies)

                col_card, col_btn = st.columns([6, 1])

                with col_card:
                    st.markdown(f"""
                    <div class="glass-card" style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem; padding: 1rem 1.5rem;">
                        <div style="display: flex; align-items: center; gap: 1rem; flex: 2; min-width: 200px;">
                            <span style="background: #F3F4F6; color: #64748B; padding: 0.25rem 0.6rem; border-radius: 100px; font-size: 0.75rem; font-weight: 600; min-width: 28px; text-align: center;">{i+1}</span>
                            <div>
                                <h4 style="margin: 0; color: #1B3A5F; font-size: 0.95rem; font-weight: 600;">{rec['nome']} {rec['cognome']}</h4>
                                <p style="margin: 0.15rem 0 0; color: #94A3B8; font-size: 0.75rem;">{rec['prodotto']}</p>
                            </div>
                        </div>

                        <div style="flex: 1; min-width: 120px;">
                            {render_opportunity_bar(rec['score'])}
                        </div>

                        <div style="flex: 1; min-width: 100px; display: flex; justify-content: center;">
                            {policy_icons}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                with col_btn:
                    if st.button("Dettagli", key=f"top20_{i}", use_container_width=True):
                        st.session_state.nbo_page = 'detail'
                        st.session_state.nbo_selected_client = client
                        st.session_state.nbo_selected_recommendation = rec['recommendation']
                        st.rerun()
```

---

## STEP 6: Modificare Analytics Mode (Pre-filtro Emilia Romagna)

**File:** `app.py`

**Posizione:** Nella sezione Helios View (righe 1172+), modificare il ViewState della mappa e aggiungere filtro regionale.

### 6.1 Aggiungere Filtro Regionale

**Prima della creazione della mappa (circa riga 1270)**, aggiungere:

```python
# Pre-filter to Emilia Romagna for Analytics mode
from src.config.constants import EMILIA_ROMAGNA_PROVINCES, BOLOGNA_COORDINATES

# Filter dataframe to Emilia Romagna provinces
# This assumes 'provincia' or 'citta' column contains province/city names
if 'provincia' in filtered_df.columns:
    emilia_mask = filtered_df['provincia'].str.contains('|'.join(EMILIA_ROMAGNA_PROVINCES), case=False, na=False)
elif 'citta' in filtered_df.columns:
    emilia_mask = filtered_df['citta'].str.contains('|'.join(EMILIA_ROMAGNA_PROVINCES), case=False, na=False)
else:
    emilia_mask = pd.Series([True] * len(filtered_df))

filtered_df = filtered_df[emilia_mask]
```

### 6.2 Centrare Mappa su Bologna

**Modificare il ViewState (circa riga 1298):**

```python
# View State (centered on Bologna)
view_state = pdk.ViewState(
    latitude=BOLOGNA_COORDINATES['lat'],  # 44.4949
    longitude=BOLOGNA_COORDINATES['lon'],  # 11.3426
    zoom=8,  # Regional view
    pitch=0,
)
```

---

## STEP 7: Modificare Client Detail View per CV Features

**File:** `app.py`

**Posizione:** Nella sezione CV Features (righe 2157-2245), sostituire con:

```python
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

            # CV detections
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
```

---

## STEP 8: Aggiornare Import in app.py

**File:** `app.py`

**Posizione:** Inizio file, negli import (righe 26-38), aggiungere:

```python
from src.config.constants import (
    DEFAULT_SEISMIC_ZONE,
    SEISMIC_ZONE_COLORS,
    ABITAZIONI_COLUMNS,
    POLICY_ICONS,  # Aggiungere
    EMILIA_ROMAGNA_PROVINCES,  # Aggiungere
    BOLOGNA_COORDINATES,  # Aggiungere
)
```

---

## Checklist di Verifica

Dopo l'implementazione, verificare:

- [ ] **Navigazione:** I pulsanti "Policy Advisor" e "Analytics" cambiano modalità
- [ ] **Profilo utente:** Mario Rossi appare in alto a destra con avatar "MR"
- [ ] **Top 5 Premium:** Mostra 5 card con clienti alto CLV + alto score
- [ ] **Barra opportunità:** Nessun numero, solo barra + label (Eccellente/Alta/Media/Bassa)
- [ ] **Icone polizze:** SVG custom per ogni tipo di polizza
- [ ] **Top 20:** Lista compatta con barre e icone, senza codice_cliente visibile
- [ ] **CV Features:** Sezione "Cosa sappiamo dell'abitazione" nel dettaglio cliente
- [ ] **Analytics:** Mappa centrata su Bologna, dati filtrati per Emilia Romagna
- [ ] **Sidebar:** Completamente rimossa/nascosta

---

## Note Tecniche

### Dipendenze
- Nessuna nuova dipendenza richiesta
- Usa solo librerie già presenti nel progetto (streamlit, pandas, plotly, pydeck)

### Performance
- Le icone SVG sono inline per evitare chiamate HTTP
- Il calcolo dei Premium Clients è cacheable
- I filtri regionali sono applicati server-side

### Compatibilità
- Le variabili legacy (`dashboard_mode`, `user_name`, etc.) sono mantenute per retrocompatibilità
- La transizione può essere graduale

---

*Documento generato per il progetto Helios - AI Challenge Generali x Bicocca*
*Versione: 1.0 | Data: Gennaio 2026*
