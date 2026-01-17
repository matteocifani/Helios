#!/usr/bin/env python3
"""
=============================================================================
HOUSE ANALYSIS PIPELINE - Analisi Completa Proprietà Residenziali
=============================================================================

Pipeline unificata che:
1. Cattura screenshot satellitare da Google Maps
2. Rileva pannelli solari con YOLOv8 (segmentazione)
3. Analizza la proprietà con LLM multimodale (OpenRouter)

Uso:
    python house_analysis_pipeline.py "Via Roma 123, Milano"
    python house_analysis_pipeline.py "Via Roma 123, Milano" --model openai/gpt-4o
    python house_analysis_pipeline.py "Via Roma 123, Milano" --skip-scrape  # usa screenshot esistente

Output:
    - results/<indirizzo_normalizzato>/
        - satellite_view.png          (screenshot satellitare)
        - solar_detection.json        (risultati YOLOv8)
        - solar_annotated.png         (immagine con pannelli evidenziati)
        - llm_analysis.json           (analisi LLM completa)
        - analysis_report.json        (report unificato finale)

Requisiti:
    - playwright (pip install playwright && playwright install chromium)
    - ultralytics (pip install ultralytics)
    - httpx (pip install httpx)
    - opencv-python, numpy
    - File .env con OPENROUTER_API_KEY nella root del progetto

Autore: Pipeline generata automaticamente
Data: Gennaio 2026
=============================================================================
"""

import os
import sys
import json
import time
import random
import re
import base64
import argparse
from pathlib import Path
from datetime import datetime

# ============================================================================
# CONFIGURAZIONE GLOBALE
# ============================================================================

SCRIPT_DIR = Path(__file__).parent
DEFAULT_LLM_MODEL = "google/gemini-2.0-flash-001"
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Prompt per l'analisi LLM
LLM_ANALYSIS_PROMPT = """Analizza questa immagine satellitare/aerea di una proprietà residenziale.

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


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def normalize_address(address: str) -> str:
    """Normalizza l'indirizzo per usarlo come nome cartella"""
    # Rimuovi caratteri speciali, sostituisci spazi con underscore
    normalized = re.sub(r'[^\w\s-]', '', address)
    normalized = re.sub(r'\s+', '_', normalized)
    return normalized[:80]  # Limita lunghezza


def random_delay(min_sec=2, max_sec=5):
    """Delay casuale per sembrare più umano"""
    delay = random.uniform(min_sec, max_sec)
    time.sleep(delay)


def get_api_key() -> str | None:
    """Recupera API key da ambiente o file .env"""
    key = os.environ.get("OPENROUTER_API_KEY")
    if key:
        return key
    
    # Prova a leggere da .env nella root del progetto
    for env_path in [SCRIPT_DIR.parent / ".env", SCRIPT_DIR / ".env"]:
        if env_path.exists():
            with open(env_path) as f:
                for line in f:
                    if line.startswith("OPENROUTER_API_KEY="):
                        return line.split("=", 1)[1].strip().strip('"\'')
    return None


