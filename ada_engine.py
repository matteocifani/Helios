"""
DEPRECATED: Use src.ada.engine instead.
This file is kept for backward compatibility.
"""
import warnings
warnings.warn(
    "Importing from 'ada_engine' is deprecated. Use 'from src.ada.engine import ADAEngine' instead.",
    DeprecationWarning,
    stacklevel=2
)
from src.ada.engine import *
