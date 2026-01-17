import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

try:
    # Fetch all IDs to count locally if head=True is flaky
    print("Fetching total count...")
    # Using count='exact' without head=True sometimes works better or just fetching a col
    response_total = supabase.table('abitazioni').select('id', count='exact').execute()
    total = response_total.count
    
    print("Fetching geocoded count...")
    response_geo = supabase.table('abitazioni').select('id', count='exact').not_.is_('latitudine', 'null').execute()
    geocoded = response_geo.count
    
    print("-" * 30)
    print(f"Total Records: {total}")
    print(f"Geocoded:      {geocoded}")
    print(f"Pending:       {total - geocoded}")
    print("-" * 30)

except Exception as e:
    print(f"Error: {e}")
