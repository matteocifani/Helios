import osmnx as ox
import pandas as pd
import random
from datetime import datetime
from tqdm import tqdm
import time
import geopandas as gpd
from shapely.geometry import Point
import matplotlib.pyplot as plt

# Cache for street names and buildings by region
street_names_cache = {}
buildings_cache = {}

def get_street_names_for_region(region_name, major_city):
    """Extract real street names from major city"""
    if region_name in street_names_cache:
        tqdm.write(f"   💾 Using cached street names for {region_name}")
        return street_names_cache[region_name]

    tqdm.write(f"   🔍 Extracting street names from {major_city}...")

    try:
        # Get streets from the major city (much faster than entire region)
        streets = ox.features_from_place(
            major_city,
            tags={'highway': ['primary', 'secondary', 'tertiary', 'residential']},
        )

        tqdm.write(f"   ✓ Downloaded {len(streets)} street segments from {major_city}")

        # Extract street names
        street_list = []
        if 'name' in streets.columns:
            street_list = streets['name'].dropna().unique().tolist()
            tqdm.write(f"   ✓ Found {len(street_list)} unique street names")
            # Keep only valid Italian street names
            street_list = [s for s in street_list if isinstance(s, str) and len(s) < 50][:200]
            tqdm.write(f"   ✓ Filtered to {len(street_list)} valid street names")

        # If we got some streets, cache them
        if street_list:
            street_names_cache[region_name] = street_list
            return street_list
        else:
            tqdm.write(f"   ⚠️  No valid street names found for {region_name}")
    except Exception as e:
        tqdm.write(f"   ✗ Errore estrazione vie per {region_name}: {type(e).__name__}: {e}")

    # Fallback to generic Italian street names if API fails
    fallback = [
        "Via Roma", "Via Garibaldi", "Via Mazzini", "Via Dante", "Via Verdi",
        "Via Cavour", "Via Marconi", "Via Kennedy", "Corso Italia", "Corso Vittorio Emanuele",
        "Via Nazionale", "Via XX Settembre", "Piazza Duomo", "Via Matteotti", "Via Gramsci",
        "Via Leopardi", "Via Pascoli", "Via Manzoni", "Corso Umberto", "Via Bellini",
        "Via Vittorio Veneto", "Via Colombo", "Via Galilei", "Piazza Garibaldi", "Via Trieste"
    ]
    street_names_cache[region_name] = fallback
    return fallback


def get_buildings_for_region(region_name, gdf, target_points):
    """Extract actual buildings from the region polygon"""
    if region_name in buildings_cache:
        tqdm.write(f"   💾 Using cached building data for {region_name}")
        return buildings_cache[region_name]

    try:
        tqdm.write(f"   🏗️  Downloading building data for {region_name}...")
        tqdm.write(f"   ⏳ This may take a while for large regions...")

        # Get buildings from the region polygon
        buildings = ox.features_from_polygon(
            gdf.geometry.iloc[0],
            tags={'building': True}
        )

        tqdm.write(f"   ✓ Download complete!")

        if len(buildings) > 0:
            tqdm.write(f"   ✓ Found {len(buildings):,} buildings in {region_name}")

            # Sample buildings if we have too many
            if len(buildings) > target_points * 2:
                original_count = len(buildings)
                buildings = buildings.sample(n=min(target_points * 2, len(buildings)))
                tqdm.write(f"   📊 Sampled down from {original_count:,} to {len(buildings):,} buildings")
            else:
                tqdm.write(f"   📊 Using all {len(buildings):,} buildings (no sampling needed)")

            # Cache the buildings
            buildings_cache[region_name] = buildings
            tqdm.write(f"   💾 Cached building data for future use")
            return buildings
        else:
            tqdm.write(f"   ⚠️  No buildings found for {region_name}")
            return None

    except Exception as e:
        tqdm.write(f"   ✗ Error downloading buildings for {region_name}: {type(e).__name__}: {e}")
        return None


