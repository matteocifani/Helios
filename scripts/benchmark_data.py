
import time
import sys
import os

# Add root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data.db_utils import fetch_abitazioni, fetch_clienti

def benchmark():
    print("🚀 Starting Benchmark...")
    
    start_time = time.time()
    print("📦 Fetching Abitazioni (simulating load_data part 1)...")
    df_ab = fetch_abitazioni()
    ab_time = time.time() - start_time
    print(f"✅ Abitazioni fetched in {ab_time:.2f}s. Rows: {len(df_ab)}")
    
    start_time = time.time()
    print("👥 Fetching Clienti (simulating load_data part 2)...")
    df_cl = fetch_clienti()
    cl_time = time.time() - start_time
    print(f"✅ Clienti fetched in {cl_time:.2f}s. Rows: {len(df_cl)}")
    
    print("-" * 30)
    print(f"Total Data Load Time: {ab_time + cl_time:.2f}s")
    print("-" * 30)

if __name__ == "__main__":
    benchmark()
