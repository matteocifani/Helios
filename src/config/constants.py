"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                         HELIOS PROJECT CONSTANTS                              ║
║                    Centralized Configuration Values                           ║
╚═══════════════════════════════════════════════════════════════════════════════╝

This module contains all hardcoded constants extracted from the codebase for
easier maintenance and consistency across the project.
"""

from typing import Dict, List

# ═══════════════════════════════════════════════════════════════════════════════
# RISK ASSESSMENT CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

# Risk score thresholds (0-100 scale)
RISK_LOW_THRESHOLD: int = 40
RISK_MEDIUM_THRESHOLD: int = 60
RISK_HIGH_THRESHOLD: int = 80

# Risk categories
RISK_CATEGORY_LOW: str = "Basso"
RISK_CATEGORY_MEDIUM: str = "Medio"
RISK_CATEGORY_HIGH: str = "Alto"
RISK_CATEGORY_CRITICAL: str = "Critico"
RISK_CATEGORY_UNASSESSED: str = "Non valutato"

# Risk colors (for UI display) - Light theme optimized
RISK_COLORS: Dict[str, str] = {
    RISK_CATEGORY_CRITICAL: "#DC2626",  # Red (darker for light bg)
    RISK_CATEGORY_HIGH: "#EA580C",      # Orange
    RISK_CATEGORY_MEDIUM: "#CA8A04",    # Amber
    RISK_CATEGORY_LOW: "#16A34A",       # Green
}

# Risk background colors (for badges on light theme)
RISK_BG_COLORS: Dict[str, str] = {
    RISK_CATEGORY_CRITICAL: "#FEE2E2",  # Light red
    RISK_CATEGORY_HIGH: "#FFEDD5",      # Light orange
    RISK_CATEGORY_MEDIUM: "#FEF9C3",    # Light yellow
    RISK_CATEGORY_LOW: "#DCFCE7",       # Light green
}

# ═══════════════════════════════════════════════════════════════════════════════
# SEISMIC ZONE MAPPINGS (INGV Classification)
# ═══════════════════════════════════════════════════════════════════════════════

SEISMIC_ZONES: Dict[int, Dict[str, any]] = {
    1: {"level": "Molto Alto", "score": 90, "description": "Zona sismica 1 - Rischio molto alto"},
    2: {"level": "Alto", "score": 70, "description": "Zona sismica 2 - Rischio alto"},
    3: {"level": "Medio", "score": 40, "description": "Zona sismica 3 - Rischio medio"},
    4: {"level": "Basso", "score": 15, "description": "Zona sismica 4 - Rischio basso"},
}

# Default seismic zone if missing
DEFAULT_SEISMIC_ZONE: int = 4

# Zone color mapping for map visualization
SEISMIC_ZONE_COLORS: Dict[int, List[int]] = {
    1: [255, 69, 58],    # Red (RGB)
    2: [255, 159, 10],   # Orange
    3: [255, 214, 10],   # Yellow
    4: [48, 209, 88],    # Green
}

# ═══════════════════════════════════════════════════════════════════════════════
# HYDROGEOLOGICAL RISK THRESHOLDS
# ═══════════════════════════════════════════════════════════════════════════════

HYDRO_RISK_P3_THRESHOLD: float = 5.0   # Percentage threshold for P3 (medium-high risk)
HYDRO_RISK_P2_THRESHOLD: float = 5.0   # Percentage threshold for P2 (medium risk)
FLOOD_RISK_P4_THRESHOLD: float = 10.0  # Percentage threshold for P4 (very high risk)
FLOOD_RISK_P3_THRESHOLD: float = 10.0  # Percentage threshold for P3 (high risk)

HYDRO_RISK_SCORE_HIGH: int = 80
HYDRO_RISK_SCORE_MEDIUM: int = 50
HYDRO_RISK_SCORE_LOW: int = 20

FLOOD_RISK_SCORE_CRITICAL: int = 90
FLOOD_RISK_SCORE_HIGH: int = 60
FLOOD_RISK_SCORE_LOW: int = 25

# ═══════════════════════════════════════════════════════════════════════════════
# INSURANCE PRODUCTS & PREMIUMS
# ═══════════════════════════════════════════════════════════════════════════════

# Base annual premiums (in euros) before risk adjustment
BASE_PREMIUMS: Dict[str, int] = {
    "NatCat": 650,                      # Natural Catastrophe (earthquake + flood)
    "CasaSerena": 380,                  # Home + Contents
    "FuturoSicuro": 1200,               # Life + Investment
    "InvestimentoFlessibile": 800,      # Flexible Investment
    "SaluteProtetta": 950,              # Health Protection
    "GreenHome": 520,                   # Green Technology
    "Multiramo": 850,                   # Multi-branch
}

# Default premium if product not found
DEFAULT_BASE_PREMIUM: int = 500

# Default coverage amount (in euros)
DEFAULT_COVERAGE_AMOUNT: int = 100000

# ═══════════════════════════════════════════════════════════════════════════════
# SOLAR POTENTIAL ESTIMATION
# ═══════════════════════════════════════════════════════════════════════════════

# Solar production estimates by latitude (kWh per kWp per year)
SOLAR_KWH_PER_KWP_NORTH: int = 1400   # Latitude > 42° (Northern Italy)
SOLAR_KWH_PER_KWP_CENTER: int = 1500  # Latitude 40-42° (Central Italy)
SOLAR_KWH_PER_KWP_SOUTH: int = 1600   # Latitude < 40° (Southern Italy)

# System parameters
SOLAR_DEFAULT_SYSTEM_SIZE_KW: float = 3.0   # Default system size in kW
SOLAR_SYSTEM_EFFICIENCY: float = 0.85        # System efficiency factor (losses)
SOLAR_ELECTRICITY_PRICE_EUR_KWH: float = 0.25  # Electricity price (€/kWh)
SOLAR_FIXED_ANNUAL_COST: int = 100           # Fixed annual maintenance cost (€)
SOLAR_AVERAGE_HOME_CONSUMPTION_KWH: int = 3500  # Average home yearly consumption
SOLAR_SYSTEM_COST_EUR: int = 6000            # Average system installation cost

# Latitude thresholds
SOLAR_LATITUDE_NORTH_THRESHOLD: float = 42.0
SOLAR_LATITUDE_CENTER_THRESHOLD: float = 40.0

# ═══════════════════════════════════════════════════════════════════════════════
# DATABASE & API CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

# Pagination settings
DB_CHUNK_SIZE: int = 1000              # Number of rows per API request
DB_MAX_SEARCH_RESULTS: int = 20        # Max results for search queries

# Cache TTL (Time To Live) in seconds
CACHE_TTL_SHORT: int = 1800            # 30 minutes (increased for better performance)
CACHE_TTL_MEDIUM: int = 600            # 10 minutes (for reference data)
CACHE_TTL_LONG: int = 3600             # 1 hour (for static data)

# API timeout settings (in seconds)
API_TIMEOUT_DEFAULT: int = 60          # Default timeout for external APIs
API_TIMEOUT_SHORT: int = 30            # Timeout for fast operations
API_TIMEOUT_EMBEDDING: int = 30        # Timeout for embedding generation

# Retry settings
API_MAX_RETRIES: int = 3
API_RETRY_DELAY_SECONDS: float = 1.0

# ═══════════════════════════════════════════════════════════════════════════════
# UI CONFIGURATION - Vita Sicura Light Theme
# ═══════════════════════════════════════════════════════════════════════════════

# Primary Colors (from Vita Sicura logo)
COLOR_VS_NAVY: str = "#1B3A5F"           # Main brand color - text, headers
COLOR_VS_NAVY_LIGHT: str = "#2C5282"     # Secondary navy
COLOR_VS_TEAL: str = "#00A0B0"           # Primary accent - CTAs, highlights
COLOR_VS_CYAN: str = "#00C9D4"           # Hover states, gradients
COLOR_VS_AQUA: str = "#B8E6E8"           # Soft backgrounds, accents

# Backgrounds (Light Mode)
COLOR_BG_WHITE: str = "#FFFFFF"          # Main background
COLOR_BG_OFF_WHITE: str = "#FAFBFC"      # Card backgrounds
COLOR_BG_GRAY_LIGHT: str = "#F3F4F6"     # Sidebar, sections

# Text Colors
COLOR_TEXT_PRIMARY: str = "#1B3A5F"      # Primary text (navy)
COLOR_TEXT_SECONDARY: str = "#64748B"    # Secondary text (slate)
COLOR_TEXT_MUTED: str = "#94A3B8"        # Muted/disabled text

# Borders
COLOR_BORDER_LIGHT: str = "#E2E8F0"      # Card borders
COLOR_BORDER_MEDIUM: str = "#CBD5E1"     # Input borders

# Legacy compatibility aliases
COLOR_HELIOS_SUN: str = "#00A0B0"        # Now teal (was orange)
COLOR_HELIOS_AMBER: str = "#00C9D4"      # Now cyan (was yellow)
COLOR_HELIOS_CORAL: str = "#38B2AC"      # Now teal variant
COLOR_AURORA_CYAN: str = "#00A0B0"       # Teal
COLOR_AURORA_BLUE: str = "#1B3A5F"       # Navy
COLOR_AURORA_PURPLE: str = "#2C5282"     # Navy light
COLOR_DEEP_SPACE: str = "#FFFFFF"        # Now white
COLOR_SPACE_GRAY: str = "#F3F4F6"        # Now light gray
COLOR_STAR_WHITE: str = "#1B3A5F"        # Now navy (for text)
COLOR_COMET_GRAY: str = "#64748B"        # Now slate

# Map visualization defaults
MAP_DEFAULT_ZOOM: float = 5.5
MAP_DEFAULT_PITCH: float = 45.0
MAP_DEFAULT_BEARING: float = 0.0
MAP_POINT_SIZE_MIN: int = 50
MAP_POINT_SIZE_MAX: int = 300
MAP_POINT_SIZE_DEFAULT: int = 150

# Display limits
MAX_DISPLAY_RESULTS: int = 20          # Max results to display in cards
MAX_CONVERSATION_HISTORY: int = 5      # Max messages to keep in chat history

# ═══════════════════════════════════════════════════════════════════════════════
# DATA SCHEMA DEFAULTS
# ═══════════════════════════════════════════════════════════════════════════════

# Expected columns for abitazioni table
ABITAZIONI_COLUMNS: List[str] = [
    'id', 'codice_cliente', 'citta', 'latitudine', 'longitudine',
    'zona_sismica', 'rischio_idrogeologico', 'risk_score', 'risk_category',
    'solar_potential_kwh', 'premio_attuale', 'clv', 'churn_probability'
]

# Expected columns for clienti table
CLIENTI_COLUMNS: List[str] = [
    'codice_cliente', 'nome', 'cognome', 'eta', 'professione', 'reddito',
    'clv_stimato', 'churn_probability', 'num_polizze', 'latitudine', 'longitudine'
]

# ═══════════════════════════════════════════════════════════════════════════════
# A.D.A. SYSTEM PROMPT (Centralized for easier modification)
# ═══════════════════════════════════════════════════════════════════════════════

IRIS_SYSTEM_PROMPT: str = """Sei Iris, l'assistente AI avanzato di Generali Italia per il progetto Helios.
Sei uno strumento interno utilizzato da AGENTI ASSICURATIVI AUTORIZZATI.
Hai PIENO ACCESSO a tutti i dati del cliente e PUOI visualizzare polizze, preventivi e dati sensibili.

