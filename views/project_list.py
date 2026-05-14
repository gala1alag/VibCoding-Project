from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QComboBox, QPushButton, QFileDialog, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor
from controllers.project_ctrl import ProjectCtrl

LANGUAGES = ["全部", "Python", "C++", "Java", "JavaScript", "TypeScript", "C#", "Go", "Rust", "HTML/CSS", "其他"]


class ProjectListWidget(QWidget):
    project_selected = pyqtSignal(int)
    project_deleted = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._ctrl = ProjectCtrl()
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._lang_filter = QComboBox()
        self._lang_filter.addItems(LANGUAGES)
        self._lang_filter.currentTextChanged.connect(self.refresh)
        layout.addWidget(self._lang_filter)

        self._list = QListWidget()
        self._list.currentItemChanged.connect(self._on_selection_changed)
        layout.addWidget(self._list)

        btn_row = QHBoxLayout()
        self._btn_add = QPushButton("添加项目")
        self._btn_del = QPushButton("删除")
        self._btn_add.clicked.connect(self._on_add)
        self._btn_del.clicked.connect(self._on_delete)
        btn_row.addWidget(self._btn_add)
        btn_row.addWidget(self._btn_del)
        layout.addLayout(btn_row)

    def refresh(self):
        lang = self._lang_filter.currentText()
        projects = self._ctrl.get_all(lang)
        self._list.clear()
        for p in projects:
            item = QListWidgetItem()
            color = p.get("color") or "#4A90D9"
            lang_label = p.get("language") or "其他"
            item.setText(f"  {p['name']}  [{lang_label}]")
            item.setData(Qt.UserRole, p["id"])
            item.setForeground(QColor(color))
            self._list.addItem(item)

    def _on_selection_changed(self, current, _previous):
        if current:
            self.project_selected.emit(current.data(Qt.UserRole))

    def _on_add(self):
        path = QFileDialog.getExistingDirectory(self, "选择项目文件夹")
        if not path:
            path, _ = QFileDialog.getOpenFileName(self, "选择单文件", filter="所有文件 (*)")
        if not path:
            return
        import os
        name = os.path.basename(path)
        type_ = "file" if os.path.isfile(path) else "folder"
        self._ctrl.add(name, path, type_)
        self.refresh()

    def _on_delete(self):
        item = self._list.currentItem()
        if not item:
            return
        pid = item.data(Qt.UserRole)
        reply = QMessageBox.question(self, "确认删除", f"删除项目 {item.text().strip()}？")
        if reply == QMessageBox.Yes:
            self._ctrl.delete(pid)
            self.refresh()
            self.project_deleted.emit()
