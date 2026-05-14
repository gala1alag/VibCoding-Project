from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLineEdit, QListWidget, QListWidgetItem, QLabel
)
from PyQt5.QtCore import Qt, QFileInfo
from PyQt5.QtGui import QIcon
from controllers.launcher_ctrl import LauncherCtrl


class LauncherView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._ctrl = LauncherCtrl()
        self._all_apps = []
        self._build_ui()
        self._ctrl.start_scan(on_done=self._on_scan_done)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        self._search = QLineEdit()
        self._search.setPlaceholderText("搜索应用...")
        self._search.setFixedHeight(40)
        self._search.setStyleSheet("font-size: 16px; padding: 4px 8px;")
        self._search.textChanged.connect(self._on_search)
        layout.addWidget(self._search)

        self._status = QLabel("正在扫描应用...")
        self._status.setStyleSheet("color: #888; font-size: 12px;")
        layout.addWidget(self._status)

        self._list = QListWidget()
        self._list.setIconSize(__import__('PyQt5.QtCore', fromlist=['QSize']).QSize(24, 24))
        self._list.itemActivated.connect(self._on_launch)
        layout.addWidget(self._list)

    def showEvent(self, event):
        super().showEvent(event)
        self._search.setFocus()

    def _on_scan_done(self):
        self._all_apps = self._ctrl.search("")
        self._status.setText(f"共 {len(self._all_apps)} 个应用")
        self._refresh_list(self._all_apps)

    def _on_search(self, text: str):
        results = self._ctrl.search(text)
        self._refresh_list(results)

    def _refresh_list(self, apps: list):
        self._list.clear()
        for app in apps:
            item = QListWidgetItem(app["name"])
            item.setToolTip(app["path"])
            item.setData(Qt.UserRole, app)
            icon = QIcon(QFileInfo(app["path"]).absoluteFilePath())
            if not icon.isNull():
                item.setIcon(icon)
            self._list.addItem(item)

    def _on_launch(self, item: QListWidgetItem):
        app = item.data(Qt.UserRole)
        try:
            self._ctrl.launch(app)
        except Exception:
            pass

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            item = self._list.currentItem() or (self._list.item(0) if self._list.count() else None)
            if item:
                self._on_launch(item)
        else:
            super().keyPressEvent(event)
