"""
Export Supabase database schema to documentation.
Fetches table structures and saves them to docs/supabase_schema/
"""

import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'docs', 'supabase_schema')

# Tables to document
TABLES = [
    'clienti',
    'polizze',
    'abitazioni',
    'sinistri',
    'interactions',
]


def get_supabase_client():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        print("ERROR: SUPABASE_URL and SUPABASE_KEY must be set")
        return None
    return create_client(url, key)


def get_table_schema(client, table_name):
    """Get schema by fetching one row and analyzing structure."""
    try:
        response = client.table(table_name).select("*").limit(1).execute()
        if response.data:
            sample = response.data[0]
            schema = {}
            for key, value in sample.items():
                if value is None:
                    dtype = "unknown (null)"
                elif isinstance(value, bool):
                    dtype = "boolean"
                elif isinstance(value, int):
                    dtype = "integer"
                elif isinstance(value, float):
                    dtype = "float"
                elif isinstance(value, str):
                    if 'date' in key.lower() or key.endswith('_at'):
                        dtype = "timestamp/date"
                    else:
                        dtype = "text"
                elif isinstance(value, list):
                    dtype = "array"
                elif isinstance(value, dict):
                    dtype = "jsonb"
                else:
                    dtype = type(value).__name__
                schema[key] = {"type": dtype, "sample": value}
            return schema, sample
        return {}, {}
    except Exception as e:
        print(f"  Error fetching {table_name}: {e}")
        return {}, {}


def get_table_count(client, table_name):
    """Get row count for a table."""
    try:
        response = client.table(table_name).select("*", count="exact").limit(0).execute()
        return response.count
    except:
        return "unknown"


def main():
    print("=" * 60)
    print("       SUPABASE SCHEMA EXPORTER")
    print("=" * 60)

    client = get_supabase_client()
    if not client:
        sys.exit(1)

    print("\nConnected to Supabase")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    all_schemas = []

    for table in TABLES:
        print(f"\nFetching schema for: {table}")
        schema, sample = get_table_schema(client, table)
        count = get_table_count(client, table)

        if schema:
            # Save individual table schema
            table_file = os.path.join(OUTPUT_DIR, f"{table}.md")
            with open(table_file, 'w', encoding='utf-8') as f:
                f.write(f"# Table: {table}\n\n")
                f.write(f"**Row count:** {count}\n\n")
                f.write("## Columns\n\n")
                f.write("| Column | Type | Sample Value |\n")
                f.write("|--------|------|-------------|\n")
                for col, info in schema.items():
                    sample_val = str(info['sample'])[:50] if info['sample'] is not None else "NULL"
                    sample_val = sample_val.replace("|", "\\|").replace("\n", " ")
                    f.write(f"| {col} | {info['type']} | {sample_val} |\n")

            print(f"  Saved: {table_file}")
            print(f"  Columns: {len(schema)}, Rows: {count}")

            all_schemas.append({
                "table": table,
                "columns": len(schema),
                "rows": count,
                "schema": schema
            })

    # Save combined overview
    overview_file = os.path.join(OUTPUT_DIR, "README.md")
    with open(overview_file, 'w', encoding='utf-8') as f:
        f.write("# Supabase Database Schema\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("## Tables Overview\n\n")
        f.write("| Table | Columns | Rows |\n")
        f.write("|-------|---------|------|\n")
        for s in all_schemas:
            f.write(f"| [{s['table']}]({s['table']}.md) | {s['columns']} | {s['rows']} |\n")

        f.write("\n## Table Details\n\n")
        for s in all_schemas:
            f.write(f"### {s['table']}\n\n")
            f.write("| Column | Type |\n")
            f.write("|--------|------|\n")
            for col, info in s['schema'].items():
                f.write(f"| {col} | {info['type']} |\n")
            f.write("\n")

    print(f"\nOverview saved: {overview_file}")
    print(f"\nDone! Schema exported to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
