#!/usr/bin/env python3
"""
List all tables in Supabase and their row counts
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

from db_utils import get_supabase_client

client = get_supabase_client()

if not client:
    print("❌ Failed to get Supabase client")
    sys.exit(1)

print("✅ Supabase client connected\n")

# List of common table names to try
tables_to_check = [
    "polizze", "policies", "policy",
    "clienti", "clients", "client",
    "abitazioni", "properties",
    "interactions"
]

print("📊 Checking tables:\n")

for table_name in tables_to_check:
    try:
        response = client.table(table_name).select("*", count="exact").limit(1).execute()
        count = response.count if hasattr(response, 'count') else len(response.data)
        print(f"✅ {table_name:20} - {count:,} rows")

        # Show sample data
        if response.data:
            first_row = response.data[0]
            columns = list(first_row.keys())[:5]  # First 5 columns
            print(f"   Columns (sample): {', '.join(columns)}")

    except Exception as e:
        print(f"❌ {table_name:20} - Error: {str(e)[:50]}")

print("\n" + "="*60)
