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
        
        # Fallback: try just city + Italia
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


def main(batch_size: int = 100):
    """
    Main geocoding function.
    
    Args:
        batch_size: Number of records to process (use None for all)
    """
    print("🌍 HELIOS Geocoding Script")
    print("=" * 50)
    
    # Get records needing geocoding
    df = get_abitazioni_without_coords(limit=batch_size)
    print(f"📊 Found {len(df)} records to geocode")
    
    if df.empty:
        print("✅ All records already have coordinates!")
        return
    
    # Process records
    success_count = 0
    fail_count = 0
    
    for idx, row in tqdm(df.iterrows(), total=len(df), desc="Geocoding"):
        lat, lon = geocode_address(row)
        
        if lat and lon:
            if update_coordinates(row['id'], lat, lon):
                success_count += 1
            else:
                fail_count += 1
        else:
            fail_count += 1
    
    # Summary
    print("\n" + "=" * 50)
    print(f"✅ Successfully geocoded: {success_count}")
    print(f"❌ Failed: {fail_count}")
    print(f"📊 Success rate: {success_count/(success_count+fail_count)*100:.1f}%")


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
