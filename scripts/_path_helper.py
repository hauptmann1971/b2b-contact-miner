"""Helper to add project root to Python path for scripts in subdirectories"""
import sys
import os
from pathlib import Path

# Add project root to path (scripts/ is one level deep)
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
