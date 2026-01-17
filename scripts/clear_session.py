"""
Script per pulire completamente la cache di Streamlit.
"""

import shutil
import os
from pathlib import Path

# Clear Streamlit cache directories
cache_dirs = [
    Path.home() / ".streamlit" / "cache",
    Path.home() / ".streamlit" / "cache_data",
    Path(__file__).parent / ".streamlit",
]

for cache_dir in cache_dirs:
    if cache_dir.exists():
        print(f"🗑️  Removing: {cache_dir}")
        shutil.rmtree(cache_dir, ignore_errors=True)
    else:
        print(f"⏭️  Not found: {cache_dir}")

print("✅ All Streamlit caches cleared!")
