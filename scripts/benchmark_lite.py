
import time
import sys
import os
import pandas as pd

# Add root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data.db_utils import fetch_abitazioni, fetch_clienti

def benchmark():
    print("🚀 Starting Benchmark: Lite vs Full...")
    
    # 1. Full Load (Legacy)
    # Note: We can't easily force non-lite if we changed default, but we can pass lite=False
    print("\n📦 [Legacy] Fetching Full Data (approximate)...")
    start_time = time.time()
    df_ab_full = fetch_abitazioni(lite=False)
    df_cl_full = fetch_clienti(lite=False)
    full_time = time.time() - start_time
    print(f"❌ Full Load: {full_time:.2f}s")
    
    # 2. Lite Load (Optimized)
    print("\n⚡ [Optimized] Fetching Lite Data...")
    start_time = time.time()
    df_ab_lite = fetch_abitazioni(lite=True)
    df_cl_lite = fetch_clienti(lite=True)
    lite_time = time.time() - start_time
    print(f"✅ Lite Load: {lite_time:.2f}s")
    
    # Calculate Improvement
    improvement = full_time - lite_time
    percent = (improvement / full_time) * 100
    
    print("\n" + "="*40)
    print(f"🚀 SPEEDUP: {percent:.1f}% Faster")
    print(f"⏱ Time Saved: {improvement:.2f}s per load")
    print("="*40)

if __name__ == "__main__":
    benchmark()
