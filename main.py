import sys
import os
from PyQt5.QtWidgets import QApplication
from core.database import init_db
from core.settings import Settings
from views.main_window import MainWindow


def load_theme(app: QApplication, theme: str):
    theme_path = os.path.join(
        os.path.dirname(__file__), "assets", "themes", f"{theme}.qss"
    )
    if os.path.exists(theme_path):
        with open(theme_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())


def main():
    init_db()

    app = QApplication(sys.argv)
    app.setApplicationName("开发者工作台")

    settings = Settings()
    load_theme(app, settings.get("theme") or "dark")

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
