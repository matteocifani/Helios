"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                    HELIOS GEOCODING SCRIPT                                    ║
║              Geocode addresses and update Supabase                            ║
╚═══════════════════════════════════════════════════════════════════════════════╝

This script geocodes addresses from the abitazioni table and updates 
latitudine/longitudine in Supabase.

Uses free Nominatim API (OpenStreetMap) - requires 1 second delay between requests.
"""

import os
import time
import pandas as pd
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from supabase import create_client
from dotenv import load_dotenv
from tqdm import tqdm

# Load environment
load_dotenv()

# Initialize Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Initialize geocoder with rate limiting (1 request per second for Nominatim)
geolocator = Nominatim(user_agent="helios_geocoder_vitasicura")
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1.1)


def get_abitazioni_without_coords(limit: int = None) -> pd.DataFrame:
    """Fetch abitazioni that need geocoding."""
    query = supabase.table("abitazioni").select(
        "id, indirizzo_completo, citta, provincia, paese"
    ).is_("latitudine", "null")
    
    if limit:
        query = query.limit(limit)
    
    response = query.execute()
    return pd.DataFrame(response.data)


def geocode_address(row: pd.Series) -> tuple:
    """
    Geocode a single address using multiple fallback strategies.
    
    Returns:
        tuple: (latitude, longitude) or (None, None) if failed
    """
    # Build full address for geocoding
    address_parts = []
    
    if row.get('indirizzo_completo'):
        address_parts.append(row['indirizzo_completo'])
    if row.get('citta'):
        address_parts.append(row['citta'])
    if row.get('provincia'):
        address_parts.append(row['provincia'])
    
    address_parts.append("Italia")
    
    full_address = ", ".join(address_parts)
    
    try:
        # Try full address first
        location = geocode(full_address)
        if location:
            return (location.latitude, location.longitude)
        
        # 2. Try city cleanup - Remove "Calabra" and other common suffixes if present
        if row.get('citta'):
            city_original = row['citta']
            
            # Strategy: Clean "Calabra"
            if "Calabra" in city_original:
                city_clean = city_original.replace("Calabra", "").strip()
                clean_address = f"{city_clean}, Italia"
                # print(f"DEBUG: Trying cleaned city: {clean_address}")
                location = geocode(clean_address)
                if location:
                    return (location.latitude, location.longitude)

            # Strategy: Clean other suffixes (generic approach, split by space and take first word if > 2 chars)
            # Useful for "Santi Lorenzo E Flaviano" -> "Santi Lorenzo"? No, maybe better to check known mappings in future.
            # But for things like "Collecalcioni", it might be a hamlet of a larger city (missing province is killer).
            
        # 3. Fallback: try just city + Italia (already tried originally, but let's keep it as last resort)
        if row.get('citta'):
            city_address = f"{row['citta']}, Italia"
            location = geocode(city_address)
            if location:
                return (location.latitude, location.longitude)
        
        return (None, None)
        
    except Exception as e:
        print(f"Error geocoding '{full_address}': {e}")
        return (None, None)


def update_coordinates(abitazione_id: int, lat: float, lon: float) -> bool:
    """Update coordinates in Supabase."""
    try:
        supabase.table("abitazioni").update({
            "latitudine": lat,
            "longitudine": lon
        }).eq("id", abitazione_id).execute()
        return True
    except Exception as e:
        print(f"Error updating id {abitazione_id}: {e}")
        return False


def main(batch_size: int = 1000):
    """
    Main geocoding function with auto-looping.
    
    Args:
        batch_size: Number of records to process per batch (max 1000 usually)
    """
    print("🌍 HELIOS Geocoding Script - Auto Loop Mode")
    print("=" * 50)
    
    total_processed = 0
    total_success = 0
    total_fail = 0
    
    while True:
        # Get records needing geocoding
        # If batch_size is provided (not None/0), use it. If 0/None passed, use default valid int.
        # But here we want to loop.
        current_limit = batch_size if batch_size and batch_size > 0 else 1000
        
        print(f"\n🔄 Fetching next batch (limit: {current_limit})...")
        df = get_abitazioni_without_coords(limit=current_limit)
        
        count = len(df)
        print(f"📊 Found {count} records to geocode in this batch")
        
        if df.empty:
            print("✅ All records have been processed!")
            break
        
        # Process records
        batch_success = 0
        batch_fail = 0
        
        for idx, row in tqdm(df.iterrows(), total=len(df), desc=f"Geocoding Batch"):
            lat, lon = geocode_address(row)
            
            if lat and lon:
                if update_coordinates(row['id'], lat, lon):
                    batch_success += 1
                else:
                    batch_fail += 1
            else:
                batch_fail += 1
                
        total_processed += count
        total_success += batch_success
        total_fail += batch_fail
        
        print(f"   Batch result: {batch_success} OK, {batch_fail} Failed")
        
        # Check if we should stop (if we processed fewer than requested, we are done)
        if count < current_limit:
            print("✅ No more records to fetch.")
            break

    # Final Summary
    print("\n" + "=" * 50)
    print("🏁 GEOCODING COMPLETE")
    print(f"📊 Total processed: {total_processed}")
    print(f"✅ Total success: {total_success}")
    print(f"❌ Total failed: {total_fail}")
    if total_processed > 0:
        print(f"📈 Overall success rate: {total_success/total_processed*100:.1f}%")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Geocode abitazioni addresses")
    parser.add_argument(
        "--batch", "-b",
        type=int,
        default=100,
        help="Number of records to process (default: 100, use 0 for all)"
    )
    
    args = parser.parse_args()
    batch_size = args.batch if args.batch > 0 else None
    
    main(batch_size=batch_size)
