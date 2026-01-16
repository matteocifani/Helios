"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                    A.D.A. - AUGMENTED DIGITAL ADVISOR                         ║
║                   n8n Webhook Integration Module                              ║
╚═══════════════════════════════════════════════════════════════════════════════╝
"""

import os
import requests
import streamlit as st
from typing import Optional, List, Dict
from dotenv import load_dotenv

load_dotenv()


class ADAClient:
    """
    Client for interacting with A.D.A. AI agent via n8n webhook.
    """
    
    def __init__(self):
        self.webhook_url = os.getenv("N8N_WEBHOOK_URL", "")
        self.timeout = 120  # 2 minutes timeout for AI processing
    
    def is_configured(self) -> bool:
        """Check if webhook URL is configured."""
        return bool(self.webhook_url)
    
    def send_message(
        self, 
        message: str, 
        client_id: Optional[str] = None,
        history: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Send a message to A.D.A. and get a response.
        
        Args:
            message: User's message
            client_id: Optional client ID for context
            history: Optional chat history for context
            
        Returns:
            dict with 'success', 'response', and optionally 'data'
        """
        if not self.is_configured():
            return {
                "success": False,
                "response": "⚠️ A.D.A. non è configurato. Verifica la configurazione del webhook n8n.",
                "data": None
            }
        
        try:
            payload = {
                "message": message,
                "client_id": client_id,
                "history": history[-5:] if history else [],  # Last 5 messages
                "timestamp": st.session_state.get("session_start", ""),
                "session_id": st.session_state.get("session_id", "")
            }
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=self.timeout,
                headers={
                    "Content-Type": "application/json",
                    "X-Source": "Helios-FluidView"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "response": data.get("output", data.get("response", "Nessuna risposta ricevuta.")),
                    "data": data.get("data", None),
                    "tools_used": data.get("tools_used", [])
                }
            else:
                return {
                    "success": False,
                    "response": f"⚠️ Errore di comunicazione (HTTP {response.status_code}). Riprova tra qualche secondo.",
                    "data": None
                }
                
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "response": "⏱️ La richiesta ha impiegato troppo tempo. A.D.A. potrebbe essere occupato con analisi complesse. Riprova.",
                "data": None
            }
        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "response": "🔌 Impossibile connettersi ad A.D.A. Verifica che n8n sia attivo e raggiungibile.",
                "data": None
            }
        except Exception as e:
            return {
                "success": False,
                "response": f"❌ Errore imprevisto: {str(e)}",
                "data": None
            }
    
    def get_client_analysis(self, client_id: str) -> Dict:
        """
        Request a complete client analysis from A.D.A.
        """
        message = f"Esegui un'analisi completa del cliente {client_id}, includendo rischio, potenziale e raccomandazioni."
        return self.send_message(message, client_id=client_id)
    
    def calculate_quote(self, client_id: str, product_type: str = "NatCat") -> Dict:
        """
        Request a quote calculation for a specific client.
        """
        message = f"Calcola un preventivo {product_type} per il cliente {client_id}."
        return self.send_message(message, client_id=client_id)
    
    def get_solar_estimate(self, lat: float, lon: float) -> Dict:
        """
        Request solar potential estimate for coordinates.
        """
        message = f"Stima il potenziale solare per le coordinate {lat}, {lon}."
        return self.send_message(message)


# Singleton instance
ada_client = ADAClient()


def render_ada_chat():
    """
    Render the A.D.A. chat interface component.
    """
    # Initialize chat history
    if "ada_messages" not in st.session_state:
        st.session_state.ada_messages = [
            {
                "role": "assistant",
                "content": get_welcome_message()
            }
        ]
    
    # Chat container
    chat_container = st.container()
    
    with chat_container:
        for msg in st.session_state.ada_messages:
            avatar = "☀️" if msg["role"] == "assistant" else "👤"
            with st.chat_message(msg["role"], avatar=avatar):
                st.markdown(msg["content"])
    
    # Input
    if prompt := st.chat_input("Chiedi ad A.D.A..."):
        # Add user message
        st.session_state.ada_messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)
        
        # Get response
        with st.chat_message("assistant", avatar="☀️"):
            with st.spinner("A.D.A. sta elaborando..."):
                if ada_client.is_configured():
                    result = ada_client.send_message(
                        prompt,
                        client_id=st.session_state.get("selected_client_id"),
                        history=st.session_state.ada_messages
                    )
                    response = result["response"]
                else:
                    # Fallback to local responses
                    response = get_local_response(prompt)
                
                st.markdown(response)
                st.session_state.ada_messages.append({"role": "assistant", "content": response})


