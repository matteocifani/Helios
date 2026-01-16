"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                    A.D.A. - AUGMENTED DIGITAL ADVISOR                         ║
║                        Python Core Engine                                     ║
╚═══════════════════════════════════════════════════════════════════════════════╝

Implementazione Python completa di A.D.A. con:
- Integrazione OpenRouter (Claude 3.5 Sonnet)
- 6 Tools: Client Profile, Policies, Risk, Solar, RAG, Premium
- Gestione conversazione multi-turn
"""

import os
import json
import requests
from typing import Optional, Dict, List, Any
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


class ADAEngine:
    """
    Core engine per A.D.A. - Gestisce AI, tools e conversazione.
    """
    
    def __init__(self, supabase_client):
        self.supabase = supabase_client
        self.openrouter_key = os.getenv("OPENROUTER_API_KEY")
        self.model = "anthropic/claude-3.5-sonnet"
        
        # Tool registry
        self.tools = {
            "client_profile_lookup": self.tool_client_profile,
            "policy_status_check": self.tool_policy_status,
            "risk_assessment": self.tool_risk_assessment,
            "solar_potential_calc": self.tool_solar_potential,
            "doc_retriever_rag": self.tool_rag_retriever,
            "premium_calculator": self.tool_premium_calculator
        }
        
        # Tool definitions for Claude
        self.tool_definitions = [
            {
                "name": "client_profile_lookup",
                "description": "Get complete profile for a specific client including demographics, risk score, CLV, and property details. Use when user asks about a specific client.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "client_id": {
                            "type": "integer",
                            "description": "Client ID (codice_cliente)"
                        }
                    },
                    "required": ["client_id"]
                }
            },
            {
                "name": "policy_status_check",
                "description": "Get all active insurance policies for a client. Use when user asks about current policies or coverage.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "client_id": {
                            "type": "integer",
                            "description": "Client ID"
                        }
                    },
                    "required": ["client_id"]
                }
            },
            {
                "name": "risk_assessment",
                "description": "Analyze comprehensive risk profile including seismic, hydrogeological, and flood risk. Returns risk score 0-100 and category.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "client_id": {
                            "type": "integer",
                            "description": "Client ID to assess property risk"
                        }
                    },
                    "required": ["client_id"]
                }
            },
            {
                "name": "solar_potential_calc",
                "description": "Calculate solar energy production potential. Returns annual kWh, ROI estimate, and savings.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "client_id": {
                            "type": "integer",
                            "description": "Client ID for property location"
                        }
                    },
                    "required": ["client_id"]
                }
            },
            {
                "name": "doc_retriever_rag",
                "description": "Search historical client interactions using semantic search. Returns relevant past conversations, claims, or notes.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "client_id": {
                            "type": "integer",
                            "description": "Client ID"
                        },
                        "query": {
                            "type": "string",
                            "description": "Search query for semantic search"
                        }
                    },
                    "required": ["client_id", "query"]
                }
            },
            {
                "name": "premium_calculator",
                "description": "Calculate insurance premium quote based on risk score, product type, and coverage amount.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "risk_score": {
                            "type": "number",
                            "description": "Risk score 0-100"
                        },
                        "product_type": {
                            "type": "string",
                            "description": "Product: NatCat, CasaSerena, FuturoSicuro, etc.",
                            "enum": ["NatCat", "CasaSerena", "FuturoSicuro", "InvestimentoFlessibile", "SaluteProtetta", "GreenHome", "Multiramo"]
                        },
                        "coverage_amount": {
                            "type": "number",
                            "description": "Coverage amount in euros (default 100000)"
                        }
                    },
                    "required": ["risk_score", "product_type"]
                }
            }
        ]
    
    def chat(self, message: str, client_id: Optional[int] = None, history: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        Main chat interface - gestisce conversazione con A.D.A.
        
        Args:
            message: User message
            client_id: Optional client ID for context
            history: Conversation history
            
        Returns:
            Dict with response, tools_used, etc.
        """
        try:
            # Build context
            context = self._build_context(client_id)
            
            # Build messages
            messages = self._build_messages(message, context, history)
            
            # Call Claude with tools
            response = self._call_claude(messages)
            
            # Process tool calls if any
            if response.get("stop_reason") == "tool_use":
                response = self._process_tool_calls(response, messages)
            
            # Extract final response
            final_text = self._extract_text(response)
            tools_used = self._extract_tools_used(response)
            
            return {
                "success": True,
                "response": final_text,
                "tools_used": tools_used,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "response": f"⚠️ Errore: {str(e)}",
                "tools_used": [],
                "error": str(e)
            }
    
    def _build_context(self, client_id: Optional[int]) -> str:
        """Build context string with client info if available."""
        if not client_id:
            return ""
        
        try:
            # Query client data
            response = self.supabase.table("clienti").select(
                "codice_cliente, nome, cognome, eta, professione, reddito, "
                "clv_stimato, churn_probability, num_polizze"
            ).eq("codice_cliente", client_id).single().execute()
            
            if not response.data:
                return ""
            
            client = response.data
            
            # Query abitazione
            abit_response = self.supabase.table("abitazioni").select(
                "risk_score, risk_category, zona_sismica, solar_potential_kwh, citta"
            ).eq("codice_cliente", client_id).execute()
            
            abit = abit_response.data[0] if abit_response.data else {}
            
            # Build context string
            context = f"""
CONTESTO CLIENTE:
- Nome: {client.get('nome')} {client.get('cognome')}
- Età: {client.get('eta')}
- Professione: {client.get('professione')}
- CLV: €{client.get('clv_stimato', 0):,.0f}
- Rischio Churn: {client.get('churn_probability', 0) * 100:.1f}%
- Polizze Attive: {client.get('num_polizze', 0)}
- Risk Score: {abit.get('risk_score', 'N/D')}/100 ({abit.get('risk_category', 'Non valutato')})
- Zona Sismica: {abit.get('zona_sismica', 'N/D')}
- Potenziale Solare: {abit.get('solar_potential_kwh', 'Non calcolato')} kWh/anno
- Località: {abit.get('citta', 'N/D')}
"""
            return context
            
        except Exception as e:
            print(f"Error building context: {e}")
            return ""
    
    def _build_messages(self, message: str, context: str, history: Optional[List[Dict]]) -> List[Dict]:
        """Build message array for Claude API."""
        messages = []
        
        # Add history if present
        if history:
            for msg in history[-5:]:  # Last 5 messages only
                messages.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", "")
                })
        
        # Add current message with context
        current_content = message
        if context:
            current_content = f"{context}\n\nRichiesta: {message}"
        
        messages.append({
            "role": "user",
            "content": current_content
        })
        
        return messages
    
    def _call_claude(self, messages: List[Dict]) -> Dict:
        """Call OpenRouter/Claude API."""
        url = "https://openrouter.ai/api/v1/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {self.openrouter_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://helios-project.local",
            "X-Title": "Helios A.D.A."
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": self._get_system_prompt()
                }
            ] + messages,
            "tools": self.tool_definitions,
            "temperature": 0.3,
            "max_tokens": 2000
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        
        return response.json()
    
    def _process_tool_calls(self, response: Dict, messages: List[Dict]) -> Dict:
        """Process tool calls and get final response."""
        tool_results = []
        
        # Extract tool calls from response
        choice = response.get("choices", [{}])[0]
        message = choice.get("message", {})
        tool_calls = message.get("tool_calls", [])
        
        # Execute each tool
        for tool_call in tool_calls:
            tool_name = tool_call.get("function", {}).get("name")
            tool_args = json.loads(tool_call.get("function", {}).get("arguments", "{}"))
            
            if tool_name in self.tools:
                result = self.tools[tool_name](**tool_args)
                tool_results.append({
                    "role": "tool",
                    "tool_call_id": tool_call.get("id"),
                    "content": json.dumps(result)
                })
        
        # Call Claude again with tool results
        messages.append(message)
        messages.extend(tool_results)
        
        return self._call_claude(messages)
    
    def _extract_text(self, response: Dict) -> str:
        """Extract text response from Claude."""
        choice = response.get("choices", [{}])[0]
        message = choice.get("message", {})
        return message.get("content", "Nessuna risposta generata.")
    
    def _extract_tools_used(self, response: Dict) -> List[str]:
        """Extract list of tools used."""
        # This would need more sophisticated parsing of the full conversation
        # For now, return empty list
        return []
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for A.D.A."""
        return """Sei A.D.A. (Augmented Digital Advisor), assistente AI di Helios specializzato in analisi assicurativa.