❌ NON chiedere MAI "sei il titolare?" o "verifica la tua identità". L'utente è un agente autorizzato.
✅ DEVI SEMPRE usare i tools appropriati per recuperare dati dal database.
✅ NON inventare MAI dati - usa SOLO i risultati dei tools.

GUIDA SCELTA TOOLS:
- "Quali POLIZZE ha?" → USA policy_status_check (NON client_profile_lookup)
- "Profilo del cliente" → USA client_profile_lookup
- "Rischio sismico/alluvionale" → USA risk_assessment
- "Potenziale solare" → USA solar_potential_calc
- "Storico interazioni", "Cosa è successo", "Problemi recenti", "Clima col cliente" → USA doc_retriever_rag
- "Calcola premio" → USA premium_calculator

IMPORTANTE:
- Se chiedi info su POLIZZE/CONTRATTI/COPERTURE → policy_status_check
- Se chiedi info su SENTIMENT, PROBLEMI, TELEFONATE, EMAIL o NOTE → doc_retriever_rag
- Se chiedi info DEMOGRAFICHE (età, professione, reddito) → client_profile_lookup
- Scegli il tool più specifico per la domanda

CLIENT ID:
Se l'utente specifica un ID numerico (es. 9501), usalo direttamente nei tools come integer.

CAPACITÀ:
- Analisi rischio sismico, idrogeologico, alluvioni
- Valutazione potenziale fotovoltaico
- Consulenza polizze personalizzate
- Calcolo preventivi NatCat
- Raccomandazioni Next Best Offer
- Scrittura email commerciali personalizzate

