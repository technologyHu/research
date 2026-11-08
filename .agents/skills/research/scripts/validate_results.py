"""Compatibility launcher; implementation belongs to the common support skill."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "research-common" / "scripts"))
from legacy_entry import forward

forward(globals())
