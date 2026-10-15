import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[1]  # tests/ lives inside src/
sys.path.insert(0, str(SRC))
