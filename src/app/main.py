from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from .config import load_config
from .db.session import init_db
from .ui.main_window import MainWindow


def main() -> int:
    config = load_config()
    init_db(config.db_path)

    app = QApplication(sys.argv)
    window = MainWindow(config)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
