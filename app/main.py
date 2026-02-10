from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import importlib.util  # noqa: E402


_spec = importlib.util.spec_from_file_location(
    "app_main_entry", str(SRC / "app" / "main.py")
)
if _spec is None or _spec.loader is None:
    raise RuntimeError("Unable to load src/app/main.py")
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)
run_app = _module.main


if __name__ == "__main__":
    raise SystemExit(run_app())
