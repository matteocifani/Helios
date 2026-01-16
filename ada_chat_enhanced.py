"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                    A.D.A. CHAT - Enhanced Python Version                      ║
║                   Streamlit Interface con Engine Locale                       ║
╚═══════════════════════════════════════════════════════════════════════════════╝
"""

import os
import streamlit as st
from typing import Dict
from dotenv import load_dotenv

# Import production ADA engine
print("📦 Importing ada_engine (production version)...")
from ada_engine import ADAEngine

load_dotenv()


def init_ada_engine() -> None:
    """Initialize A.D.A. engine with Supabase connection."""
    if "ada_engine" not in st.session_state:
        try:
            print("=" * 80)
            print("🔧 INITIALIZING A.D.A. ENGINE")
            print("=" * 80)

            # Import here to avoid circular dependency
            from db_utils import get_supabase_client

            supabase = get_supabase_client()
            if supabase:
                st.session_state.ada_engine = ADAEngine(supabase)
                st.session_state.ada_mode = "python"  # Using Python engine
                print("✅ A.D.A. Engine initialized successfully")
            else:
                st.session_state.ada_engine = None
                st.session_state.ada_mode = "fallback"
                print("❌ Supabase connection failed, using fallback mode")
        except Exception as e:
            st.error(f"⚠️ Errore inizializzazione A.D.A.: {e}")
            st.session_state.ada_engine = None
            st.session_state.ada_mode = "fallback"


def render_ada_chat() -> None:
    """
    Render the A.D.A. chat interface with Python engine.
    """
    # Initialize engine
    init_ada_engine()
    
    # Initialize chat history
    if "ada_messages" not in st.session_state:
        st.session_state.ada_messages = [
            {
                "role": "assistant",
                "content": get_welcome_message()
            }
        ]
    
    # Display mode indicator
    mode_emoji = "🐍" if st.session_state.get("ada_mode") == "python" else "⚙️" if st.session_state.get("ada_mode") == "n8n" else "💤"
    mode_text = "Python Engine" if st.session_state.get("ada_mode") == "python" else "n8n Webhook" if st.session_state.get("ada_mode") == "n8n" else "Fallback Mode"
    
    st.caption(f"{mode_emoji} **A.D.A. Status:** {mode_text}")
    
    # Chat container
    chat_container = st.container()
    
    with chat_container:
        for msg in st.session_state.ada_messages:
            avatar = "☀️" if msg["role"] == "assistant" else "👤"
            with st.chat_message(msg["role"], avatar=avatar):
                st.markdown(msg["content"])
                
                # Show tools used if present
                if "tools_used" in msg and msg["tools_used"]:
                    with st.expander("🔧 Tools utilizzati"):
                        for tool in msg["tools_used"]:
                            st.code(tool, language="text")
    
    # Input
    if prompt := st.chat_input("Chiedi ad A.D.A..."):
        # Add user message
        st.session_state.ada_messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)
        
        # Get response
        with st.chat_message("assistant", avatar="☀️"):
            with st.spinner("A.D.A. sta elaborando..."):
                result = get_ada_response(prompt)
                
                response = result.get("response", "Errore di elaborazione.")
                tools_used = result.get("tools_used", [])
                
                st.markdown(response)
                
                # Show tools if used
                if tools_used:
                    with st.expander("🔧 Tools utilizzati"):
                        for tool in tools_used:
                            st.code(tool, language="text")
                
                # Add to history
                st.session_state.ada_messages.append({
                    "role": "assistant",
                    "content": response,
                    "tools_used": tools_used
                })


def get_ada_response(prompt: str) -> Dict:
    """
    Get response from A.D.A. - tries Python engine, falls back to local.
    """
    client_id = st.session_state.get("selected_client_id")
    history = st.session_state.ada_messages
    
    # Try Python engine
    if st.session_state.get("ada_engine"):
        try:
            result = st.session_state.ada_engine.chat(
                message=prompt,
                client_id=client_id,
                history=history
            )
            
            if result.get("success"):
                return result
        except Exception as e:
            st.error(f"A.D.A. Engine error: {e}")
    
    # Fallback to local response
    return {
        "response": get_local_response(prompt),
        "tools_used": [],
        "success": True
    }


def get_welcome_message() -> str:
    """Generate welcome message for A.D.A. chatbot."""
    return """Ciao! Sono **A.D.A.**, il tuo Augmented Digital Advisor. 🌞

Posso aiutarti a:
- 📊 **Analizzare il rischio** di specifici clienti o aree geografiche
- 💰 **Calcolare preventivi** personalizzati per polizze NatCat
- ☀️ **Stimare il potenziale solare** di un'abitazione
- 🔍 **Rispondere a domande** sulle condizioni di polizza
- 📋 **Consultare lo storico** interazioni clienti

Come posso assisterti oggi?"""


def get_local_response(prompt: str) -> str:
    """
    Generate local fallback response when A.D.A. engine is not available.

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

Sono A.D.A., specializzato in:

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

Sono A.D.A., il tuo Augmented Digital Advisor. Per aiutarti al meglio, ho bisogno di più dettagli.

📝 **Prova a chiedermi:**
- "Analizza il rischio del cliente [ID]"
- "Calcola il potenziale solare per il cliente [ID]"
- "Quali polizze ha il cliente [ID]?"
- "Preventivo NatCat per cliente [ID]"
- "Storico interazioni del cliente [ID]"

Oppure dimmi semplicemente cosa ti serve e cercherò di aiutarti! 😊"""


# For standalone testing
if __name__ == "__main__":
    st.set_page_config(page_title="A.D.A. Chat", page_icon="☀️", layout="wide")
    st.title("☀️ A.D.A. - Augmented Digital Advisor")
    render_ada_chat()
