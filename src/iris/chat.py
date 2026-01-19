"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                    IRIS CHAT - Enhanced Python Version                        ║
║                   Streamlit Interface con Engine Locale                       ║
╚═══════════════════════════════════════════════════════════════════════════════╝
"""

import os
import streamlit as st
from typing import Dict
from dotenv import load_dotenv

# Import production Iris engine
print("📦 Importing iris_engine (production version)...")
from src.iris.engine import IrisEngine

load_dotenv()



IRIS_VERSION = "1.0"  # Increment to force reload

def init_iris_engine() -> None:
    """Initialize Iris engine with Supabase connection."""
    # Check if engine exists or version changed
    if "iris_engine" not in st.session_state or st.session_state.get("iris_version") != IRIS_VERSION:
        try:
            print("=" * 80)
            print(f"🔧 INITIALIZING IRIS ENGINE (v{IRIS_VERSION})")
            print("=" * 80)

            # Import here to avoid circular dependency
            from src.data.db_utils import get_supabase_client

            supabase = get_supabase_client()
            if supabase:
                st.session_state.iris_engine = IrisEngine(supabase)
                st.session_state.iris_mode = "python"
                st.session_state.iris_version = IRIS_VERSION
                print(f"✅ Iris Engine v{IRIS_VERSION} initialized successfully")
            else:
                st.session_state.iris_engine = None
                st.session_state.iris_mode = "fallback"
                print("❌ Supabase connection failed, using fallback mode")
        except Exception as e:
            st.error(f"⚠️ Errore inizializzazione Iris: {e}")
            st.session_state.iris_engine = None
            st.session_state.iris_mode = "fallback"


def render_iris_chat() -> None:
    """
    Render the Iris chat interface with Python engine.
    Optimized for sidebar display (compact mode).
    """
    # Apply Vita Sicura Light Theme CSS for sidebar chat
    st.markdown("""
    <style>
        /* Sidebar-optimized chat styling */
        [data-testid="stSidebar"] [data-testid="stChatMessage"] {
            background: rgba(255, 255, 255, 0.9) !important;
            border: 1px solid #E2E8F0 !important;
            border-radius: 12px !important;
            padding: 0.6rem !important;
            margin-bottom: 0.5rem !important;
            box-shadow: 0 1px 2px rgba(27, 58, 95, 0.04) !important;
        }

        /* User message in sidebar */
        [data-testid="stSidebar"] [data-testid="stChatMessage"][data-testid*="user"] {
            background: linear-gradient(135deg, rgba(0, 160, 176, 0.08) 0%, rgba(0, 201, 212, 0.04) 100%) !important;
            border: 1px solid rgba(0, 160, 176, 0.12) !important;
        }

        /* Chat input in sidebar */
        [data-testid="stSidebar"] [data-testid="stChatInput"] {
            border-radius: 12px !important;
        }

        [data-testid="stSidebar"] [data-testid="stChatInput"] > div {
            background: #FFFFFF !important;
            border: 1px solid #E2E8F0 !important;
            border-radius: 12px !important;
            box-shadow: 0 1px 4px rgba(27, 58, 95, 0.06) !important;
        }

        [data-testid="stSidebar"] [data-testid="stChatInput"] input {
            font-family: 'Inter', sans-serif !important;
            font-size: 0.8rem !important;
            color: #1B3A5F !important;
        }

        [data-testid="stSidebar"] [data-testid="stChatInput"] input::placeholder {
            color: #94A3B8 !important;
            font-size: 0.75rem !important;
        }

        /* Chat message text in sidebar */
        [data-testid="stSidebar"] [data-testid="stChatMessage"] p,
        [data-testid="stSidebar"] [data-testid="stChatMessage"] span,
        [data-testid="stSidebar"] [data-testid="stChatMessage"] li {
            color: #1B3A5F !important;
            font-family: 'Inter', sans-serif !important;
            font-size: 0.9rem !important;
            line-height: 1.4 !important;
        }

        [data-testid="stSidebar"] [data-testid="stChatMessage"] strong {
            color: #00A0B0 !important;
        }

        /* Expander in sidebar chat */
        [data-testid="stSidebar"] [data-testid="stChatMessage"] .streamlit-expanderHeader {
            background: rgba(243, 244, 246, 0.8) !important;
            border: 1px solid #E2E8F0 !important;
            border-radius: 6px !important;
            font-size: 0.7rem !important;
            padding: 0.4rem !important;
        }

        /* Code blocks in sidebar chat */
        [data-testid="stSidebar"] [data-testid="stChatMessage"] code {
            background: #F3F4F6 !important;
            color: #1B3A5F !important;
            border: 1px solid #E2E8F0 !important;
            border-radius: 4px !important;
            font-family: 'JetBrains Mono', monospace !important;
            font-size: 0.7rem !important;
        }

        /* Chat avatar sizing for sidebar */
        [data-testid="stSidebar"] [data-testid="stChatMessage"] img,
        [data-testid="stSidebar"] [data-testid="stChatMessage"] [data-testid="stChatMessageAvatar"] {
            width: 24px !important;
            height: 24px !important;
        }
    </style>
    """, unsafe_allow_html=True)

    # Initialize engine
    init_iris_engine()

    # Initialize chat history
    if "iris_messages" not in st.session_state:
        st.session_state.iris_messages = [
            {
                "role": "assistant",
                "content": get_welcome_message_compact()
            }
        ]

    # Check for auto-prompt from map selection (compact for sidebar)
    if st.session_state.get('iris_auto_prompt'):
        auto_prompt = st.session_state.iris_auto_prompt

        st.markdown(f"""
        <div style="background: #FEF3C7; border-radius: 8px; padding: 0.5rem; margin-bottom: 0.5rem; font-size: 0.75rem;">
            <strong>💡 Prompt suggerito</strong>
        </div>
        """, unsafe_allow_html=True)

        if st.button("🚀 Esegui", key="use_auto_prompt", type="primary", use_container_width=True):
            # Add user message with auto-prompt
            st.session_state.iris_messages.append({"role": "user", "content": auto_prompt})

            # Get response
            result = get_iris_response(auto_prompt)
            response = result.get("response", "Errore di elaborazione.")
            tools_used = result.get("tools_used", [])

            # Add to history
            st.session_state.iris_messages.append({
                "role": "assistant",
                "content": response,
                "tools_used": tools_used
            })

            # Clear auto-prompt
            st.session_state.iris_auto_prompt = None
            st.rerun()

        if st.button("✕ Ignora", key="ignore_auto_prompt", use_container_width=True):
            st.session_state.iris_auto_prompt = None
            st.rerun()

    # Chat container
    chat_container = st.container()
    
    with chat_container:
        for msg in st.session_state.iris_messages:
            avatar = "☀️" if msg["role"] == "assistant" else "👤"
            with st.chat_message(msg["role"], avatar=avatar):
                st.markdown(msg["content"])
                
                # Show tools used if present
                if "tools_used" in msg and msg["tools_used"]:
                    with st.expander("🔧 Tools utilizzati"):
                        for tool in msg["tools_used"]:
                            st.code(tool, language="text")
    
    # Input
    if prompt := st.chat_input("Scrivi qui..."):
        # Add user message
        st.session_state.iris_messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)
        
        # Get response
        with st.chat_message("assistant", avatar="☀️"):
            with st.spinner("Iris sta elaborando..."):
                result = get_iris_response(prompt)
                
                response = result.get("response", "Errore di elaborazione.")
                tools_used = result.get("tools_used", [])
                
                st.markdown(response)
                
                # Show tools if used
                if tools_used:
                    with st.expander("🔧 Tools utilizzati"):
                        for tool in tools_used:
                            st.code(tool, language="text")
                
                # Add to history
                st.session_state.iris_messages.append({
                    "role": "assistant",
                    "content": response,
                    "tools_used": tools_used
                })


def get_iris_response(prompt: str) -> Dict:
    """
    Get response from Iris - tries Python engine, falls back to local.
    """
    client_id = st.session_state.get("selected_client_id")
    history = st.session_state.iris_messages
    
    # Try Python engine
    if st.session_state.get("iris_engine"):
        try:
            result = st.session_state.iris_engine.chat(
                message=prompt,
                client_id=client_id,
                history=history
            )
            
            if result.get("success"):
                return result
        except Exception as e:
            st.error(f"Iris Engine error: {e}")
    
    # Fallback to local response
    return {
        "response": get_local_response(prompt),
        "tools_used": [],
        "success": True
    }


def get_welcome_message() -> str:
    """Generate welcome message for Iris chatbot."""
    return """Ciao! Sono **Iris**, il tuo Intelligent Advisor. 🌞

