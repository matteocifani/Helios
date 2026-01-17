#!/usr/bin/env python3
"""
Test Supabase query for policies
"""

import sys
import os

# Add current dir to path
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

from db_utils import get_supabase_client

client = get_supabase_client()

if not client:
    print("❌ Failed to get Supabase client")
    sys.exit(1)

print("✅ Supabase client connected")

# Test query with client_id = 9501
print("\n📊 Testing query: polizze WHERE codice_cliente = 9501")

try:
    response = client.table("polizze").select("*").eq("codice_cliente", 9501).execute()

    print(f"Results: {len(response.data)} rows")

    if response.data:
        print("\n📋 Found policies:")
        for i, policy in enumerate(response.data, 1):
            print(f"\n{i}. {policy.get('prodotto')}")
            print(f"   codice_cliente: {policy.get('codice_cliente')} (type: {type(policy.get('codice_cliente'))})")
            print(f"   stato: {policy.get('stato_polizza')}")
    else:
        print("\n❌ No policies found")

        # Try to see what client_ids exist
        print("\n🔍 Let's check what client IDs exist in the table:")
        sample = client.table("polizze").select("codice_cliente").limit(10).execute()
        print(f"Sample client IDs: {[p['codice_cliente'] for p in sample.data]}")

except Exception as e:
    print(f"❌ Error: {e}")
