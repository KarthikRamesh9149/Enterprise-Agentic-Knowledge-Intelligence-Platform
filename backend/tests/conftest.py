import os
import sys
from pathlib import Path

os.environ.setdefault("JWT_SECRET", "test-only-signing-secret-not-for-production-1234")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
