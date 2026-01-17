"""
DEPRECATED: Use src.ada.chat instead.
This file is kept for backward compatibility.
"""
import warnings
warnings.warn(
    "Importing from 'ada_chat_enhanced' is deprecated. Use 'from src.ada.chat import render_ada_chat' instead.",
    DeprecationWarning,
    stacklevel=2
)
from src.ada.chat import *
