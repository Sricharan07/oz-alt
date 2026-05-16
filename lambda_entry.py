from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "packages" / "oz-api" / "src"))

from oz_api.lambda_app import handler  # noqa: E402

