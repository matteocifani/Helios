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

# Import constants
from constants import (
    BASE_PREMIUMS,
    DEFAULT_BASE_PREMIUM,
    DEFAULT_COVERAGE_AMOUNT,
    SEISMIC_ZONES,
    DEFAULT_SEISMIC_ZONE,
    HYDRO_RISK_P3_THRESHOLD,
    HYDRO_RISK_P2_THRESHOLD,
    FLOOD_RISK_P4_THRESHOLD,
    FLOOD_RISK_P3_THRESHOLD,
    HYDRO_RISK_SCORE_HIGH,
    HYDRO_RISK_SCORE_MEDIUM,
    HYDRO_RISK_SCORE_LOW,
    FLOOD_RISK_SCORE_CRITICAL,
    FLOOD_RISK_SCORE_HIGH,
    FLOOD_RISK_SCORE_LOW,
    SOLAR_KWH_PER_KWP_NORTH,
    SOLAR_KWH_PER_KWP_CENTER,
    SOLAR_KWH_PER_KWP_SOUTH,
    SOLAR_DEFAULT_SYSTEM_SIZE_KW,
    SOLAR_SYSTEM_EFFICIENCY,
    SOLAR_ELECTRICITY_PRICE_EUR_KWH,
    SOLAR_FIXED_ANNUAL_COST,
    SOLAR_AVERAGE_HOME_CONSUMPTION_KWH,
    SOLAR_SYSTEM_COST_EUR,
    SOLAR_LATITUDE_NORTH_THRESHOLD,
    SOLAR_LATITUDE_CENTER_THRESHOLD,
    API_TIMEOUT_DEFAULT,
    API_TIMEOUT_EMBEDDING,
    MAX_CONVERSATION_HISTORY,
    ADA_SYSTEM_PROMPT,
    get_seismic_zone_info,
)

load_dotenv()

# VERIFY MODULE IS LOADED
print("=" * 80)
print("🔄 ADA_ENGINE.PY LOADED - PRODUCTION VERSION")
print("=" * 80)


