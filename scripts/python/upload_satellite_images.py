
import os
import sys
import random
import time
import json
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client

# Add the parent directory to sys.path to allow imports
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

from src.utils.vision_analysis import analyze_image

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
IMAGES_DIR = "/Users/matteocifani/Downloads/Immagini "

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Error: SUPABASE_URL or SUPABASE_KEY not found.")
    sys.exit(1)

def get_supabase_client() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def upload_and_analyze():
    supabase = get_supabase_client()
    
    # 1. Get images
    if not os.path.exists(IMAGES_DIR):
        print(f"❌ Error: Images directory not found: {IMAGES_DIR}")
        sys.exit(1)
        
    images = [f for f in os.listdir(IMAGES_DIR) if f.casefold().endswith(('.png', '.jpg', '.jpeg'))]
    if not images:
        print("❌ No images found in directory.")
        sys.exit(1)
        
    print(f"📸 Found {len(images)} images.")
    
    # 2. Get clients (Fetching from nbo_master.json to match UI)
    print("👥 Fetching clients from nbo_master.json...")
    try:
        nbo_path = os.path.join(os.path.dirname(__file__), '../../Data/nbo_master.json')
        with open(nbo_path, 'r') as f:
            nbo_data = json.load(f)
            
        # Calculate Score for each client to match UI sorting
        # Formula: retention * 0.3 + redditivita * 0.4 + propensione * 0.3
        # Weights default: {'retention': 0.3, 'redditivita': 0.4, 'propensione': 0.3}
        
        clients_with_score = []
        for c in nbo_data:
            cid = c.get('codice_cliente')
            recs = c.get('raccomandazioni', [])
            
            # Find max score for this client (as UI likely picks the best rec)
            max_score = 0
            for r in recs:
                 comp = r.get('componenti', {})
                 # Scores in JSON are usually 0-100
                 s = (comp.get('retention_gain', 0) * 0.3 + 
                      comp.get('redditivita', 0) * 0.4 + 
                      comp.get('propensione', 0) * 0.3)
                 if s > max_score:
                     max_score = s
            
            if cid:
                clients_with_score.append((max_score, cid))
                
        # Sort desc by Score
        clients_with_score.sort(key=lambda x: x[0], reverse=True)
        
        # Take Top 80 (to cover Top 5 + Top 25 Leaderboard safely)
        clients = [c[1] for c in clients_with_score[:80]]
        
        if not clients:
            print("❌ No clients found in nbo_master.json.")
            sys.exit(1)
            
        print(f"✅ Found {len(clients)} target clients (Top Score) from UI data.")
            
    except Exception as e:
        print(f"❌ Error fetching clients: {e}")
        # Fallback to DB
        print("⚠️ Fallback to DB fetch...")
        response = supabase.table("clienti").select("codice_cliente").limit(100).execute()
        clients = [c['codice_cliente'] for c in response.data]
    
    # Do NOT shuffle as we want the Top ones
    # random.shuffle(clients) 
    
    # Map images to clients (one image per client for now)
    assignments = []
    
    print(f"🔄 Assigning images to {len(clients)} clients...")
    
    for i, client_id in enumerate(clients):
        # Cycle through images if not enough
        image_file = images[i % len(images)]
        assignments.append((client_id, image_file))

    # 3. Process each assignment
    success_count = 0
    
    for client_id, image_name in assignments:
        image_path = os.path.join(IMAGES_DIR, image_name)
        print(f"\nPROCESSING Client {client_id} with Image {image_name}...")
        
        # A. Upload to Storage
        storage_path = f"{client_id}/{image_name}"
        public_url = ""
        
        try:
            with open(image_path, 'rb') as f:
                file_content = f.read()
            
            # Simple upsert
            supabase.storage.from_("satellite-images").upload(
                path=storage_path,
                file=file_content,
                file_options={"content-type": "image/png", "upsert": "true"}
            )
            
            # Get Public URL
            public_url = supabase.storage.from_("satellite-images").get_public_url(storage_path)
            print(f"   ✅ Uploaded: {public_url}")
            
        except Exception as e:
            print(f"   ❌ Upload failed: {e}")
            continue

        # B. Run VLM Analysis
        print("   🧠 Running VLM Analysis...")
        analysis = analyze_image(image_path)
        
        if "error" in analysis:
            print(f"   ⚠️ VLM Analysis failed: {analysis['error']}")
            # We continue even if analysis fails, just storing the image is valuable
            analysis = {"error": analysis["error"]}
        else:
            print("   ✅ Analysis complete.")

        # C. Insert/Update DB Record
        record = {
            "codice_cliente": client_id,
            "image_url": public_url,
            "vlm_analysis": analysis
        }
        
        try:
            # Upsert into table (we have UNIQUE on codice_cliente)
            supabase.table("client_satellite_images").upsert(record, on_conflict="codice_cliente").execute()
            print("   ✅ DB Record saved.")
            success_count += 1
        except Exception as e:
            print(f"   ❌ DB Insert failed: {e}")

    print(f"\n\n=== COMPLETE: Successfully processed {success_count}/{num_assignments} assignments. ===")

if __name__ == "__main__":
    upload_and_analyze()