Posso aiutarti a:
- 📊 **Analizzare il rischio** di specifici clienti o aree geografiche
- 💰 **Calcolare preventivi** personalizzati per polizze NatCat
- ☀️ **Stimare il potenziale solare** di un'abitazione
- 🔍 **Rispondere a domande** sulle condizioni di polizza
- 📋 **Consultare lo storico** interazioni clienti

Come posso assisterti oggi?"""


def get_welcome_message_compact() -> str:
    """Generate compact welcome message for sidebar chat."""
    return """Ciao! Sono **Iris**. 🌞

Posso aiutarti con:
• Analisi rischio clienti
• Preventivi polizze
• Dati potenziale solare
• Info prodotti

Come posso aiutarti?"""


def get_local_response(prompt: str) -> str:
    """
    Generate local fallback response when Iris engine is not available.

    Args:
        prompt: User's message

    Returns:
        Contextual help message based on keywords in prompt
    """
    prompt_lower = prompt.lower()
    
    # Rischio
    if any(word in prompt_lower for word in ["rischio", "risk", "pericolo", "sicurezza"]):
        return """📊 **Analisi Rischio Portfolio**

Per un'analisi rischio accurata, ho bisogno del **codice cliente**.

Puoi chiedermi:
- "Analizza il rischio del cliente 100"
- "Qual è il risk score dell'abitazione del cliente 250"
- "Mostrami i dati di rischio sismico per il cliente X"