class ADAEngine:
    """
    Core engine per A.D.A. - Gestisce AI, tools e conversazione.
    """
    
    def __init__(self, supabase_client):
        print("🎯 ADAEngine.__init__() called - Using FIXED version with tool calling")
        self.supabase = supabase_client
        self.openrouter_key = os.getenv("OPENROUTER_API_KEY")
        self.model = "anthropic/claude-3.5-sonnet"
        print(f"🔑 OpenRouter API Key present: {bool(self.openrouter_key)}")
        print(f"📡 Model: {self.model}")
        
        # Tool registry
        self.tools = {
            "client_profile_lookup": self.tool_client_profile,
            "policy_status_check": self.tool_policy_status,
            "risk_assessment": self.tool_risk_assessment,
            "solar_potential_calc": self.tool_solar_potential,
            "doc_retriever_rag": self.tool_rag_retriever,
            "premium_calculator": self.tool_premium_calculator,
            "database_explorer": self.tool_database_explorer
        }
        # Tool definitions for Claude (OpenAI-compatible format for OpenRouter)
        self.tool_definitions = [
            {
                "type": "function",
                "function": {
                    "name": "client_profile_lookup",
                    "description": "Get client demographics, age, profession, income, CLV, and property information. Use ONLY for questions about client personal info, NOT for policies. Keywords: profilo, età, professione, reddito, informazioni personali.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "client_id": {
                                "type": "integer",
                                "description": "Client ID (codice_cliente)"
                            }
                        },
                        "required": ["client_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "policy_status_check",
                    "description": "Get ALL active insurance policies for a client with details (product name, premium, expiration date). Use this tool when user asks about policies, polizze, coverage, coperture, contratti. Keywords: polizze, polizza, policies, copertura, contratti, assicurazione.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "client_id": {
                                "type": "integer",
                                "description": "Client ID"
                            }
                        },
                        "required": ["client_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "risk_assessment",
                    "description": "Analyze comprehensive risk profile including seismic, hydrogeological, and flood risk. Returns risk score 0-100 and category.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "client_id": {
                                "type": "integer",
                                "description": "Client ID to assess property risk"
                            }
                        },
                        "required": ["client_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "solar_potential_calc",
                    "description": "Calculate solar energy production potential. Returns annual kWh, ROI estimate, and savings.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "client_id": {
                                "type": "integer",
                                "description": "Client ID for property location"
                            }
                        },
                        "required": ["client_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "doc_retriever_rag",
                    "description": "Search historical client interactions using semantic search. Returns relevant past conversations, claims, or notes.",
                    "parameters": {
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
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "premium_calculator",
                    "description": "Calculate insurance premium quote based on risk score, product type, and coverage amount.",
                    "parameters": {
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
            },
            {
                "type": "function",
                "function": {
                    "name": "database_explorer",
                    "description": "General purpose database tool. Use this to query tables directly when no specific tool matches. Allows counting records or listing details. useful for questions like 'quante case ha', 'elenca i sinistri', etc.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "table_name": {
                                "type": "string",
                                "description": "Table to query",
                                "enum": ["clienti", "abitazioni", "polizze", "sinistri", "interactions"]
                            },
                            "client_id": {
                                "type": "integer",
                                "description": "Optional client ID filter"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Max records to return (default 10)",
                                "default": 10
                            }
                        },
                        "required": ["table_name"]
                    }
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

            # DEBUG: Log response structure
            print(f"[DEBUG] API Response keys: {list(response.keys())}")
            if "choices" in response:
                choice = response["choices"][0]
                print(f"[DEBUG] Finish reason: {choice.get('finish_reason')}")
                if choice.get("finish_reason") == "tool_calls":
                    tool_calls = choice.get("message", {}).get("tool_calls", [])
                    print(f"[DEBUG] Tool calls detected: {[tc['function']['name'] for tc in tool_calls]}")

            # Process tool calls if any
            choice = response.get("choices", [{}])[0]
            if choice.get("finish_reason") == "tool_calls":
                print("[DEBUG] Processing tool calls...")
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
            for msg in history[-MAX_CONVERSATION_HISTORY:]:  # Last N messages only
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
        
        response = requests.post(url, headers=headers, json=payload, timeout=API_TIMEOUT_DEFAULT)
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
        """Extract list of tools used from response."""
        tools = []

        # Check if response has choices with tool_calls
        if "choices" in response:
            for choice in response["choices"]:
                message = choice.get("message", {})
                tool_calls = message.get("tool_calls", [])

                for tool_call in tool_calls:
                    tool_name = tool_call.get("function", {}).get("name")
                    if tool_name:
                        tools.append(tool_name)

        return tools
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for A.D.A. from constants."""
        return ADA_SYSTEM_PROMPT

    # ========================================================================
    # TOOLS IMPLEMENTATION
    # ========================================================================
    
    def tool_client_profile(self, client_id: int) -> Dict:
        """Tool: Get client profile."""
        print(f"[DEBUG] Executing tool_client_profile for {client_id}")
        try:
            # Simple direct queries for reliability
            client = self.supabase.table("clienti").select("*").eq("codice_cliente", client_id).single().execute()
            abit = self.supabase.table("abitazioni").select("*").eq("codice_cliente", client_id).execute()
            
            return {
                "profile": {
                    "cliente": client.data,
                    "abitazioni": abit.data if abit.data else []
                }
            }
            
        except Exception as e:
            print(f"[ERROR] tool_client_profile: {e}")
            return {"error": f"Cliente non trovato: {str(e)}"}
    
    def tool_policy_status(self, client_id: int) -> Dict:
        """Tool: Get active policies."""
        print(f"[DEBUG] Executing tool_policy_status for {client_id}")
        try:
            # Query all policies for this client
            response = self.supabase.table("polizze").select("*").eq("codice_cliente", client_id).execute()

            print(f"[DEBUG] Found {len(response.data)} policies in database")

            if not response.data or len(response.data) == 0:
                print(f"[DEBUG] No policies found for client {client_id}")
                return {
                    "policies": [],
                    "count": 0,
                    "message": f"Nessuna polizza trovata per il cliente {client_id}"
                }

            # Map columns with ALL important details
            policies = []
            for p in response.data:
                policy_data = {
                    "prodotto": p.get("prodotto"),
                    "area_bisogno": p.get("area_bisogno"),
                    "stato": p.get("stato_polizza"),
                    "data_emissione": p.get("data_emissione"),
                    "data_scadenza": p.get("data_scadenza"),
                    "premio_ricorrente": p.get("premio_ricorrente"),
                    "premio_unico": p.get("premio_unico"),
                    "premio_totale_annuo": p.get("premio_totale_annuo"),
                    "capitale_rivalutato": p.get("capitale_rivalutato"),
                    "massimale": p.get("massimale")
                }
                policies.append(policy_data)
                print(f"[DEBUG] Policy: {policy_data['prodotto']} - {policy_data['stato']}")

            return {
                "policies": policies,
                "count": len(policies),
                "message": f"Trovate {len(policies)} polizze per il cliente {client_id}"
            }

        except Exception as e:
            print(f"[ERROR] tool_policy_status: {e}")
            return {"error": str(e), "policies": [], "count": 0}
    
    def tool_risk_assessment(self, client_id: int) -> Dict:
        """Tool: Assess property risk."""
        print(f"[DEBUG] Executing tool_risk_assessment for {client_id}")
        try:
            response = self.supabase.table("abitazioni").select(
                "risk_score, risk_category, zona_sismica, "
                "hydro_risk_p3, hydro_risk_p2, flood_risk_p4, flood_risk_p3, citta"
            ).eq("codice_cliente", client_id).single().execute()
            
            data = response.data

            # Calculate breakdown using constants
            zona = data.get("zona_sismica", DEFAULT_SEISMIC_ZONE)
            seismic = get_seismic_zone_info(zona)

            # Hydrogeological risk scoring using constants
            hydro_risk_p3 = data.get("hydro_risk_p3", 0)
            hydro_risk_p2 = data.get("hydro_risk_p2", 0)
            hydro_score = (
                HYDRO_RISK_SCORE_HIGH if hydro_risk_p3 > HYDRO_RISK_P3_THRESHOLD
                else HYDRO_RISK_SCORE_MEDIUM if hydro_risk_p2 > HYDRO_RISK_P2_THRESHOLD
                else HYDRO_RISK_SCORE_LOW
            )

            # Flood risk scoring using constants
            flood_risk_p4 = data.get("flood_risk_p4", 0)
            flood_risk_p3 = data.get("flood_risk_p3", 0)
            flood_score = (
                FLOOD_RISK_SCORE_CRITICAL if flood_risk_p4 > FLOOD_RISK_P4_THRESHOLD
                else FLOOD_RISK_SCORE_HIGH if flood_risk_p3 > FLOOD_RISK_P3_THRESHOLD
                else FLOOD_RISK_SCORE_LOW
            )
            
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
            print(f"[ERROR] tool_risk_assessment: {e}")
            return {"error": str(e)}
    
    def tool_solar_potential(self, client_id: int) -> Dict:
        """Tool: Calculate solar potential."""
        print(f"[DEBUG] Executing tool_solar_potential for {client_id}")
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
            
            # Otherwise estimate using constants
            lat = data.get("latitudine", 42)
            kwh_per_kwp = (
                SOLAR_KWH_PER_KWP_NORTH if lat > SOLAR_LATITUDE_NORTH_THRESHOLD
                else SOLAR_KWH_PER_KWP_CENTER if lat > SOLAR_LATITUDE_CENTER_THRESHOLD
                else SOLAR_KWH_PER_KWP_SOUTH
            )
            kwh_annual = int(SOLAR_DEFAULT_SYSTEM_SIZE_KW * kwh_per_kwp * SOLAR_SYSTEM_EFFICIENCY)

            savings = int(kwh_annual * SOLAR_ELECTRICITY_PRICE_EUR_KWH - SOLAR_FIXED_ANNUAL_COST)
            coverage = min(100, int((kwh_annual / SOLAR_AVERAGE_HOME_CONSUMPTION_KWH) * 100))
            
            return {
                "kwh_annual": kwh_annual,
                "savings_euro": savings,
                "coverage_percent": coverage,
                "roi_years": round(SOLAR_SYSTEM_COST_EUR / savings, 1) if savings > 0 else 99,
                "location": data.get("citta"),
                "source": "estimated"
            }
            
        except Exception as e:
            print(f"[ERROR] tool_solar_potential: {e}")
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
                timeout=API_TIMEOUT_EMBEDDING
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
    
    def tool_premium_calculator(self, risk_score: float, product_type: str, coverage_amount: float = DEFAULT_COVERAGE_AMOUNT) -> Dict:
        """Tool: Calculate premium using constants."""
        base = BASE_PREMIUMS.get(product_type, DEFAULT_BASE_PREMIUM)
        risk_multiplier = 1 + (risk_score / 100)
        coverage_factor = coverage_amount / DEFAULT_COVERAGE_AMOUNT
        
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

    def tool_database_explorer(self, table_name: str, client_id: Optional[int] = None, limit: int = 10) -> Dict:
        """Tool: Generic database explorer."""
        print(f"[DEBUG] Executing tool_database_explorer on {table_name}")
        try:
            query = self.supabase.table(table_name).select("*")
            
            if client_id:
                query = query.eq("codice_cliente", client_id)
            
            response = query.limit(limit).execute()
            
            return {
                "table": table_name,
                "count": len(response.data),
                "data": response.data,
                "message": f"Retrieved {len(response.data)} records from {table_name}"
            }
            
        except Exception as e:
            print(f"[ERROR] tool_database_explorer: {e}")
            return {"error": str(e)}
