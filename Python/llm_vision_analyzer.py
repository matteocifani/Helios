#!/usr/bin/env python3
"""
Analisi avanzata di immagini satellitari tramite LLM multimodale (OpenRouter).

Modelli consigliati per immagini aeree/satellitari (in ordine di raccomandazione):
1. google/gemini-2.0-flash-001         — veloce, economico, ottimo su dati geo
2. openai/gpt-4o                        — molto preciso, più costoso
3. anthropic/claude-3.5-sonnet          — ottimo reasoning visivo
4. google/gemini-1.5-pro                — forte su immagini complesse

Uso:
    export OPENROUTER_API_KEY="sk-or-..."
    python llm_vision_analyzer.py [path_immagine]

Output:
    - Stampa analisi strutturata
    - Salva JSON in yolo_results/llm_vision_analysis.json
"""

import os
import sys
import json
import base64
import httpx
from pathlib import Path

# ============ CONFIGURAZIONE ============
# Modello di default (puoi cambiarlo)
DEFAULT_MODEL = "google/gemini-2.0-flash-001"
# Alternative: "openai/gpt-4o", "anthropic/claude-3.5-sonnet", "google/gemini-1.5-pro"

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

ROOT = Path(__file__).parent
OUT_DIR = ROOT / "yolo_results"
OUT_DIR.mkdir(exist_ok=True)

# ============ PROMPT DI ANALISI ============
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
    """Recupera API key da ambiente o file .env"""
    key = os.environ.get("OPENROUTER_API_KEY")
    if key:
        return key
    
    # Prova a leggere da .env nella root del progetto
    env_file = ROOT.parent / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                if line.startswith("OPENROUTER_API_KEY="):
                    return line.split("=", 1)[1].strip().strip('"\'')
    
    # Prova anche nella cartella Python
    env_file2 = ROOT / ".env"
    if env_file2.exists():
        with open(env_file2) as f:
            for line in f:
                if line.startswith("OPENROUTER_API_KEY="):
                    return line.split("=", 1)[1].strip().strip('"\'')
    
    return None

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
        raise ValueError(
            "API key OpenRouter non trovata!\n"
            "Imposta la variabile d'ambiente OPENROUTER_API_KEY o crea un file .env"
        )
    
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Immagine non trovata: {image_path}")
    
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
    
    print(f"Invio richiesta a {model}...")
    
    # Invia la richiesta
    with httpx.Client(timeout=60.0) as client:
        response = client.post(OPENROUTER_API_URL, headers=headers, json=payload)
    
    if response.status_code != 200:
        raise Exception(f"Errore API: {response.status_code} - {response.text}")
    
    result = response.json()
    
    # Estrai il contenuto della risposta
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
        "image_path": str(image_path),
        "usage": result.get("usage", {})
    }
    
    return analysis

def main():
    # Percorso immagine (default: satellite_view.png)
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
    else:
        image_path = str(ROOT / "satellite_view.png")
    
    # Modello (opzionale secondo argomento)
    model = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_MODEL
    
    print(f"=== LLM Vision Analyzer ===")
    print(f"Immagine: {image_path}")
    print(f"Modello: {model}")
    print()
    
    try:
        analysis = analyze_image(image_path, model)
        
        # Salva JSON
        out_json = OUT_DIR / "llm_vision_analysis.json"
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)
        
        print("=== ANALISI COMPLETATA ===\n")
        
        # Stampa risultati formattati
        if "pannelli_solari" in analysis:
            ps = analysis["pannelli_solari"]
            print(f"🔆 PANNELLI SOLARI: {'SÌ' if ps.get('presenti') else 'NO'}")
            if ps.get('presenti'):
                print(f"   Quantità: {ps.get('quantita_stimata', 'N/D')}")
                print(f"   Copertura: {ps.get('copertura_tetto_percentuale', 'N/D')}%")
            print()
        
        if "piscina" in analysis:
            p = analysis["piscina"]
            print(f"🏊 PISCINA: {'SÌ' if p.get('presente') else 'NO'}")
            if p.get('presente'):
                print(f"   Forma: {p.get('forma', 'N/D')}")
                print(f"   Dimensione: {p.get('dimensione', 'N/D')}")
            print()
        
        if "vegetazione" in analysis:
            v = analysis["vegetazione"]
            print(f"🌳 VEGETAZIONE:")
            print(f"   Alberi vicino casa: {'SÌ' if v.get('alberi_vicino_casa') else 'NO'}")
            print(f"   Alberi che ombreggiano tetto: {'SÌ' if v.get('alberi_ombra_tetto') else 'NO'}")
            print(f"   Giardino curato: {'SÌ' if v.get('giardino_curato') else 'NO'}")
            print()
        
        if "tetto" in analysis:
            t = analysis["tetto"]
            print(f"🏠 TETTO:")
            print(f"   Tipo: {t.get('tipo', 'N/D')}")
            print(f"   Condizioni: {t.get('condizioni', 'N/D')}")
            print()
        
        if "sintesi" in analysis:
            print(f"📋 SINTESI: {analysis['sintesi']}")
            print()
        
        print(f"✅ Risultati salvati in: {out_json}")
        
        # Info costi
        if "_metadata" in analysis and "usage" in analysis["_metadata"]:
            usage = analysis["_metadata"]["usage"]
            print(f"\n📊 Token usati: {usage.get('total_tokens', 'N/D')}")
    
    except ValueError as e:
        print(f"❌ Errore configurazione: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Errore: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
