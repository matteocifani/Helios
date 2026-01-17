from playwright.sync_api import sync_playwright
import time
import sys
import random
import os

# Directory dello script per salvare gli screenshot
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def random_delay(min_sec=2, max_sec=5):
    """Delay casuale per sembrare più umano"""
    delay = random.uniform(min_sec, max_sec)
    time.sleep(delay)

def scrape_house_satellite(address):
    """
    Accedi a Google Maps, cerca un indirizzo (casa), passa a visualizzazione satellite
    e zoomma sulla casa.
    
    Args:
        address (str): L'indirizzo della casa da cercare (es: "Via Roma 123, Milano")
    """
    
    with sync_playwright() as p:
        # Opzioni di browser anti-blocco
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
        
        # Context con viewport e user agent custom
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 2560, "height": 1440},
            timezone_id="Europe/Rome",
            locale="it-IT",
        )
        
        page = context.new_page()
        
        print("[1] Apertura di Google Maps...")
        page.goto("https://www.google.com/maps", wait_until="networkidle")
        print("   Attendendo il caricamento completo...")
        random_delay(5, 8)
        
        # ===== GESTIONE COOKIE CONSENT =====
        print("[1.5] Gestione banner cookie...")
        try:
            # Prova diversi selettori per il pulsante "Accetta tutto" / "Accept all"
            cookie_selectors = [
                'button:has-text("Accetta tutto")',
                'button:has-text("Accept all")',
                'button[aria-label*="Accetta"]',
                'button[aria-label*="Accept"]',
                'form:has-text("Accetta tutto") button',
                '[aria-label="Accetta tutto"]',
                'div[role="dialog"] button:first-of-type',
            ]
            
            cookie_accepted = False
            for selector in cookie_selectors:
                try:
                    cookie_btn = page.locator(selector).first
                    if cookie_btn.is_visible(timeout=3000):
                        cookie_btn.click()
                        print(f"   ✓ Cookie accettati con: {selector}")
                        cookie_accepted = True
                        random_delay(4, 6)
                        break
                except:
                    continue
            
            if not cookie_accepted:
                print("   Nessun banner cookie trovato o già accettato")
        except Exception as e:
            print(f"   Nota: Errore gestione cookie: {e}")
        
        random_delay(3, 5)
        
        # ===== RICERCA INDIRIZZO =====
        print(f"[2] Ricerca dell'indirizzo: {address}")
        import urllib.parse
        encoded_address = urllib.parse.quote(address)
        
        # Naviga all'URL di ricerca
        search_url = f"https://www.google.com/maps/search/{encoded_address}"
        
        print(f"   Navigazione a: {search_url}")
        page.goto(search_url, wait_until="domcontentloaded")
        print("   Attendendo il caricamento della mappa...")
        random_delay(10, 14)
        
        # Attendi che la pagina si stabilizzi
        try:
            page.wait_for_load_state("networkidle", timeout=20000)
        except:
            print("   Timeout durante il caricamento, continuiamo...")
        
        random_delay(3, 5)
        
        # ===== CLICCA SUL RISULTATO PER CENTRARE LA MAPPA SULLA CASA =====
        print("[2.5] Centro la mappa sulla casa...")
        try:
            # Clicca sul primo risultato della ricerca (la scheda a sinistra)
            result_selectors = [
                'div[role="article"]',  # Card del risultato
                'a[data-value="Indicazioni"]',  # Link indicazioni
                'div.Nv2PK',  # Card risultato
                'div[class*="result"]',
                'h1.DUwDvf',  # Nome del posto
            ]
            
            result_clicked = False
            for selector in result_selectors:
                try:
                    result = page.locator(selector).first
                    if result.is_visible(timeout=3000):
                        result.click()
                        print(f"   ✓ Cliccato sul risultato: {selector}")
                        result_clicked = True
                        random_delay(4, 6)
                        break
                except:
                    continue
            
            if not result_clicked:
                print("   Provo a cliccare direttamente sul marker...")
                # Clicca al centro della mappa dove dovrebbe esserci il marker
                page.mouse.click(960, 400)
                random_delay(3, 5)
                
        except Exception as e:
            print(f"   Nota: {e}")
        
        # Attendi che la mappa si centri
        random_delay(4, 6)
        
        # ===== PASSAGGIO A SATELLITE (FONDAMENTALE PER VEDERE IL TETTO) =====
        print("[3] Passaggio a visualizzazione satellite...")
        satellite_activated = False
        
        # METODO 1: Modifica URL per forzare vista satellite
        # Il parametro !3m1!1e3 forza la vista satellite in Google Maps
        try:
            current_url = page.url
            print(f"   URL attuale: {current_url[:80]}...")
            
            # Se l'URL contiene coordinate, aggiungi il parametro satellite
            if "@" in current_url:
                # Aggiungi /data=!3m1!1e3 per satellite
                if "/data=" in current_url:
                    # Modifica il data esistente
                    satellite_url = current_url.split("/data=")[0] + "/data=!3m1!1e3"
                else:
                    # Aggiungi data satellite
                    satellite_url = current_url + "/data=!3m1!1e3"
                
                print(f"   Navigazione a URL satellite...")
                page.goto(satellite_url, wait_until="domcontentloaded")
                random_delay(8, 12)
                satellite_activated = True
                print("   ✓ Vista satellite attivata via URL")
        except Exception as e:
            print(f"   Errore metodo URL: {e}")
        
        random_delay(3, 5)
        
        # METODO 2: Se URL non ha funzionato, prova click sul pulsante Livelli
        if not satellite_activated:
            print("   Provo metodo click su Livelli...")
            try:
                # Hover sulla minimappa per far apparire il menu
                page.mouse.move(80, 950)
                random_delay(1, 2)
                
                # Cerca il pulsante Livelli che appare
                layers_selectors = [
                    'button[aria-label="Livelli"]',
                    'button[aria-label="Layers"]',
                    'button[aria-label="Mostra le opzioni mappa"]',
                    'button[aria-label="Show map options"]',
                    '[aria-label*="Livelli"]',
                    '[aria-label*="Layers"]',
                ]
                
                for selector in layers_selectors:
                    try:
                        btn = page.locator(selector).first
                        if btn.is_visible(timeout=2000):
                            btn.click()
                            print(f"   ✓ Aperto menu Livelli: {selector}")
                            random_delay(2, 3)
                            
                            # Ora cerca e clicca su "Satellite"
                            sat_options = [
                                'button[aria-label="Satellite"]',
                                '[aria-label="Satellite"]',
                                'text=Satellite',
                            ]
                            for sat_sel in sat_options:
                                try:
                                    sat_btn = page.locator(sat_sel).first
                                    if sat_btn.is_visible(timeout=2000):
                                        sat_btn.click()
                                        print("   ✓ Satellite attivato!")
                                        satellite_activated = True
                                        random_delay(4, 6)
                                        break
                                except:
                                    continue
                            break
                    except:
                        continue
            except Exception as e:
                print(f"   Errore metodo click: {e}")
        
        # METODO 3: Ultimo tentativo - JavaScript per cambiare layer
        if not satellite_activated:
            print("   Ultimo tentativo con shortcut/JS...")
            try:
                # Prova shortcut da tastiera (alcuni sistemi supportano)
                page.keyboard.press("Control+Shift+G")
                random_delay(2, 3)
            except:
                pass
        
        random_delay(3, 4)
        
        # Verifica che siamo ancora sulla pagina giusta
        print(f"   URL finale: {page.url[:80]}...")
        
        print("[4] Zoommo sulla casa...")
        
        # IMPORTANTE: Prima di zoomare, dobbiamo centrare la vista sulla casa
        # Cerchiamo le coordinate dall'URL e usiamo quelle
        current_url = page.url
        
        # Estrai le coordinate dall'URL se presenti (formato: @lat,lng,zoom)
        import re
        coords_match = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', current_url)
        
        if coords_match:
            lat = coords_match.group(1)
            lng = coords_match.group(2)
            print(f"   Coordinate trovate: {lat}, {lng}")
            
            # Naviga direttamente alle coordinate con zoom massimo (22z)
            # Il formato !3m1!1e3 è per satellite
            zoom_url = f"https://www.google.com/maps/@{lat},{lng},22z/data=!3m1!1e3"
            print(f"   Navigazione a coordinate con zoom massimo...")
            page.goto(zoom_url, wait_until="domcontentloaded")
            random_delay(8, 12)
            print("   ✓ Zoom diretto sulla posizione")
            
        else:
            print("   Coordinate non trovate nell'URL, uso zoom manuale...")
            # Clicca al centro della mappa dove dovrebbe esserci la casa
            page.mouse.click(960, 450)
            random_delay(2, 3)
            
            # Usa wheel per zoomare
            for i in range(24):
                page.mouse.wheel(0, -300)
                print(f"   Zoom {i+1}/24...")
                random_delay(0.8, 1.5)
        
        random_delay(5, 8)
        
        print("[5] Attesa caricamento tile satellitari ad alto zoom...")
        # Aspetta che i tile siano caricati PRIMA di screenshottare
        
        # Attesa per i tile - questo è fondamentale
        print("   Attesa caricamento tile (15 secondi)...")
        time.sleep(15)
        
        # RIMUOVI LE ETICHETTE dalla mappa per evitare falsi positivi nel detector
        print("   Rimozione etichette dalla mappa...")
        try:
            page.evaluate("""
                // Nasconde tutte le etichette testuali sulla mappa
                const labels = document.querySelectorAll('[data-label], [class*="label"], [class*="Label"]');
                labels.forEach(el => el.style.display = 'none');
                
                // Nasconde i marker e le icone
                const markers = document.querySelectorAll('[class*="marker"], [class*="Marker"], [class*="poi"]');
                markers.forEach(el => el.style.display = 'none');
                
                // Nasconde gli elementi SVG che contengono testo
                const svgTexts = document.querySelectorAll('svg text, svg tspan');
                svgTexts.forEach(el => el.style.display = 'none');
                
                // Nasconde i div con nomi delle strade
                const roadLabels = document.querySelectorAll('[class*="road"], [class*="street"], [class*="via"]');
                roadLabels.forEach(el => {
                    if (el.innerText && el.innerText.length < 50) {
                        el.style.display = 'none';
                    }
                });
            """)
            print("   ✓ Etichette nascoste")
        except Exception as e:
            print(f"   Nota: impossibile nascondere etichette: {e}")
        
        # Breve pausa per applicare le modifiche
        time.sleep(2)
        
        # Stabilizzazione rete
        try:
            print("   Attesa stabilizzazione rete...")
            page.wait_for_load_state("networkidle", timeout=10000)
        except:
            print("   Timeout rete, continuo...")
        
        # Breve pausa finale
        time.sleep(3)
        
        print("[6] Screenshot della casa in modalità satellite...")
        # Usa path assoluto per lo screenshot
        screenshot_path = os.path.join(SCRIPT_DIR, "satellite_view.png")
        try:
            # Pre-screenshot: accertati che il viewport non sia stato modificato
            page.evaluate("window.scrollTo(0, 0);")  # Scroll top
            random_delay(1, 2)
            
            # SOLUZIONE CHIAVE: Cattura SOLO la parte centrale dello schermo
            # Questo isola la singola casa escludendo le case vicine
            # Viewport è 2560x1440, prendiamo un quadrato centrale di 1000x1000 pixel
            # centrato sulla posizione della casa (alta risoluzione)
            
            viewport_width = 2560
            viewport_height = 1440
            crop_size = 1000  # Dimensione del crop (quadrato) - alta risoluzione
            
            # Calcola le coordinate del crop PERFETTAMENTE centrato
            crop_x = (viewport_width - crop_size) // 2   # 780
            crop_y = (viewport_height - crop_size) // 2  # 220 - perfettamente centrato
            
            print(f"   Catturando area centrale {crop_size}x{crop_size} pixel (alta risoluzione)...")
            
            page.screenshot(
                path=screenshot_path, 
                full_page=False,
                clip={
                    "x": crop_x,
                    "y": crop_y,
                    "width": crop_size,
                    "height": crop_size
                }
            )
            print(f"   ✓ Screenshot salvato: {screenshot_path}")
            print(f"   ✓ Area catturata: {crop_size}x{crop_size}px (solo la casa)")
            print(f"   ✓ Lo screenshot è già isolato - nessun ritaglio aggiuntivo necessario")
        except Exception as e:
            print(f"   Errore screenshot con clip: {e}")
            print("   Provo screenshot completo...")
            try:
                page.screenshot(path=screenshot_path, full_page=False)
                print(f"   ✓ Screenshot salvato (completo): {screenshot_path}")
            except Exception as e2:
                print(f"   Errore screenshot: {e2}")
                # Prova un path alternativo
                alt_path = "/tmp/satellite_view.png"
                page.screenshot(path=alt_path)
                print(f"   ✓ Screenshot salvato (alternativo): {alt_path}")
        
        print("[7] Operazione completata! La finestra rimarrà aperta 30 secondi.")
        print("    Puoi interagire con la mappa manualmente se necessario.")
        
        # Mantieni la finestra aperta per 30 secondi
        time.sleep(30)
        
        browser.close()
        print("[8] Browser chiuso.")

if __name__ == "__main__":
    # Indirizzo di default o da riga di comando
    if len(sys.argv) > 1:
        address = " ".join(sys.argv[1:])
    else:
        # Chiedi l'indirizzo all'utente
        address = input("Inserisci l'indirizzo della casa (es: Via Roma 123, Milano): ").strip()
    
    if not address:
        print("Errore: Devi inserire un indirizzo!")
        sys.exit(1)
    
    scrape_house_satellite(address)