def get_welcome_message() -> str:
    """Generate welcome message for A.D.A."""
    return """Ciao! Sono **A.D.A.**, il tuo Augmented Digital Advisor. 🌞

Posso aiutarti a:
- 📊 **Analizzare il rischio** di specifici clienti o aree geografiche
- 💰 **Calcolare preventivi** personalizzati per polizze NatCat
- ☀️ **Stimare il potenziale solare** di un'abitazione
- 🔍 **Rispondere a domande** sulle condizioni di polizza

Come posso assisterti oggi?"""


def get_local_response(prompt: str) -> str:
    """
    Generate a local response when webhook is not available.
    This is a fallback for demo purposes.
    """
    prompt_lower = prompt.lower()
    
    if any(word in prompt_lower for word in ["rischio", "risk", "pericolo"]):
        return """📊 **Analisi Rischio Portfolio**

Ho analizzato il database SkyGuard. Ecco le statistiche principali:

- 🔴 **Critico** (≥80): ~8% del portafoglio
- 🟠 **Alto** (60-79): ~22% del portafoglio  
- 🟡 **Medio** (40-59): ~35% del portafoglio
- 🟢 **Basso** (<40): ~35% del portafoglio

⚠️ Le aree più critiche sono concentrate in:
- Zone sismiche 1-2 (Centro Italia, Sicilia orientale)
- Aree a rischio alluvione P2/P3 (Liguria, Emilia-Romagna)

Vuoi approfondire una specifica area geografica?"""
    
    elif any(word in prompt_lower for word in ["solare", "solar", "fotovoltaico", "pannelli"]):
        return """☀️ **Analisi Potenziale Solare**

Basandomi sui dati PVGIS integrati:

- **Produzione media stimata**: 3,200-4,200 kWh/anno per impianto 3kW
- **ROI medio**: 6-8 anni
- **Risparmio annuo**: €650-950

🎯 **Opportunità identificate:**
- ~70% del portafoglio ha potenziale solare positivo
- I clienti in Sicilia e Sardegna hanno i rendimenti più alti
- Cross-selling consigliato: Polizza impianto + RC pannelli

Vuoi che identifichi i top prospect per una campagna solar?"""
    
    elif any(word in prompt_lower for word in ["preventivo", "quota", "prezzo", "costo"]):
        return """💰 **Calcolo Preventivo**

Per calcolare un preventivo accurato, ho bisogno di:

1. **Codice Cliente** o coordinate dell'immobile
2. **Tipo di copertura** desiderata:
   - 🏠 Base (Incendio + Furto)
   - 🌊 NatCat (Terremoto + Alluvione)
   - ☀️ Green (Impianti tecnologici)
   - 💎 Premium (All-risk)

Indicami questi dati e calcolerò un preventivo personalizzato basato sul risk score dell'immobile."""
    
    elif any(word in prompt_lower for word in ["cliente", "cerca", "trova"]):
        return """🔍 **Ricerca Cliente**

Puoi cercare un cliente in diversi modi:
- **Per ID**: "HAB00001" o "CLI1234"
- **Per città**: "Milano", "Roma", etc.
- **Per rischio**: "clienti ad alto rischio a Napoli"

Usa la tab **🔍 Dettaglio Clienti** per una ricerca avanzata, oppure dimmi cosa stai cercando e ti aiuto io!"""
    
    else:
        return """Grazie per la tua domanda! 

Sono A.D.A., specializzato in:

🎯 **Le mie competenze:**
- Analisi rischio sismico e idrogeologico
- Calcolo potenziale fotovoltaico (PVGIS)
- Preventivi personalizzati
- Insights sul portafoglio clienti

📝 **Prova a chiedermi:**
- "Qual è la situazione rischio nel Centro Italia?"
- "Stima il potenziale solare per Firenze"
- "Identifica i clienti alto valore in zone critiche"
- "Calcola un preventivo NatCat"

Come posso aiutarti?"""