CAPACITÀ:
- Analisi rischio sismico, idrogeologico, alluvioni
- Valutazione potenziale fotovoltaico
- Consulenza polizze personalizzate
- Calcolo preventivi NatCat
- Raccomandazioni Next Best Offer

REGOLE:
1. USA SEMPRE i tools per dati attuali - mai inventare numeri
2. Se chiedi info cliente, usa client_profile_lookup
3. Per rischio, usa risk_assessment
4. Per polizze attive, usa policy_status_check
5. Rispondi in italiano professionale ma friendly
6. Max 3-4 paragrafi per risposta
7. Usa emoji strategici (🏠 🌊 ☀️ 📊)
8. Se dati insufficienti, chiedi chiarimenti

FORMATO NUMERI:
- Risk score: 0-100 (Basso <40, Medio 40-59, Alto 60-79, Critico ≥80)
- Importi: separatore migliaia (€15.000)
- Percentuali: 1 decimale (85.3%)"""
    
    # ========================================================================
    # TOOLS IMPLEMENTATION
    # ========================================================================
    
    def tool_client_profile(self, client_id: int) -> Dict:
        """Tool: Get client profile."""
        try:
            response = self.supabase.rpc(
                "get_client_profile",
                {"p_client_id": client_id}
            ).execute()
            
            if response.data:
                return {"profile": response.data}
            
            # Fallback: manual query
            client = self.supabase.table("clienti").select("*").eq("codice_cliente", client_id).single().execute()
            abit = self.supabase.table("abitazioni").select("*").eq("codice_cliente", client_id).execute()
            
            return {
                "profile": {
                    "cliente": client.data,
                    "abitazione": abit.data[0] if abit.data else None
                }
            }
            
        except Exception as e:
            return {"error": f"Cliente non trovato: {str(e)}"}
    
    def tool_policy_status(self, client_id: int) -> Dict:
        """Tool: Get active policies."""
        try:
            response = self.supabase.table("polizze").select(
                "prodotto, area_bisogno, stato_polizza, data_emissione, "
                "data_scadenza, premio_totale_annuo, massimale"
            ).eq("codice_cliente", client_id).eq("stato_polizza", "Attiva").execute()
            
            return {
                "policies": response.data,
                "count": len(response.data)
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def tool_risk_assessment(self, client_id: int) -> Dict:
        """Tool: Assess property risk."""
        try:
            response = self.supabase.table("abitazioni").select(
                "risk_score, risk_category, zona_sismica, "
                "hydro_risk_p3, hydro_risk_p2, flood_risk_p4, flood_risk_p3, citta"
            ).eq("codice_cliente", client_id).single().execute()
            
            data = response.data
            
            # Calculate breakdown
            seismic_map = {
                "1": {"level": "Molto Alto", "score": 90},
                "2": {"level": "Alto", "score": 70},
                "3": {"level": "Medio", "score": 40},
                "4": {"level": "Basso", "score": 15}
            }
            
            seismic = seismic_map.get(str(data.get("zona_sismica", "")), {"level": "Non valutato", "score": 0})
            
            hydro_score = 80 if data.get("hydro_risk_p3", 0) > 5 else 50 if data.get("hydro_risk_p2", 0) > 5 else 20
            flood_score = 90 if data.get("flood_risk_p4", 0) > 10 else 60 if data.get("flood_risk_p3", 0) > 10 else 25
            
            return {
                "risk_score": data.get("risk_score", 0),
                "risk_category": data.get("risk_category", "Non valutato"),
                "breakdown": {
                    "sismico": seismic,
                    "idrogeologico": {"score": hydro_score, "p3": data.get("hydro_risk_p3")},
                    "alluvionale": {"score": flood_score, "p4": data.get("flood_risk_p4")}
                },
                "location": data.get("citta")
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def tool_solar_potential(self, client_id: int) -> Dict:
        """Tool: Calculate solar potential."""
        try:
            response = self.supabase.table("abitazioni").select(
                "solar_potential_kwh, solar_savings_euro, solar_coverage_percent, "
                "latitudine, longitudine, citta"
            ).eq("codice_cliente", client_id).single().execute()
            
            data = response.data
            
            # If already calculated, return cached
            if data.get("solar_potential_kwh"):
                return {
                    "kwh_annual": data["solar_potential_kwh"],
                    "savings_euro": data.get("solar_savings_euro", 0),
                    "coverage_percent": data.get("solar_coverage_percent", 0),
                    "location": data.get("citta"),
                    "source": "cached"
                }
            
            # Otherwise estimate
            lat = data.get("latitudine", 42)
            kwh_per_kwp = 1400 if lat > 42 else 1500 if lat > 40 else 1600
            system_size = 3
            kwh_annual = int(system_size * kwh_per_kwp * 0.85)
            
            savings = int(kwh_annual * 0.25 - 100)
            coverage = min(100, int((kwh_annual / 3500) * 100))
            
            return {
                "kwh_annual": kwh_annual,
                "savings_euro": savings,
                "coverage_percent": coverage,
                "roi_years": round(6000 / savings, 1) if savings > 0 else 99,
                "location": data.get("citta"),
                "source": "estimated"
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def tool_rag_retriever(self, client_id: int, query: str) -> Dict:
        """Tool: RAG document retrieval."""
        try:
            # Generate query embedding
            emb_response = requests.post(
                "https://openrouter.ai/api/v1/embeddings",
                headers={
                    "Authorization": f"Bearer {self.openrouter_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "openai/text-embedding-3-small",
                    "input": query
                },
                timeout=30
            )
            
            embedding = emb_response.json()["data"][0]["embedding"]
            
            # Vector search (requires pgvector extension)
            # Note: This is simplified - actual implementation depends on Supabase setup
            response = self.supabase.table("interactions").select(
                "text_embedded, data_interazione, tipo_interazione, esito"
            ).eq("codice_cliente", client_id).limit(5).execute()
            
            return {
                "documents": response.data,
                "count": len(response.data)
            }
            
        except Exception as e:
            return {"error": str(e), "documents": []}
    
    def tool_premium_calculator(self, risk_score: float, product_type: str, coverage_amount: float = 100000) -> Dict:
        """Tool: Calculate premium."""
        base_premiums = {
            "NatCat": 650,
            "CasaSerena": 380,
            "FuturoSicuro": 1200,
            "InvestimentoFlessibile": 800,
            "SaluteProtetta": 950,
            "GreenHome": 520,
            "Multiramo": 850
        }
        
        base = base_premiums.get(product_type, 500)
        risk_multiplier = 1 + (risk_score / 100)
        coverage_factor = coverage_amount / 100000
        
        premium_annual = int(base * risk_multiplier * coverage_factor)
        premium_monthly = int(premium_annual / 12)
        
        return {
            "product": product_type,
            "premium_annual": premium_annual,
            "premium_monthly": premium_monthly,
            "risk_score": risk_score,
            "coverage": coverage_amount,
            "breakdown": {
                "base": base,
                "risk_multiplier": round(risk_multiplier, 2),
                "coverage_factor": round(coverage_factor, 2)
            }
        }
