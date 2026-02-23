"""App package entry point."""

from __future__ import annotations

import sys

sys.modules.setdefault("app", sys.modules[__name__])
