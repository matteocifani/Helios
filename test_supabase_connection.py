import os
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()

def test_connection():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

    print(f"URL: {url}")
    # Don't print the full key for security, just the first few chars
    print(f"KEY: {key[:5]}..." if key else "KEY: None")

    if not url or not key:
        print("❌ Missing Supabase credentials in .env")
        return

    try:
        supabase = create_client(url, key)
        print("✅ Client initialized")

        # Test 1: Fetch Clienti
        print("\n--- Testing 'clienti' table ---")
        response = supabase.table("clienti").select("*").limit(5).execute()
        print(f"Status: Success, Found {len(response.data)} records")
        if response.data:
            print(f"Sample data: {response.data[0]}")

        # Test 2: Fetch Polizze
        print("\n--- Testing 'polizze' table ---")
        response = supabase.table("polizze").select("*").limit(5).execute()
        print(f"Status: Success, Found {len(response.data)} records")
        
        # Test 3: Fetch Abitazioni
        print("\n--- Testing 'abitazioni' table ---")
        response = supabase.table("abitazioni").select("*").limit(5).execute()
        print(f"Status: Success, Found {len(response.data)} records")

    except Exception as e:
        print(f"\n❌ Connection failed: {e}")

if __name__ == "__main__":
    test_connection()
