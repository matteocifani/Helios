
import os
import sys
import pandas as pd
from dotenv import load_dotenv

# Add parent directory to path to import src
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.data.db_utils import fetch_abitazioni

def verify_chart_logic():
    print("Fetching abitazioni data...")
    df = fetch_abitazioni()
    
    if df.empty:
        print("DataFrame is empty!")
        return

    # Simulate Filtered DF (assuming all data for now)
    filtered_df = df

    print("\n--- Verifying Hydro Risk Binning ---")
    if 'hydro_risk_p3' in filtered_df.columns:
        # Helper for binning
        def get_hydro_level(val):
            try:
                v = float(val)
                if v < 5.0: return "Basso"
                if v < 20.0: return "Medio"
                return "Alto"
            except:
                return "N/D"

        risk_levels = filtered_df['hydro_risk_p3'].apply(get_hydro_level)
        valid_levels = ["Basso", "Medio", "Alto"]
        counts = risk_levels.value_counts().reindex(valid_levels, fill_value=0)
        
        print("Hydro Counts:")
        print(counts)
    else:
        print("Column hydro_risk_p3 NOT found")

    print("\n--- Verifying Flood Risk Binning ---")
    if 'flood_risk_p3' in filtered_df.columns:
        # Helper for binning
        def get_flood_level(val):
            try:
                v = float(val)
                if v < 10.0: return "Basso"
                if v < 30.0: return "Medio"
                return "Alto"
            except:
                return "N/D"

        risk_levels = filtered_df['flood_risk_p3'].apply(get_flood_level)
        valid_levels = ["Basso", "Medio", "Alto"]
        counts = risk_levels.value_counts().reindex(valid_levels, fill_value=0)
        
        print("Flood Counts:")
        print(counts)
    else:
        print("Column flood_risk_p3 NOT found")

if __name__ == "__main__":
    verify_chart_logic()
