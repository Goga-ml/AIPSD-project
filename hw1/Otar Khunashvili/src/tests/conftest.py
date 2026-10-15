import sys
from pathlib import Path

# src/ modules import each other by bare name (they also run as scripts), so put src/ on the path.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