# Map regions to their major cities for street name extraction
major_cities = {
    'Abruzzo': 'L\'Aquila, Italy',
    'Basilicata': 'Potenza, Italy',
    'Calabria': 'Reggio Calabria, Italy',
    'Campania': 'Napoli, Italy',
    'Emilia-Romagna': 'Bologna, Italy',
    'Friuli-Venezia Giulia': 'Trieste, Italy',
    'Lazio': 'Roma, Italy',
    'Liguria': 'Genova, Italy',
    'Lombardy': 'Milano, Italy',
    'Marche': 'Ancona, Italy',
    'Molise': 'Campobasso, Italy',
    'Piedmont': 'Torino, Italy',
    'Apulia': 'Bari, Italy',
    'Sardinia': 'Cagliari, Italy',
    'Sicily': 'Palermo, Italy',
    'Tuscany': 'Firenze, Italy',
    'Trentino-Alto Adige': 'Trento, Italy',
    'Umbria': 'Perugia, Italy',
    'Aosta Valley': 'Aosta, Italy',
    'Veneto': 'Venezia, Italy'
}

# List of all 20 Italian regions with approximate weights based on size/population
regions_with_weights = [
    ("Abruzzo, Italy", 0.045),
    ("Basilicata, Italy", 0.025),
    ("Calabria, Italy", 0.050),
    ("Campania, Italy", 0.080),
    ("Emilia-Romagna, Italy", 0.070),
    ("Friuli-Venezia Giulia, Italy", 0.035),
    ("Lazio, Italy", 0.070),
    ("Liguria, Italy", 0.030),
    ("Lombardy, Italy", 0.120),
    ("Marche, Italy", 0.045),
    ("Molise, Italy", 0.015),
    ("Piedmont, Italy", 0.090),
    ("Apulia, Italy", 0.065),
    ("Sardinia, Italy", 0.050),
    ("Sicily, Italy", 0.085),
    ("Tuscany, Italy", 0.065),
    ("Trentino-Alto Adige, Italy", 0.040),
    ("Umbria, Italy", 0.030),
    ("Aosta Valley, Italy", 0.010),
    ("Veneto, Italy", 0.080)
]

target_total = 10000
all_points = []

# Calculate points per region based on weights
region_targets = {}
for region, weight in regions_with_weights:
    region_targets[region] = int(target_total * weight)

# Statistics tracking
stats = {
    'total_regions': len(regions_with_weights),
    'processed_regions': 0,
    'failed_regions': [],
    'total_points': 0,
    'total_buildings_found': 0,
    'start_time': datetime.now()
}

