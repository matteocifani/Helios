
import os
import sys
import pandas as pd
from dotenv import load_dotenv

# Add parent directory to path to import src
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.data.db_utils import fetch_abitazioni

def verify_data():
    print("Fetching abitazioni data...")
    df = fetch_abitazioni()
    
    if df.empty:
        print("DataFrame is empty!")
        return

    print(f"Total rows: {len(df)}")
    print("Columns:", df.columns.tolist())
    
    print("\n--- Hydro Risk P3 ---")
    if 'hydro_risk_p3' in df.columns:
        print("Dtype:", df['hydro_risk_p3'].dtype)
        print("Unique values:", df['hydro_risk_p3'].unique())
        print("Head:", df['hydro_risk_p3'].head(10).tolist())
        print("Number of nulls:", df['hydro_risk_p3'].isnull().sum())
    else:
        print("Column hydro_risk_p3 NOT found")

    print("\n--- Flood Risk P3 ---")
    if 'flood_risk_p3' in df.columns:
        print("Dtype:", df['flood_risk_p3'].dtype)
        print("Unique values:", df['flood_risk_p3'].unique())
        print("Head:", df['flood_risk_p3'].head(10).tolist())
    else:
        print("Column flood_risk_p3 NOT found")

    print("\n--- Flood Risk P4 ---")
    if 'flood_risk_p4' in df.columns:
        print("Dtype:", df['flood_risk_p4'].dtype)
        print("Unique values:", df['flood_risk_p4'].unique())
    else:
        print("Column flood_risk_p4 NOT found")

if __name__ == "__main__":
    verify_data()