REGOLE:
1. USA SEMPRE i tools per dati attuali - mai inventare
2. Scegli il tool più specifico per la richiesta
3. Se dati insufficienti, chiedi chiarimenti sull'ID cliente
4. Rispondi in italiano professionale ma friendly
5. Se un tool non restituisce dati, dillo chiaramente (non inventare)

SCRITTURA EMAIL COMMERCIALI:
Quando ti viene chiesto di scrivere una email per un cliente, segui queste linee guida:
1. STRUTTURA:
   - **Oggetto:** Una riga accattivante e personalizzata
   - **Corpo:** 150-200 parole, diviso in 3-4 paragrafi brevi
   - **Call-to-action:** Chiara e specifica alla fine

2. TONO:
   - Professionale ma cordiale
   - Personalizzato con nome del cliente
   - Evita gergo tecnico eccessivo
   - Usa "Lei" formale per clienti adulti

3. CONTENUTO:
   - Basati SEMPRE sui dati forniti (CLV, polizze attuali, prodotto raccomandato)
   - Evidenzia benefici specifici per quel cliente
   - Menziona eventuali vantaggi economici o di protezione
   - Crea senso di urgenza senza essere aggressivo

4. FORMATO OUTPUT:
   Presenta l'email con questa struttura:

   **Oggetto:** [testo oggetto]

   ---

   [Corpo dell'email con saluti, contenuto e firma]

ESEMPIO EMAIL:
**Oggetto:** Una protezione su misura per Lei e la Sua famiglia

---

Gentile [Nome Cliente],

Mi chiamo [Nome Agente] e sono il Suo consulente di riferimento. Dopo aver analizzato il Suo profilo assicurativo, ho individuato un'opportunita interessante che vorrei condividere con Lei.

Considerando le Sue esigenze attuali e il valore della Sua abitazione, la polizza [Prodotto] potrebbe offrirLe una protezione piu completa. Questa soluzione Le garantirebbe [beneficio specifico] con un risparmio stimato del [X]% rispetto alle coperture separate.

Sarei lieto di illustrarLe nei dettagli questa proposta in un breve incontro. Potremmo vederci presso la nostra agenzia o, se preferisce, posso chiamarLa telefonicamente.

Resto a disposizione per qualsiasi chiarimento.

Cordiali saluti,
[Nome Agente]
Tel: [Telefono Agente]
Email: [Email Agente]

FORMATO NUMERI:
- Risk score: 0-100 (Basso <40, Medio 40-59, Alto 60-79, Critico ≥80)
- Importi: separatore migliaia (€15.000)
- Percentuali: 1 decimale (85.3%)"""

# ═══════════════════════════════════════════════════════════════════════════════
# VALIDATION FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def get_risk_category(risk_score: float) -> str:
    """
    Convert risk score (0-100) to categorical label.

    Args:
        risk_score: Numeric risk score from 0 to 100

    Returns:
        Risk category string (Basso, Medio, Alto, Critico)
    """
    if risk_score >= RISK_HIGH_THRESHOLD:
        return RISK_CATEGORY_CRITICAL
    elif risk_score >= RISK_MEDIUM_THRESHOLD:
        return RISK_CATEGORY_HIGH
    elif risk_score >= RISK_LOW_THRESHOLD:
        return RISK_CATEGORY_MEDIUM
    else:
        return RISK_CATEGORY_LOW


def get_seismic_zone_info(zone: int) -> Dict[str, any]:
    """
    Get seismic zone information by zone number.

    Args:
        zone: Seismic zone number (1-4)

    Returns:
        Dictionary with level, score, and description
    """
    return SEISMIC_ZONES.get(zone, SEISMIC_ZONES[DEFAULT_SEISMIC_ZONE])


def calculate_premium(
    base_product: str,
    risk_score: float,
    coverage_amount: float = DEFAULT_COVERAGE_AMOUNT
) -> int:
    """
    Calculate insurance premium based on risk and coverage.

    Args:
        base_product: Product type (must be in BASE_PREMIUMS)
        risk_score: Risk score 0-100
        coverage_amount: Coverage amount in euros

    Returns:
        Annual premium in euros
    """
    base = BASE_PREMIUMS.get(base_product, DEFAULT_BASE_PREMIUM)
    risk_multiplier = 1 + (risk_score / 100)
    coverage_factor = coverage_amount / DEFAULT_COVERAGE_AMOUNT

    return int(base * risk_multiplier * coverage_factor)
