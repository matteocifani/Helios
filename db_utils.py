"""
DEPRECATED: Use src.data.db_utils instead.
This file is kept for backward compatibility.
"""
import warnings
warnings.warn(
    "Importing from 'db_utils' is deprecated. Use 'from src.data.db_utils import ...' instead.",
    DeprecationWarning,
    stacklevel=2
)
from src.data.db_utils import *
