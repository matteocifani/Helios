
import os
import sys
from dotenv import load_dotenv
from supabase import create_client

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

if not url or not key:
    print("Error: Missing Supabase credentials")
    sys.exit(1)

client = create_client(url, key)

try:
    # Fetch 5 records with non-null hydro risk
    response = client.table("abitazioni")\
        .select("id, hydro_risk_p3, flood_risk_p3")\
        .not_.is_("hydro_risk_p3", "null")\
        .limit(5)\
        .execute()
    
    print("--- Sample Data ---")
    for row in response.data:
        print(f"ID: {row['id']}")
        print(f"Hydro Risk P3: {row.get('hydro_risk_p3')} (Type: {type(row.get('hydro_risk_p3'))})")
        print(f"Flood Risk P3: {row.get('flood_risk_p3')} (Type: {type(row.get('flood_risk_p3'))})")
        print("-" * 20)
        
except Exception as e:
    print(f"Error: {e}")
