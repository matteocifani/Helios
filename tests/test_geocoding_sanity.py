from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import pandas as pd

# Initialize geocoder exactly as in the main script
geolocator = Nominatim(user_agent="helios_geocoder_vitasicura")
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1.1)

def test_address(name, address_parts):
    print(f"\nTesting: {name}")
    full_address = ", ".join(address_parts)
    print(f"Address: {full_address}")
    
    try:
        location = geocode(full_address)
        if location:
            print(f"✅ Success: {location.address}")
            print(f"   Coords: {location.latitude}, {location.longitude}")
        else:
            print("❌ Failed (Location not found)")
            
    except Exception as e:
        print(f"❌ Error: {e}")

# Test Cases
test_cases = [
    ("Valid Address (Rome)", ["Piazza del Colosseo", "Roma", "Lazio", "Italia"]),
    ("Valid Address (Milan)", ["Piazza del Duomo", "Milano", "Lombardia", "Italia"]),
    ("Problematic Record 1", ["Via Matteotti, 88", "Calimera Calabra", "Italia"]),
    ("Problematic Record 2", ["Piazza Duomo, 144", "Collecalcioni", "Italia"]),
]

print("🔍 Geocoding Sanity Check")
print("=========================")

for name, parts in test_cases:
    test_address(name, parts)
