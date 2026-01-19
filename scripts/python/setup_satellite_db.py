
import os
import sys
from dotenv import load_dotenv
from supabase import create_client, Client

# Add the parent directory to sys.path to allow imports if needed
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Error: SUPABASE_URL or SUPABASE_KEY not found in environment variables.")
    sys.exit(1)

def get_supabase_client() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def create_satellite_table(supabase: Client):
    print("⚙️  Creating 'client_satellite_images' table...")
    
    sql = """
    CREATE TABLE IF NOT EXISTS client_satellite_images (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        codice_cliente TEXT REFERENCES clienti(codice_cliente) ON DELETE CASCADE,
        image_url TEXT NOT NULL,
        vlm_analysis JSONB,
        created_at TIMESTAMPTZ DEFAULT NOW(),
        UNIQUE(codice_cliente)
    );
    """
    
    try:
        supabase.postgrest.rpc('exec_sql', {'sql': sql}).execute()
        print("✅ Table 'client_satellite_images' created/verified.")
    except Exception as e:
        print(f"❌ Failed to create table: {e}")
        # Fallback explanation
        print("   If 'exec_sql' RPC does not exist, you must create the table manually in Supabase SQL Editor:")
        print(sql)

def create_storage_bucket(supabase: Client):
    print("⚙️  Creating 'satellite-images' storage bucket...")
    bucket_name = "satellite-images"
    
    try:
        # Check if bucket exists
        buckets = supabase.storage.list_buckets()
        existing = [b.name for b in buckets]
        
        if bucket_name not in existing:
            supabase.storage.create_bucket(bucket_name, options={"public": True})
            print(f"✅ Bucket '{bucket_name}' created.")
        else:
            print(f"ℹ️  Bucket '{bucket_name}' already exists.")
            
    except Exception as e:
        print(f"❌ Failed to create storage bucket: {e}")

def main():
    print("=== Supabase Satellite Setup ===")
    supabase = get_supabase_client()
    
    create_satellite_table(supabase)
    create_storage_bucket(supabase)
    
    print("\nSetup complete.")

if __name__ == "__main__":
    main()