print("=" * 80)
print(f"🇮🇹 GENERATORE COORDINATE EDIFICI ITALIANI (VERSIONE BUILDINGS)")
print("=" * 80)
print(f"Target totale: {target_total:,} edifici")
print(f"Regioni da processare: {len(regions_with_weights)}")
print(f"Metodo: Estrazione edifici reali da OpenStreetMap")
print(f"Inizio: {stats['start_time'].strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)
print()

# Progress bar for regions
for idx, (region, weight) in enumerate(tqdm(regions_with_weights, desc="🏗️  Processando regioni", unit="regione")):
    region_name = region.replace(", Italy", "")
    region_start = time.time()
    target_points = region_targets[region]

    try:
        # Fetch region boundary
        tqdm.write(f"[{idx+1}/{len(regions_with_weights)}] 📍 {region_name} (target: {target_points:,})...")

        # Get the boundary of the region
        gdf = ox.geocode_to_gdf(region)

        # Get real street names for this region from major city
        major_city = major_cities.get(region_name, region)
        street_names = get_street_names_for_region(region_name, major_city)
        tqdm.write(f"   ✓ Loaded {len(street_names)} street names")

        # Get buildings for this region
        buildings = get_buildings_for_region(region_name, gdf, target_points)

        if buildings is not None and len(buildings) > 0:
            stats['total_buildings_found'] += len(buildings)
            tqdm.write(f"   📊 Total buildings found so far: {stats['total_buildings_found']:,}")

            # Sample buildings to match target
            if len(buildings) > target_points:
                tqdm.write(f"   🎲 Sampling {target_points:,} buildings from {len(buildings):,} available")
                sampled_buildings = buildings.sample(n=target_points)
            else:
                tqdm.write(f"   📍 Using all {len(buildings):,} buildings (less than target)")
                sampled_buildings = buildings

            # Extract centroids and create points
            tqdm.write(f"   🗺️  Extracting building centroids...")
            region_points = 0
            skipped_buildings = 0

            for idx, (_, building) in enumerate(sampled_buildings.iterrows()):
                try:
                    # Get centroid of building
                    if hasattr(building.geometry, 'centroid'):
                        centroid = building.geometry.centroid

                        all_points.append({
                            "region": region_name,
                            "street": random.choice(street_names),
                            "housenumber": str(random.randint(1, 200)),
                            "city": region_name.split()[0] if ' ' in region_name else region_name,
                            "postcode": f"{random.randint(10000, 99999)}",
                            "lat": centroid.y,
                            "lon": centroid.x,
                            "building_type": building.get('building', 'yes') if isinstance(building.get('building'), str) else 'yes'
                        })
                        region_points += 1
                    else:
                        skipped_buildings += 1
                except Exception as e:
                    skipped_buildings += 1
                    continue

            if skipped_buildings > 0:
                tqdm.write(f"   ⚠️  Skipped {skipped_buildings} buildings (no valid centroid)")

            stats['processed_regions'] += 1
            stats['total_points'] += region_points

            elapsed = time.time() - region_start
            tqdm.write(f"   ✓ {region_name}: {region_points:,}/{target_points:,} punti estratti in {elapsed:.1f}s")
        else:
            # Fallback to random points if no buildings found
            tqdm.write(f"   ⚠️  No buildings available, using random points as fallback")

            region_bounds = gdf.geometry.iloc[0]
            minx, miny, maxx, maxy = region_bounds.bounds
            tqdm.write(f"   📏 Region bounds: lat [{miny:.4f}, {maxy:.4f}], lon [{minx:.4f}, {maxx:.4f}]")

            region_points = 0
            attempts = 0
            max_attempts = target_points * 10
            tqdm.write(f"   🎲 Generating random points (max {max_attempts:,} attempts)...")

            last_progress = 0
            while region_points < target_points and attempts < max_attempts:
                random_lon = random.uniform(minx, maxx)
                random_lat = random.uniform(miny, maxy)
                point = Point(random_lon, random_lat)

                if region_bounds.contains(point):
                    all_points.append({
                        "region": region_name,
                        "street": random.choice(street_names),
                        "housenumber": str(random.randint(1, 200)),
                        "city": region_name.split()[0] if ' ' in region_name else region_name,
                        "postcode": f"{random.randint(10000, 99999)}",
                        "lat": random_lat,
                        "lon": random_lon,
                        "building_type": "random"
                    })
                    region_points += 1

                    # Log progress every 20%
                    progress = (region_points / target_points) * 100
                    if progress >= last_progress + 20:
                        tqdm.write(f"   📍 Progress: {region_points:,}/{target_points:,} ({progress:.0f}%)")
                        last_progress = progress

                attempts += 1

            efficiency = (region_points / attempts * 100) if attempts > 0 else 0
            tqdm.write(f"   📊 Efficiency: {efficiency:.1f}% ({region_points:,} successful / {attempts:,} attempts)")

            stats['processed_regions'] += 1
            stats['total_points'] += region_points
            elapsed = time.time() - region_start
            tqdm.write(f"   ✓ {region_name}: {region_points:,}/{target_points:,} punti (random fallback) in {elapsed:.1f}s")

        # Salvataggio incrementale ogni 5 regioni
        if (idx + 1) % 5 == 0:
            temp_df = pd.DataFrame(all_points)
            temp_df.to_csv("buildings_italy_locations_temp.csv", index=False)
            tqdm.write(f"   💾 Backup intermedio salvato: {len(temp_df):,} punti")

    except Exception as e:
        stats['failed_regions'].append(region_name)
        tqdm.write(f"   ✗ ERRORE in {region_name}: {e}")
        continue

print()
print("=" * 80)
print("📊 RIEPILOGO FINALE")
print("=" * 80)

# Final statistics
end_time = datetime.now()
duration = end_time - stats['start_time']

print(f"✓ Regioni processate con successo: {stats['processed_regions']}/{stats['total_regions']}")
print(f"✗ Regioni fallite: {len(stats['failed_regions'])}")
if stats['failed_regions']:
    print(f"  Regioni con errori: {', '.join(stats['failed_regions'])}")
print(f"🏗️  Edifici reali trovati: {stats['total_buildings_found']:,}")
print(f"📍 Totale punti generati: {stats['total_points']:,}")
print(f"🎯 Target richiesto: {target_total:,}")
print(f"📈 Percentuale completamento: {(stats['total_points']/target_total*100):.1f}%")
print(f"⏱️  Tempo totale: {duration.total_seconds():.1f}s ({duration.total_seconds()/60:.1f}min)")
if stats['total_points'] > 0:
    print(f"⚡ Velocità media: {stats['total_points']/duration.total_seconds():.1f} edifici/sec")

# Convert to DataFrame and save
df = pd.DataFrame(all_points)
output_file = "buildings_italy_locations.csv"
df.to_csv(output_file, index=False)

print()
print("=" * 80)
print(f"✅ COMPLETATO!")
print(f"📁 File salvato: {output_file}")
print(f"📊 Dimensione dataset: {len(df):,} righe × {len(df.columns)} colonne")
print(f"💾 Dimensione file: {pd.read_csv(output_file).memory_usage(deep=True).sum() / 1024:.1f} KB")
print("=" * 80)

# Create visualization of the generated points
print()
print("=" * 80)
print("📊 GENERAZIONE PLOT")
print("=" * 80)

try:
    # Create figure with larger size
    fig, ax = plt.subplots(figsize=(14, 16))

    # Plot points colored by region
    regions = df['region'].unique()
    colors = plt.cm.tab20(range(len(regions)))

    for idx, region in enumerate(regions):
        region_data = df[df['region'] == region]
        ax.scatter(
            region_data['lon'],
            region_data['lat'],
            c=[colors[idx]],
            label=region,
            alpha=0.6,
            s=10
        )

    # Styling
    ax.set_xlabel('Longitudine', fontsize=12, fontweight='bold')
    ax.set_ylabel('Latitudine', fontsize=12, fontweight='bold')
    ax.set_title(f'Distribuzione Geografica Edifici Reali\n{len(df):,} punti da OpenStreetMap - 20 regioni italiane',
                 fontsize=14, fontweight='bold', pad=20)
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)

    # Set aspect ratio to match Italy's geography
    ax.set_aspect('equal', adjustable='box')

    plt.tight_layout()

    # Save plot
    plot_filename = 'buildings_italy_locations_plot.png'
    plt.savefig(plot_filename, dpi=150, bbox_inches='tight')
    print(f"✓ Plot salvato: {plot_filename}")

    # Also create a simpler density plot
    fig2, ax2 = plt.subplots(figsize=(12, 14))
    ax2.hexbin(df['lon'], df['lat'], gridsize=50, cmap='YlOrRd', mincnt=1)
    ax2.set_xlabel('Longitudine', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Latitudine', fontsize=12, fontweight='bold')
    ax2.set_title(f'Mappa di Densità - {len(df):,} Edifici Reali', fontsize=14, fontweight='bold', pad=20)
    ax2.grid(True, alpha=0.3, linestyle='--')
    ax2.set_aspect('equal', adjustable='box')
    plt.colorbar(ax2.collections[0], ax=ax2, label='Densità punti')

    plt.tight_layout()
    density_filename = 'buildings_italy_locations_density.png'
    plt.savefig(density_filename, dpi=150, bbox_inches='tight')
    print(f"✓ Density plot salvato: {density_filename}")

    # Building type distribution
    if 'building_type' in df.columns:
        building_counts = df['building_type'].value_counts().head(10)

        fig3, ax3 = plt.subplots(figsize=(10, 6))
        building_counts.plot(kind='barh', ax=ax3, color='steelblue')
        ax3.set_xlabel('Numero di edifici', fontsize=12, fontweight='bold')
        ax3.set_ylabel('Tipo di edificio', fontsize=12, fontweight='bold')
        ax3.set_title('Top 10 Tipologie di Edifici', fontsize=14, fontweight='bold')
        ax3.grid(True, alpha=0.3, axis='x')

        plt.tight_layout()
        buildings_type_filename = 'buildings_italy_types.png'
        plt.savefig(buildings_type_filename, dpi=150, bbox_inches='tight')
        print(f"✓ Building types plot salvato: {buildings_type_filename}")

    print("=" * 80)

except Exception as e:
    print(f"⚠️  Errore nella generazione del plot: {e}")
    print("=" * 80)