⚠️ **Nota:** Attualmente sto funzionando in modalità ridotta. Per analisi complete, assicurati che la connessione al database sia attiva."""
    
    # Solare
    elif any(word in prompt_lower for word in ["solare", "solar", "fotovoltaico", "pannelli", "rinnovabile"]):
        return """☀️ **Analisi Potenziale Solare**

Per calcolare il potenziale solare, specifica il **codice cliente**.

Esempi:
- "Calcola il potenziale solare per il cliente 100"
- "Quanto risparmierebbe il cliente X con i pannelli solari?"
- "È conveniente un impianto fotovoltaico per il cliente Y?"

💡 **Info Generale:**
- Produzione media Italia: 1.200-1.800 kWh/kWp/anno
- ROI tipico: 6-8 anni
- Risparmio annuo stimato: €500-1.000 per impianto 3kW"""
    
    # Polizze
    elif any(word in prompt_lower for word in ["polizz", "policy", "copertura", "assicuraz"]):
        return """📋 **Consulenza Polizze**

Per consultare le polizze attive, indica il **codice cliente**.

Posso aiutarti con:
- Stato polizze attive e scadenze
- Coperture in essere
- Prodotti disponibili per cross-selling
- Calcolo preventivi personalizzati

Esempio: "Quali polizze ha il cliente 100?"
"""
    
    # Preventivo
    elif any(word in prompt_lower for word in ["preventivo", "prezzo", "costo", "quanto costa", "quotazione"]):
        return """💰 **Calcolo Preventivo**

Per un preventivo accurato, forniscimi:
1. **Codice cliente** (per calcolare il risk score)
2. **Tipo di prodotto** (NatCat, CasaSerena, GreenHome, etc.)
3. **Massimale** desiderato (opzionale, default €100.000)

Esempio:
"Calcola un preventivo NatCat per il cliente 100 con massimale 150.000€"

📊 **Prodotti Disponibili:**
- NatCat (Terremoto + Alluvione)
- CasaSerena (Casa + Contenuto)
- GreenHome (Impianti Tecnologici)
- FuturoSicuro (Vita + Investimento)
- SaluteProtetta (Sanitaria)"""
    
    # Ricerca cliente
    elif any(word in prompt_lower for word in ["cliente", "cerca", "trova", "profilo"]):
        return """🔍 **Ricerca Cliente**

Per cercare un cliente, usa:
- **ID Cliente**: "Mostra il profilo del cliente 100"
- **Città**: Usa la tab 🔍 Dettaglio Clienti per ricerca avanzata

Posso fornirti:
- Dati anagrafici e professionali
- CLV e probabilità churn
- Risk score abitazione
- Polizze attive
- Storico interazioni

Dimmi il codice cliente e ti mostro tutto!"""
    
    # Storico/RAG
    elif any(word in prompt_lower for word in ["storico", "passato", "interazioni", "reclam", "sinistr", "storia"]):
        return """📜 **Consultazione Storico**

Per consultare lo storico di un cliente, indica il **codice cliente**.

Posso cercare:
- Interazioni passate (call center, email)
- Reclami e sinistri
- Note agente
- Modifiche polizze

Esempio: "Ci sono stati problemi per il cliente 100?"

🔍 Uso ricerca semantica per trovare le informazioni più rilevanti."""
    
    # Capabilities
    elif any(word in prompt_lower for word in ["puoi", "aiut", "funzion", "cosa fai", "capacità"]):
        return """🎯 **Le Mie Capacità**

Sono Iris, specializzato in:

**Analisi & Valutazioni:**
- 📊 Risk assessment (sismico, idro, alluvioni)
- ☀️ Potenziale solare (PVGIS + stima ROI)
- 💰 Calcolo preventivi personalizzati

**Dati Cliente:**
- 👤 Profilo completo (anagrafica + CLV + churn)
- 📋 Polizze attive e scadenze
- 📜 Storico interazioni (RAG semantico)

**Consulenza:**
- 🎯 Next Best Offer recommendations
- ⚠️ Alert rischio alto
- 💡 Suggerimenti cross-selling

**Come Usarmi:**
Forniscimi un codice cliente e dimmi cosa ti serve!
Esempio: "Analizza il cliente 100 e suggerisci polizze"
"""
    
    # Default
    else:
        return """Grazie per la tua domanda! 

Sono Iris, il tuo Intelligent Advisor. Per aiutarti al meglio, ho bisogno di più dettagli.

📝 **Prova a chiedermi:**
- "Analizza il rischio del cliente [ID]"
- "Calcola il potenziale solare per il cliente [ID]"
- "Quali polizze ha il cliente [ID]?"
- "Preventivo NatCat per cliente [ID]"
- "Storico interazioni del cliente [ID]"

Oppure dimmi semplicemente cosa ti serve e cercherò di aiutarti! 😊"""


# For standalone testing
if __name__ == "__main__":
    st.set_page_config(page_title="Iris Chat", page_icon="☀️", layout="wide")
    st.title("☀️ Iris - Intelligent Advisor")
    render_iris_chat()