def print_section(title: str):
    """Stampa intestazione sezione"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


# ============================================================================
# STEP 1: SATELLITE SCRAPER
# ============================================================================

def capture_satellite_screenshot(address: str, output_path: Path) -> bool:
    """
    Cattura screenshot satellitare da Google Maps.
    
    Args:
        address: Indirizzo da cercare
        output_path: Path dove salvare lo screenshot
    
    Returns:
        True se successo, False altrimenti
    """
    from playwright.sync_api import sync_playwright
    import urllib.parse
    
    print_section("STEP 1: Cattura Screenshot Satellitare")
    print(f"Indirizzo: {address}")
    print(f"Output: {output_path}")
    
    try:
        with sync_playwright() as p:
            # Browser con opzioni anti-blocco
            browser = p.chromium.launch(
                headless=False,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage",
                    "--no-first-run",
                    "--no-default-browser-check",
                    "--disable-popup-blocking",
                ]
            )
            
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 2560, "height": 1440},
                timezone_id="Europe/Rome",
                locale="it-IT",
            )
            
            page = context.new_page()
            
            # 1. Apertura Google Maps
            print("[1/6] Apertura Google Maps...")
            page.goto("https://www.google.com/maps", wait_until="networkidle")
            random_delay(5, 8)
            
            # 2. Gestione cookie
            print("[2/6] Gestione cookie...")
            cookie_selectors = [
                'button:has-text("Accetta tutto")',
                'button:has-text("Accept all")',
                'button[aria-label*="Accetta"]',
            ]
            for selector in cookie_selectors:
                try:
                    btn = page.locator(selector).first
                    if btn.is_visible(timeout=3000):
                        btn.click()
                        print("      ✓ Cookie accettati")
                        random_delay(4, 6)
                        break
                except:
                    continue
            
            # 3. Ricerca indirizzo
            print(f"[3/6] Ricerca indirizzo...")
            encoded_address = urllib.parse.quote(address)
            search_url = f"https://www.google.com/maps/search/{encoded_address}"
            page.goto(search_url, wait_until="domcontentloaded")
            random_delay(10, 14)
            
            try:
                page.wait_for_load_state("networkidle", timeout=20000)
            except:
                pass
            
            # 4. Click sul risultato
            print("[4/6] Centrando sulla casa...")
            result_selectors = ['h1.DUwDvf', 'div[role="article"]', 'div.Nv2PK']
            for selector in result_selectors:
                try:
                    result = page.locator(selector).first
                    if result.is_visible(timeout=3000):
                        result.click()
                        random_delay(4, 6)
                        break
                except:
                    continue
            
            # 5. Attivazione satellite e zoom
            print("[5/6] Attivazione vista satellite + zoom...")
            current_url = page.url
            
            # Estrai coordinate e naviga con satellite + zoom massimo
            coords_match = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', current_url)
            if coords_match:
                lat, lng = coords_match.group(1), coords_match.group(2)
                zoom_url = f"https://www.google.com/maps/@{lat},{lng},22z/data=!3m1!1e3"
                page.goto(zoom_url, wait_until="domcontentloaded")
                random_delay(8, 12)
                print(f"      ✓ Coordinate: {lat}, {lng}")
            else:
                # Fallback: aggiungi satellite all'URL corrente
                if "/data=" in current_url:
                    satellite_url = current_url.split("/data=")[0] + "/data=!3m1!1e3"
                else:
                    satellite_url = current_url + "/data=!3m1!1e3"
                page.goto(satellite_url, wait_until="domcontentloaded")
                random_delay(8, 12)
            
            # Attesa caricamento tile
            print("      Attesa caricamento tile (15s)...")
            time.sleep(15)
            
            # Rimozione etichette
            try:
                page.evaluate("""
                    const labels = document.querySelectorAll('[data-label], [class*="label"], [class*="Label"]');
                    labels.forEach(el => el.style.display = 'none');
                    const markers = document.querySelectorAll('[class*="marker"], [class*="Marker"], [class*="poi"]');
                    markers.forEach(el => el.style.display = 'none');
                    const svgTexts = document.querySelectorAll('svg text, svg tspan');
                    svgTexts.forEach(el => el.style.display = 'none');
                """)
            except:
                pass
            
            time.sleep(3)
            
            # 6. Screenshot
            print("[6/6] Cattura screenshot...")
            viewport_width, viewport_height = 2560, 1440
            crop_size = 1000
            crop_x = (viewport_width - crop_size) // 2
            crop_y = (viewport_height - crop_size) // 2
            
            page.screenshot(
                path=str(output_path),
                full_page=False,
                clip={"x": crop_x, "y": crop_y, "width": crop_size, "height": crop_size}
            )
            print(f"      ✓ Screenshot salvato: {output_path.name}")
            
            # Mantieni aperto brevemente per verifica
            time.sleep(5)
            browser.close()
            
            return True
            
    except Exception as e:
        print(f"      ✗ Errore scraping: {e}")
        return False


# ============================================================================
# STEP 2: SOLAR PANEL DETECTION (YOLOv8)
# ============================================================================

def detect_solar_panels(image_path: Path, output_dir: Path) -> dict:
    """
    Rileva pannelli solari usando YOLOv8 segmentation.
    
    Args:
        image_path: Path dell'immagine da analizzare
        output_dir: Directory per i risultati
    
    Returns:
        dict con statistiche rilevamento
    """
    import cv2
    import numpy as np
    from ultralytics import YOLO
    
    print_section("STEP 2: Rilevamento Pannelli Solari (YOLOv8)")
    print(f"Immagine: {image_path}")
    
    # Carica modello
    model_path = SCRIPT_DIR / "solar_panel_yolov8s.pt"
    if not model_path.exists():
        print(f"      ✗ Modello non trovato: {model_path}")
        return {"error": "Modello YOLOv8 non trovato"}
    
    print(f"      Modello: {model_path.name}")
    model = YOLO(str(model_path))
    
    # Esegui inference
    results = model.predict(source=str(image_path), conf=0.25, task='segment', verbose=False)
    res = results[0]
    
    img = cv2.imread(str(image_path))
    h, w = img.shape[:2]
    cx, cy = w // 2, h // 2
    max_distance = min(w, h) * 0.4
    
    stats = {
        'total_area_pixels': h * w,
        'solar_panel_instances': 0,
        'solar_panel_area_pixels': 0,
        'coverage_percentage': 0.0,
        'detections': []
    }
    
    if hasattr(res, 'masks') and res.masks is not None:
        masks = res.masks.data
        confs = res.boxes.conf.cpu().numpy()
        boxes = res.boxes.xyxy.cpu().numpy()
        masks_np = masks.cpu().numpy()
        
        total_area = 0
        valid_count = 0
        
        for i, mask in enumerate(masks_np):
            mask_resized = cv2.resize(mask.astype(np.float32), (w, h))
            mask_binary = (mask_resized > 0.5).astype(np.uint8)
            
            if i < len(boxes):
                x1, y1, x2, y2 = boxes[i]
                det_cx, det_cy = (x1 + x2) / 2, (y1 + y2) / 2
                distance = ((det_cx - cx) ** 2 + (det_cy - cy) ** 2) ** 0.5
                
                if distance > max_distance:
                    continue
                
                box_w, box_h = x2 - x1, y2 - y1
                aspect_ratio = max(box_w, box_h) / (min(box_w, box_h) + 1)
                if aspect_ratio > 5:
                    continue
            
            area = int(np.sum(mask_binary))
            confidence = float(confs[i]) if i < len(confs) else 0.0
            
            total_area += area
            valid_count += 1
            
            # Colora la mask
            img[mask_binary == 1] = [255, 165, 0]
            
            stats['detections'].append({
                'instance': valid_count,
                'area_pixels': area,
                'confidence': round(confidence, 4)
            })
        
        stats['solar_panel_instances'] = valid_count
        stats['solar_panel_area_pixels'] = total_area
        stats['coverage_percentage'] = round((total_area / (h * w)) * 100, 2)
    
    # Salva immagine annotata
    annotated_path = output_dir / "solar_annotated.png"
    cv2.imwrite(str(annotated_path), img)
    
    # Salva JSON
    json_path = output_dir / "solar_detection.json"
    with open(json_path, 'w') as f:
        json.dump(stats, f, indent=2)
    
    print(f"      ✓ Pannelli rilevati: {stats['solar_panel_instances']}")
    print(f"      ✓ Area totale: {stats['solar_panel_area_pixels']} px")
    print(f"      ✓ Copertura: {stats['coverage_percentage']}%")
    
    return stats


# ============================================================================
# STEP 3: LLM VISION ANALYSIS
# ============================================================================

def analyze_with_llm(image_path: Path, output_dir: Path, model: str = DEFAULT_LLM_MODEL) -> dict:
    """
    Analizza l'immagine con un LLM multimodale via OpenRouter.
    
    Args:
        image_path: Path dell'immagine da analizzare
        output_dir: Directory per i risultati
        model: ID del modello OpenRouter
    
    Returns:
        dict con analisi LLM
    """
    import httpx
    
    print_section("STEP 3: Analisi LLM Multimodale")
    print(f"Modello: {model}")
    
    api_key = get_api_key()
    if not api_key:
        print("      ✗ API key OpenRouter non trovata!")
        return {"error": "API key mancante"}
    
    # Codifica immagine
    with open(image_path, "rb") as f:
        image_b64 = base64.b64encode(f.read()).decode("utf-8")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/satellite-house-analyzer",
        "X-Title": "House Analysis Pipeline"
    }
    
    payload = {
        "model": model,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": LLM_ANALYSIS_PROMPT},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}"}}
            ]
        }],
        "temperature": 0.1,
        "max_tokens": 2000
    }
    
    print("      Invio richiesta...")
    
    try:
        with httpx.Client(timeout=60.0) as client:
            response = client.post(OPENROUTER_API_URL, headers=headers, json=payload)
        
        if response.status_code != 200:
            print(f"      ✗ Errore API: {response.status_code}")
            return {"error": f"API error: {response.status_code}"}
        
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        
        # Parse JSON dalla risposta
        try:
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            analysis = json.loads(content.strip())
        except json.JSONDecodeError:
            analysis = {"raw_response": content, "parse_error": True}
        
        # Aggiungi metadata
        analysis["_metadata"] = {
            "model": model,
            "tokens_used": result.get("usage", {}).get("total_tokens", 0)
        }
        
        # Salva JSON
        json_path = output_dir / "llm_analysis.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)
        
        # Stampa riassunto
        if "pannelli_solari" in analysis:
            ps = analysis["pannelli_solari"]
            print(f"      🔆 Pannelli solari: {'SÌ' if ps.get('presenti') else 'NO'}")
        if "piscina" in analysis:
            p = analysis["piscina"]
            print(f"      🏊 Piscina: {'SÌ' if p.get('presente') else 'NO'}")
        if "vegetazione" in analysis:
            v = analysis["vegetazione"]
            print(f"      🌳 Alberi ombreggianti: {'SÌ' if v.get('alberi_ombra_tetto') else 'NO'}")
        if "sintesi" in analysis:
            print(f"      📋 Sintesi: {analysis['sintesi'][:100]}...")
        
        print(f"      ✓ Token usati: {analysis['_metadata'].get('tokens_used', 'N/D')}")
        
        return analysis
        
    except Exception as e:
        print(f"      ✗ Errore: {e}")
        return {"error": str(e)}


# ============================================================================
# MAIN PIPELINE
# ============================================================================

def run_pipeline(address: str, model: str = DEFAULT_LLM_MODEL, skip_scrape: bool = False):
    """
    Esegue la pipeline completa di analisi.
    
    Args:
        address: Indirizzo da analizzare
        model: Modello LLM da usare
        skip_scrape: Se True, usa screenshot esistente
    """
    print("\n" + "="*60)
    print("  🏠 HOUSE ANALYSIS PIPELINE")
    print("="*60)
    print(f"\n  Indirizzo: {address}")
    print(f"  Modello LLM: {model}")
    print(f"  Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Crea directory output
    normalized = normalize_address(address)
    output_dir = SCRIPT_DIR / "results" / normalized
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"  Output dir: {output_dir}")
    
    screenshot_path = output_dir / "satellite_view.png"
    
    # STEP 1: Screenshot
    if skip_scrape:
        if screenshot_path.exists():
            print(f"\n[SKIP] Usando screenshot esistente: {screenshot_path}")
        else:
            print(f"\n[ERROR] Screenshot non trovato: {screenshot_path}")
            return
    else:
        success = capture_satellite_screenshot(address, screenshot_path)
        if not success:
            print("\n[ERROR] Impossibile catturare screenshot. Pipeline interrotta.")
            return
    
    # STEP 2: Solar detection
    solar_stats = detect_solar_panels(screenshot_path, output_dir)
    
    # STEP 3: LLM analysis
    llm_analysis = analyze_with_llm(screenshot_path, output_dir, model)
    
    # Genera report finale unificato
    print_section("REPORT FINALE")
    
    final_report = {
        "address": address,
        "timestamp": datetime.now().isoformat(),
        "llm_model": model,
        "files": {
            "screenshot": str(screenshot_path),
            "solar_annotated": str(output_dir / "solar_annotated.png"),
            "solar_detection": str(output_dir / "solar_detection.json"),
            "llm_analysis": str(output_dir / "llm_analysis.json")
        },
        "solar_detection_yolo": {
            "panels_detected": solar_stats.get("solar_panel_instances", 0),
            "total_area_pixels": solar_stats.get("solar_panel_area_pixels", 0),
            "coverage_percentage": solar_stats.get("coverage_percentage", 0.0)
        },
        "llm_analysis_summary": {
            "pannelli_solari": llm_analysis.get("pannelli_solari", {}),
            "piscina": llm_analysis.get("piscina", {}),
            "vegetazione": llm_analysis.get("vegetazione", {}),
            "tetto": llm_analysis.get("tetto", {}),
            "sintesi": llm_analysis.get("sintesi", "")
        }
    }
    
    # Salva report
    report_path = output_dir / "analysis_report.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(final_report, f, indent=2, ensure_ascii=False)
    
    # Stampa riassunto
    print(f"Indirizzo: {address}")
    print(f"\n📊 RILEVAMENTO YOLO:")
    print(f"   Pannelli solari: {solar_stats.get('solar_panel_instances', 0)}")
    print(f"   Copertura: {solar_stats.get('coverage_percentage', 0.0)}%")
    
    print(f"\n🤖 ANALISI LLM ({model}):")
    if "pannelli_solari" in llm_analysis:
        ps = llm_analysis["pannelli_solari"]
        print(f"   Pannelli: {'SÌ' if ps.get('presenti') else 'NO'} ({ps.get('quantita_stimata', 'N/D')} stimati)")
    if "piscina" in llm_analysis:
        p = llm_analysis["piscina"]
        print(f"   Piscina: {'SÌ' if p.get('presente') else 'NO'}")
    if "vegetazione" in llm_analysis:
        v = llm_analysis["vegetazione"]
        print(f"   Alberi ombreggianti: {'SÌ' if v.get('alberi_ombra_tetto') else 'NO'}")
    if "sintesi" in llm_analysis:
        print(f"\n📋 SINTESI: {llm_analysis['sintesi']}")
    
    print(f"\n✅ Report salvato: {report_path}")
    print(f"📁 Tutti i file in: {output_dir}")
    
    return final_report


# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Pipeline completa per l'analisi di proprietà residenziali da immagini satellitari",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Esempi:
  python house_analysis_pipeline.py "Via Roma 123, Milano"
  python house_analysis_pipeline.py "Via Roma 123, Milano" --model openai/gpt-4o
  python house_analysis_pipeline.py "Via Roma 123, Milano" --skip-scrape
        """
    )
    
    parser.add_argument("address", type=str, help="Indirizzo della proprietà da analizzare")
    parser.add_argument("--model", type=str, default=DEFAULT_LLM_MODEL,
                        help=f"Modello LLM (default: {DEFAULT_LLM_MODEL})")
    parser.add_argument("--skip-scrape", action="store_true",
                        help="Salta lo scraping e usa screenshot esistente")
    
    args = parser.parse_args()
    
    run_pipeline(args.address, args.model, args.skip_scrape)


if __name__ == "__main__":
    main()
