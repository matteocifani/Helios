import os
import pytest
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

# Disable by default because it requires external network access
RUN_GEOCODING_TESTS = os.getenv("RUN_GEOCODING_TESTS") == "1"

# Initialize geocoder exactly as in the main script
geolocator = Nominatim(user_agent="helios_geocoder_vitasicura")
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1.1)

# Test cases taken from production data anomalies
test_cases = [
    ("Valid Address (Rome)", ["Piazza del Colosseo", "Roma", "Lazio", "Italia"]),
    ("Valid Address (Milan)", ["Piazza del Duomo", "Milano", "Lombardia", "Italia"]),
    ("Problematic Record 1", ["Via Matteotti, 88", "Calimera Calabra", "Italia"]),
    ("Problematic Record 2", ["Piazza Duomo, 144", "Collecalcioni", "Italia"]),
]


@pytest.mark.skipif(
    not RUN_GEOCODING_TESTS,
    reason="Geocoding sanity check requires external network; enable with RUN_GEOCODING_TESTS=1",
)
@pytest.mark.parametrize("name,address_parts", test_cases)
def test_geocoding_lookup(name, address_parts):
    full_address = ", ".join(address_parts)
    location = geocode(full_address)

    # We only assert that the geocoder returns something; failures give actionable context
    assert location is not None, f"Geocoding failed for {name}: {full_address}"
