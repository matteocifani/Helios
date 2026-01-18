"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                           HELIOS VISION                                        ║
║                   Satellite Image Analysis Pipeline                            ║
╚═══════════════════════════════════════════════════════════════════════════════╝

Pipeline per l'analisi di immagini satellitari di proprietà residenziali:
1. Cattura screenshot satellitare da Google Maps (headless)
2. Rilevamento pannelli solari con YOLOv8
3. Analisi completa con LLM Vision (OpenRouter)

Autore: Helios Team
Data: Gennaio 2026
"""

import os
import sys
import io
import json
import time
import random
import re
import base64
import tempfile
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Callable, Optional, Dict, Any
import urllib.parse

# ============================================================================
# CONFIGURATION
# ============================================================================

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
MODELS_DIR = PROJECT_ROOT / "models"
RESULTS_DIR = PROJECT_ROOT / "vision_results"

DEFAULT_LLM_MODEL = "google/gemini-2.0-flash-001"
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# HuggingFace model for solar panel detection
YOLO_MODEL_URL = "https://huggingface.co/finloop/yolov8s-seg-solar-panels/resolve/main/best.pt"
YOLO_MODEL_NAME = "solar_panel_yolov8s.pt"

# LLM Analysis Prompt
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
    """Normalize address for use as folder name."""
    normalized = re.sub(r'[^\w\s-]', '', address)
    normalized = re.sub(r'\s+', '_', normalized)
    return normalized[:80]


def random_delay(min_sec=2, max_sec=5):
    """Random delay to appear more human-like."""
    delay = random.uniform(min_sec, max_sec)
    time.sleep(delay)


def get_api_key() -> Optional[str]:
    """Get OpenRouter API key from environment or .env file."""
    key = os.environ.get("OPENROUTER_API_KEY")
    if key:
        return key
    
    # Try to read from .env in project root
    for env_path in [PROJECT_ROOT / ".env", SCRIPT_DIR / ".env"]:
        if env_path.exists():
            with open(env_path) as f:
                for line in f:
                    if line.startswith("OPENROUTER_API_KEY="):
                        return line.split("=", 1)[1].strip().strip('"\'')
    return None


# ============================================================================
# SETUP FUNCTIONS
# ============================================================================

def ensure_playwright_installed() -> bool:
    """Ensure Playwright and Chromium are installed."""
    try:
        from playwright.sync_api import sync_playwright
        # Try to launch browser to verify it's installed
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            browser.close()
        return True
    except Exception as e:
        print(f"Playwright not properly installed: {e}")
        try:
            subprocess.run(
                [sys.executable, "-m", "playwright", "install", "chromium"],
                check=True,
                capture_output=True
            )
            return True
        except Exception as install_error:
            print(f"Failed to install Playwright chromium: {install_error}")
            return False


def ensure_yolo_model() -> Optional[Path]:
    """
    Ensure YOLO model is downloaded from HuggingFace.
    Returns path to model file or None if download fails.
    """
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    model_path = MODELS_DIR / YOLO_MODEL_NAME
    
    if model_path.exists():
        return model_path
    
    print(f"Downloading YOLO model from HuggingFace...")
    
    try:
        from huggingface_hub import hf_hub_download
        
        downloaded_path = hf_hub_download(
            repo_id="finloop/yolov8s-seg-solar-panels",
            filename="best.pt",
            local_dir=MODELS_DIR,
            local_dir_use_symlinks=False
        )
        
        # Rename to our standard name
        downloaded = Path(downloaded_path)
        if downloaded.exists() and downloaded.name != YOLO_MODEL_NAME:
            downloaded.rename(model_path)
        
        return model_path
        
    except ImportError:
        # Fallback: use requests if huggingface_hub not available
        try:
            import httpx
            
            print(f"Downloading via HTTP (this may take a minute)...")
            with httpx.stream("GET", YOLO_MODEL_URL, follow_redirects=True, timeout=120.0) as response:
                response.raise_for_status()
                with open(model_path, 'wb') as f:
                    for chunk in response.iter_bytes(chunk_size=8192):
                        f.write(chunk)
            
            return model_path
            
        except Exception as e:
            print(f"Failed to download model: {e}")
            return None
    except Exception as e:
        print(f"Failed to download model: {e}")
        return None


# ============================================================================
# STEP 1: SATELLITE SCREENSHOT (Direct from Google Maps with pin detection)
# ============================================================================

def capture_satellite_screenshot(
    address: str,
    output_path: Path,
    progress_callback: Optional[Callable[[str, float], None]] = None
) -> tuple:
    """
    Capture satellite screenshot directly from Google Maps.
    Zooms in on the pin location and crops around it.

    Args:
        address: Address to search
        output_path: Path to save screenshot
        progress_callback: Optional callback for progress updates

    Returns:
        Tuple of (success: bool, error_message: str or None)
    """
    try:
        from playwright.sync_api import sync_playwright
        from PIL import Image
        import numpy as np
    except ImportError as e:
        if progress_callback:
            progress_callback(f"Errore: dipendenze mancanti", 0)
        return False, f"Dipendenze mancanti: {e}"

    if progress_callback:
        progress_callback("Avvio browser...", 0.1)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=False,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-infobars",
                    "--window-position=0,0",
                    "--window-size=1920,1080"
                ]
            )

            # Larger viewport to have more room for the map
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080},
                locale="it-IT",
                device_scale_factor=1,
            )

            page = context.new_page()

            # Search on Google Maps with satellite view
            if progress_callback:
                progress_callback("Ricerca indirizzo...", 0.2)

            encoded_address = urllib.parse.quote(address)
            search_url = f"https://www.google.com/maps/search/{encoded_address}/data=!3m1!1e3"

            page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
            time.sleep(4)

            # Handle cookies
            if progress_callback:
                progress_callback("Gestione cookie...", 0.3)

            consent_selectors = [
                "button[aria-label='Accept all']",
                "button:has-text('Accept all')",
                "button[aria-label='Accetta tutto']",
                "button:has-text('Accetta tutto')",
            ]
            for selector in consent_selectors:
                try:
                    if page.locator(selector).first.is_visible(timeout=1000):
                        page.locator(selector).first.click()
                        time.sleep(2)
                        break
                except:
                    continue

            time.sleep(3)

            # Take a screenshot to find the pin
            if progress_callback:
                progress_callback("Ricerca pin sulla mappa...", 0.4)

            # Take full page screenshot
            screenshot_bytes = page.screenshot()
            img = Image.open(io.BytesIO(screenshot_bytes))
            img_array = np.array(img)

            # Find the red/orange pin marker
            # Google Maps pin is typically red (#EA4335) or similar
            # We look for red-ish pixels
            red_channel = img_array[:, :, 0]
            green_channel = img_array[:, :, 1]
            blue_channel = img_array[:, :, 2]

            # Red pin detection: high red, low green, low blue
            red_mask = (red_channel > 180) & (green_channel < 100) & (blue_channel < 100)

            # Orange pin detection: high red, medium green, low blue
            orange_mask = (red_channel > 200) & (green_channel > 50) & (green_channel < 150) & (blue_channel < 100)

            # Combine masks
            pin_mask = red_mask | orange_mask

            # Find pin location
            pin_coords = np.where(pin_mask)

            pin_x, pin_y = None, None
            if len(pin_coords[0]) > 0:
                # Get the centroid of the pin pixels
                pin_y = int(np.mean(pin_coords[0]))
                pin_x = int(np.mean(pin_coords[1]))
                print(f"Pin detected at: ({pin_x}, {pin_y})")

                # The pin points to a location slightly below its center
                # Adjust to point at the tip of the pin
                pin_y = pin_y + 20  # Pin tip is below the centroid

            if pin_x is None:
                # Fallback: assume pin is in the center-right area (after sidebar)
                # Sidebar is about 400px, map center is at (400 + (1920-400)/2) = 1160
                pin_x = 1160
                pin_y = 540
                print(f"Pin not detected, using fallback: ({pin_x}, {pin_y})")

            # Now zoom in on the pin location
            if progress_callback:
                progress_callback("Zoom sul punto...", 0.5)

            # Move mouse to pin and zoom
            page.mouse.move(pin_x, pin_y)
            time.sleep(0.5)

            # Zoom in with mouse wheel (zoom towards the pin)
            for _ in range(10):
                page.mouse.wheel(0, -400)
                time.sleep(0.4)

            time.sleep(3)

            # After zooming, the pin should be roughly at the same screen position
            # Take final screenshot
            if progress_callback:
                progress_callback("Cattura immagine finale...", 0.8)

            # Take screenshot and crop around the zoom center
            screenshot_bytes = page.screenshot()
            img_final = Image.open(io.BytesIO(screenshot_bytes))

            # Crop 700x700 centered on where we zoomed
            crop_size = 700
            left = max(0, pin_x - crop_size // 2)
            top = max(0, pin_y - crop_size // 2)
            right = min(img_final.width, left + crop_size)
            bottom = min(img_final.height, top + crop_size)

            # Adjust if we hit edges
            if right - left < crop_size:
                left = max(0, right - crop_size)
            if bottom - top < crop_size:
                top = max(0, bottom - crop_size)

            img_cropped = img_final.crop((left, top, left + crop_size, top + crop_size))

            # Save
            output_path.parent.mkdir(parents=True, exist_ok=True)
            img_cropped.save(str(output_path), "PNG")

            browser.close()

            if progress_callback:
                progress_callback("Fatto!", 1.0)

            return True, None

    except Exception as e:
        print(f"Error capturing screenshot: {e}")
        if progress_callback:
            progress_callback(f"Errore: {str(e)[:30]}", 0)
        return False, str(e)


# ============================================================================
# STEP 2: SOLAR PANEL DETECTION (YOLO)
# ============================================================================

def detect_solar_panels(
    image_path: Path,
    output_dir: Path,
    model_path: Optional[Path] = None,
    progress_callback: Optional[Callable[[str, float], None]] = None
) -> Dict[str, Any]:
    """
    Detect solar panels in image using YOLOv8.
    
    Args:
        image_path: Path to input image
        output_dir: Directory to save results
        model_path: Path to YOLO model (auto-downloads if None)
        progress_callback: Optional callback for progress updates
    
    Returns:
        Dictionary with detection statistics
    """
    if progress_callback:
        progress_callback("Caricamento modello YOLO...", 0.1)
    
    # Ensure model is available
    if model_path is None:
        model_path = ensure_yolo_model()
    
    if model_path is None or not model_path.exists():
        return {
            "error": "Modello YOLO non disponibile",
            "solar_panel_instances": 0,
            "coverage_percentage": 0.0
        }
    
    try:
        import cv2
        import numpy as np
        from ultralytics import YOLO
    except ImportError as e:
        return {
            "error": f"Dipendenze mancanti: {e}",
            "solar_panel_instances": 0,
            "coverage_percentage": 0.0
        }
    
    if progress_callback:
        progress_callback("Analisi immagine con YOLO...", 0.3)
    
    try:
        model = YOLO(str(model_path))
        
        # Run inference
        results = model.predict(source=str(image_path), conf=0.25, task='segment', verbose=False)
        
        res = results[0]
        img = cv2.imread(str(image_path))
        h, w = img.shape[:2]
        
        statistics = {
            'source': str(image_path),
            'total_area_pixels': h * w,
            'solar_panel_instances': 0,
            'solar_panel_area_pixels': 0,
            'coverage_percentage': 0.0,
            'detections': []
        }
        
        # Center of image for filtering
        cx, cy = w // 2, h // 2
        max_distance = min(w, h) * 0.4
        
        if progress_callback:
            progress_callback("Elaborazione rilevamenti...", 0.6)
        
        if hasattr(res, 'masks') and res.masks is not None:
            masks = res.masks.data
            confs = res.boxes.conf.cpu().numpy() if hasattr(res.boxes.conf, 'cpu') else res.boxes.conf.numpy()
            boxes = res.boxes.xyxy.cpu().numpy() if hasattr(res.boxes.xyxy, 'cpu') else res.boxes.xyxy.numpy()
            
            masks_np = masks.cpu().numpy() if hasattr(masks, 'cpu') else masks.numpy()
            
            total_solar_area = 0
            valid_count = 0
            
            for i, mask in enumerate(masks_np):
                mask_resized = cv2.resize(mask.astype(np.float32), (w, h))
                mask_binary = (mask_resized > 0.5).astype(np.uint8)
                
                # Filter detections too far from center
                if i < len(boxes):
                    x1, y1, x2, y2 = boxes[i]
                    det_cx = (x1 + x2) / 2
                    det_cy = (y1 + y2) / 2
                    
                    distance = ((det_cx - cx) ** 2 + (det_cy - cy) ** 2) ** 0.5
                    if distance > max_distance:
                        continue
                    
                    # Filter very elongated detections (likely text labels)
                    box_w = x2 - x1
                    box_h = y2 - y1
                    aspect_ratio = max(box_w, box_h) / (min(box_w, box_h) + 1)
                    if aspect_ratio > 5:
                        continue
                
                area = np.sum(mask_binary)
                confidence = float(confs[i]) if i < len(confs) else 0.0
                
                total_solar_area += area
                valid_count += 1
                
                # Color mask in blue/cyan
                img[mask_binary == 1] = [255, 165, 0]  # Blue in BGR
                
                statistics['detections'].append({
                    'instance': valid_count,
                    'area_pixels': int(area),
                    'confidence': round(confidence, 3)
                })
            
            statistics['solar_panel_instances'] = valid_count
            statistics['solar_panel_area_pixels'] = int(total_solar_area)
            statistics['coverage_percentage'] = round((total_solar_area / (h * w)) * 100, 2)
        
        if progress_callback:
            progress_callback("Salvataggio risultati...", 0.9)
        
        # Save annotated image
        output_dir.mkdir(parents=True, exist_ok=True)
        annotated_path = output_dir / "solar_annotated.png"
        cv2.imwrite(str(annotated_path), img)
        
        # Save JSON
        json_path = output_dir / "solar_detection.json"
        with open(json_path, 'w') as f:
            json.dump(statistics, f, indent=2)
        
        statistics['annotated_image_path'] = str(annotated_path)
        
        if progress_callback:
            progress_callback("Rilevamento completato!", 1.0)
        
        return statistics
        
    except Exception as e:
        return {
            "error": str(e),
            "solar_panel_instances": 0,
            "coverage_percentage": 0.0
        }


# ============================================================================
# STEP 3: LLM VISION ANALYSIS
# ============================================================================

def analyze_with_llm(
    image_path: Path,
    output_dir: Path,
    model: str = DEFAULT_LLM_MODEL,
    progress_callback: Optional[Callable[[str, float], None]] = None
) -> Dict[str, Any]:
    """
    Analyze image with LLM Vision via OpenRouter.
    
    Args:
        image_path: Path to image
        output_dir: Directory to save results
        model: OpenRouter model ID
        progress_callback: Optional callback for progress updates
    
    Returns:
        Dictionary with analysis results
    """
    try:
        import httpx
    except ImportError:
        return {"error": "httpx non installato"}
    
    if progress_callback:
        progress_callback("Preparazione richiesta LLM...", 0.1)
    
    api_key = get_api_key()
    if not api_key:
        return {"error": "OPENROUTER_API_KEY non trovata"}
    
    # Encode image
    if progress_callback:
        progress_callback("Codifica immagine...", 0.2)
    
    with open(image_path, "rb") as f:
        image_b64 = base64.b64encode(f.read()).decode("utf-8")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/helios-vision",
        "X-Title": "Helios Vision Analysis"
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
    
    if progress_callback:
        progress_callback(f"Invio a {model.split('/')[-1]}...", 0.4)
    
    try:
        with httpx.Client(timeout=90.0) as client:
            response = client.post(OPENROUTER_API_URL, headers=headers, json=payload)
        
        if response.status_code != 200:
            return {"error": f"API error: {response.status_code}"}
        
        if progress_callback:
            progress_callback("Elaborazione risposta...", 0.8)
        
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        
        # Parse JSON from response
        try:
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            analysis = json.loads(content.strip())
        except json.JSONDecodeError:
            analysis = {"raw_response": content, "parse_error": True}
        
        # Add metadata
        analysis["_metadata"] = {
            "model": model,
            "tokens_used": result.get("usage", {}).get("total_tokens", 0)
        }
        
        # Save JSON
        output_dir.mkdir(parents=True, exist_ok=True)
        json_path = output_dir / "llm_analysis.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)
        
        if progress_callback:
            progress_callback("Analisi LLM completata!", 1.0)
        
        return analysis
        
    except Exception as e:
        return {"error": str(e)}


# ============================================================================
# MAIN PIPELINE
# ============================================================================

def run_analysis_pipeline(
    address: str,
    model: str = DEFAULT_LLM_MODEL,
    step_callback: Optional[Callable[[int, str, float], None]] = None
) -> Dict[str, Any]:
    """
    Run the complete analysis pipeline.
    
    Args:
        address: Address to analyze
        model: LLM model to use
        step_callback: Callback for step updates (step_number, message, progress)
            - step 1: Address search
            - step 2: Satellite capture
            - step 3: YOLO detection
            - step 4: LLM analysis
    
    Returns:
        Dictionary with complete analysis results
    """
    # Create output directory
    normalized = normalize_address(address)
    output_dir = RESULTS_DIR / normalized
    output_dir.mkdir(parents=True, exist_ok=True)
    
    screenshot_path = output_dir / "satellite_view.png"
    
    result = {
        "address": address,
        "timestamp": datetime.now().isoformat(),
        "output_dir": str(output_dir),
        "success": False,
        "steps": {
            "screenshot": {"completed": False},
            "solar_detection": {"completed": False},
            "llm_analysis": {"completed": False}
        }
    }
    
    # STEP 1: Capture satellite screenshot
    def step1_callback(msg, pct):
        if step_callback:
            step_callback(1, msg, pct)
    
    if step_callback:
        step_callback(1, "Avvio cattura satellitare...", 0)
    
    success, error_msg = capture_satellite_screenshot(address, screenshot_path, step1_callback)
    
    if not success or not screenshot_path.exists():
        result["error"] = error_msg if error_msg else "Impossibile catturare screenshot satellitare"
        return result
    
    result["steps"]["screenshot"] = {
        "completed": True,
        "path": str(screenshot_path)
    }
    result["screenshot_path"] = str(screenshot_path)
    
    # STEP 2: Solar panel detection
    def step2_callback(msg, pct):
        if step_callback:
            step_callback(2, msg, pct)
    
    if step_callback:
        step_callback(2, "Avvio rilevamento pannelli solari...", 0)
    
    solar_stats = detect_solar_panels(screenshot_path, output_dir, progress_callback=step2_callback)
    
    result["steps"]["solar_detection"] = {
        "completed": "error" not in solar_stats,
        "data": solar_stats
    }
    result["solar_detection"] = solar_stats
    
    # STEP 3: LLM Vision analysis
    def step3_callback(msg, pct):
        if step_callback:
            step_callback(3, msg, pct)
    
    if step_callback:
        step_callback(3, "Avvio analisi LLM Vision...", 0)
    
    llm_analysis = analyze_with_llm(screenshot_path, output_dir, model, step3_callback)
    
    result["steps"]["llm_analysis"] = {
        "completed": "error" not in llm_analysis,
        "data": llm_analysis
    }
    result["llm_analysis"] = llm_analysis
    
    # Final report
    result["success"] = all(
        step.get("completed", False) 
        for step in result["steps"].values()
    )
    
    # Save complete report
    report_path = output_dir / "analysis_report.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    result["report_path"] = str(report_path)
    
    if step_callback:
        step_callback(4, "Analisi completata!", 1.0)
    
    return result


# ============================================================================
# CLI
# ============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Helios Vision - Satellite Image Analysis")
    parser.add_argument("address", type=str, help="Address to analyze")
    parser.add_argument("--model", type=str, default=DEFAULT_LLM_MODEL, help="LLM model")
    
    args = parser.parse_args()
    
    def print_progress(step, msg, pct):
        step_names = {1: "Screenshot", 2: "YOLO", 3: "LLM", 4: "Done"}
        print(f"[Step {step} - {step_names.get(step, '?')}] {msg} ({pct*100:.0f}%)")
    
    result = run_analysis_pipeline(args.address, args.model, print_progress)
    
    print("\n" + "="*60)
    print("RISULTATI")
    print("="*60)
    
    if result.get("success"):
        print(f"✅ Analisi completata con successo!")
        print(f"📁 Output: {result['output_dir']}")
        
        if "llm_analysis" in result and "sintesi" in result["llm_analysis"]:
            print(f"\n📋 SINTESI: {result['llm_analysis']['sintesi']}")
        
        solar = result.get("solar_detection", {})
        print(f"\n🔆 Pannelli solari: {solar.get('solar_panel_instances', 0)}")
        print(f"   Copertura: {solar.get('coverage_percentage', 0)}%")
    else:
        print(f"❌ Errore: {result.get('error', 'Sconosciuto')}")
