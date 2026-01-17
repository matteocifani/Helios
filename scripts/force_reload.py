"""
Script per forzare il reload completo di tutti i moduli.
Da eseguire prima di lanciare Streamlit.
"""

import sys
import os
from pathlib import Path

# Get the script directory
script_dir = Path(__file__).parent

# Remove all cached modules from this directory
modules_to_remove = []
for module_name in list(sys.modules.keys()):
    module = sys.modules[module_name]
    if hasattr(module, '__file__') and module.__file__:
        module_path = Path(module.__file__)
        try:
            if script_dir in module_path.parents or module_path.parent == script_dir:
                modules_to_remove.append(module_name)
        except:
            pass

for module_name in modules_to_remove:
    print(f"🧹 Removing cached module: {module_name}")
    del sys.modules[module_name]

print("✅ Module cache cleared!")
