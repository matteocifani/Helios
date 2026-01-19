
import os
import json
import base64
import requests
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DEFAULT_MODEL = "google/gemini-2.0-flash-001"
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

ANALYSIS_PROMPT = """Analizza questa immagine satellitare/aerea di una proprietà residenziale.

Identifica e descrivi le seguenti caratteristiche, indicando per ciascuna:
- Se è presente (sì/no)
- Posizione approssimativa nell'immagine
- Dimensione stimata o quantità
- Eventuali note aggiuntive

CARATTERISTICHE DA ANALIZZARE:

1. **PANNELLI SOLARI**
   - Sono presenti pannelli solari sul tetto?
   - Quanti pannelli circa?
   - Coprono quale percentuale del tetto?

2. **PISCINA**
   - È presente una piscina nella proprietà?
   - Forma (rettangolare, ovale, irregolare)?
   - Dimensione approssimativa?

3. **ALBERI E VEGETAZIONE**
   - Ci sono alberi vicino alla casa?
   - Ci sono alberi che potrebbero fare ombra sul tetto?
   - Il giardino è curato o trascurato?

4. **CARATTERISTICHE DEL TETTO**
   - Tipo di tetto (tegole, lamiera, piano)?
   - Condizioni generali (buono, da riparare)?
   - Presenza di lucernari, antenne, camini?

5. **PROPRIETÀ E DINTORNI**
   - Dimensione approssimativa del lotto
   - Presenza di garage/box auto
   - Presenza di altri edifici annessi
   - Tipo di recinzione (se visibile)

6. **ALTRE OSSERVAZIONI**
   - Qualsiasi altra caratteristica rilevante

Rispondi in formato JSON strutturato con questa struttura:
{
  "pannelli_solari": {
    "presenti": true/false,
    "quantita_stimata": numero o null,
    "copertura_tetto_percentuale": numero o null,
    "note": "descrizione"
  },
  "piscina": {
    "presente": true/false,
    "forma": "descrizione" o null,
    "dimensione": "descrizione" o null,
    "note": "descrizione"
  },
  "vegetazione": {
    "alberi_vicino_casa": true/false,
    "alberi_ombra_tetto": true/false,
    "giardino_curato": true/false,
    "note": "descrizione"
  },
  "tetto": {
    "tipo": "descrizione",
    "condizioni": "buono/medio/scarso",
    "lucernari": true/false,
    "antenne": true/false,
    "camini": true/false,
    "note": "descrizione"
  },
  "proprieta": {
    "dimensione_lotto": "descrizione",
    "garage": true/false,
    "edifici_annessi": true/false,
    "recinzione": "descrizione" o null,
    "note": "descrizione"
  },
  "altre_osservazioni": "descrizione",
  "sintesi": "breve riassunto complessivo della proprietà"
}
"""

def get_api_key():
    """Recupera API key da ambiente"""
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        # Fallback location check if needed, but os.getenv should suffice if load_dotenv worked
        pass
    return key

def encode_image_base64(image_path: str) -> str:
    """Codifica immagine in base64"""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def get_image_media_type(image_path: str) -> str:
    """Determina il media type dell'immagine"""
    ext = Path(image_path).suffix.lower()
    return {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp"
    }.get(ext, "image/png")

def analyze_image(image_path: str, model: str = DEFAULT_MODEL, api_key: str = None) -> dict:
    """
    Analizza un'immagine satellitare usando un LLM multimodale via OpenRouter.
    
    Args:
        image_path: Percorso dell'immagine da analizzare
        model: ID del modello OpenRouter da usare
        api_key: API key OpenRouter (opzionale, usa env var se non fornita)
    
    Returns:
        dict con l'analisi strutturata
    """
    if not api_key:
        api_key = get_api_key()
    
    if not api_key:
         return {"error": "API key OpenRouter non trovata"}
    
    if not os.path.exists(image_path):
        return {"error": f"Immagine non trovata: {image_path}"}
    
    try:
        # Prepara l'immagine
        image_b64 = encode_image_base64(image_path)
        media_type = get_image_media_type(image_path)
        
        # Costruisci la richiesta
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/satellite-house-analyzer",
            "X-Title": "Satellite House Analyzer"
        }
        
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": ANALYSIS_PROMPT
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{media_type};base64,{image_b64}"
                            }
                        }
                    ]
                }
            ],
            "temperature": 0.1,  # Bassa per output più deterministico
            "max_tokens": 2000
        }
        
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=payload, timeout=60)
        
        if response.status_code != 200:
            return {"error": f"API Error {response.status_code}: {response.text}"}
        
        result = response.json()
        
        # Estrai il contenuto della risposta
        if "choices" in result and len(result["choices"]) > 0:
            content = result["choices"][0]["message"]["content"]
            
            # Prova a parsare come JSON
            try:
                # Rimuovi eventuale markdown code block
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0]
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0]
                
                analysis = json.loads(content.strip())
            except json.JSONDecodeError:
                # Se non è JSON valido, restituisci come testo
                analysis = {
                    "raw_response": content,
                    "parse_error": "La risposta non era in formato JSON valido"
                }
            
            # Aggiungi metadata
            analysis["_metadata"] = {
                "model": model,
                "usage": result.get("usage", {})
            }
            
            return analysis
        else:
             return {"error": "Nessuna risposta dal modello"}
             
    except Exception as e:
        return {"error": str(e)}
