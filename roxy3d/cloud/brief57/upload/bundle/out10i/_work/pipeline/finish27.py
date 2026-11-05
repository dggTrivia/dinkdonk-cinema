"""Recheck only final assembly/packing after a packaging-only correction."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from smoke27 import draft,tail,finish
from contracts27 import run
draft();tail();run();finish()
