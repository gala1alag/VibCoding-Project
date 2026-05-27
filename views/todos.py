from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QPushButton, QDialog, QFormLayout, QLineEdit, QComboBox, QTextEdit,
    QDialogButtonBox, QMessageBox, QMenu, QAction,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from controllers.todo_ctrl import TodoController

_PRIORITY_COLORS = {"high": "#e74c3c", "medium": "#f39c12", "low": "#27ae60"}
_PRIORITY_LABELS = {"high": "高", "medium": "中", "low": "低"}
_STATUS_LABELS = {"todo": "待办", "doing": "进行中", "done": "完成"}
_COLUMNS = ["todo", "doing", "done"]


class _TodoDialog(QDialog):
    def __init__(self, parent=None, todo=None):
        super().__init__(parent)
        self.setWindowTitle("编辑任务" if todo else "新建任务")
        self.setMinimumWidth(380)
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self._title = QLineEdit()
        self._title.setPlaceholderText("任务标题")
        self._desc = QTextEdit()
        self._desc.setPlaceholderText("详细描述（可选）")
        self._desc.setMaximumHeight(72)
        self._priority = QComboBox()
        self._priority.addItems(["高", "中", "低"])
        self._status = QComboBox()
        self._status.addItems(["待办", "进行中", "完成"])
        self._due = QLineEdit()
        self._due.setPlaceholderText("YYYY-MM-DD（可选）")

        form.addRow("标题 *", self._title)
        form.addRow("描述", self._desc)
        form.addRow("优先级", self._priority)
        form.addRow("状态", self._status)
        form.addRow("截止日期", self._due)
        layout.addLayout(form)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self._accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

        if todo:
            self._title.setText(todo.get("title") or "")
            self._desc.setPlainText(todo.get("description") or "")
            self._priority.setCurrentIndex({"high": 0, "medium": 1, "low": 2}.get(todo.get("priority"), 1))
            self._status.setCurrentIndex({"todo": 0, "doing": 1, "done": 2}.get(todo.get("status"), 0))
            self._due.setText(todo.get("due_date") or "")

    def _accept(self):
        if not self._title.text().strip():
            QMessageBox.warning(self, "提示", "标题不能为空")
            return
        self.accept()

    def get_data(self):
        return {
            "title": self._title.text().strip(),
            "description": self._desc.toPlainText().strip(),
            "priority": ["high", "medium", "low"][self._priority.currentIndex()],
            "status": ["todo", "doing", "done"][self._status.currentIndex()],
            "due_date": self._due.text().strip() or None,
        }


class _KanbanColumn(QWidget):
    def __init__(self, status, ctrl, board, parent=None):
        super().__init__(parent)
        self._status = status
        self._ctrl = ctrl
        self._board = board
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        self._header = QLabel(_STATUS_LABELS[self._status])
        self._header.setAlignment(Qt.AlignCenter)
        self._header.setStyleSheet("font-size: 14px; font-weight: bold; padding: 6px; border-radius: 4px;")
        layout.addWidget(self._header)

        self._list = QListWidget()
        self._list.setContextMenuPolicy(Qt.CustomContextMenu)
        self._list.customContextMenuRequested.connect(self._context_menu)
        self._list.setWordWrap(True)
        layout.addWidget(self._list, stretch=1)

        add_btn = QPushButton("+ 添加")
        add_btn.clicked.connect(self._on_add)
        layout.addWidget(add_btn)

    def load(self, todos):
        self._list.clear()
        for t in todos:
            if t["status"] != self._status:
                continue
            priority = t.get("priority", "medium")
            due = f"  截止 {t['due_date']}" if t.get("due_date") else ""
            item = QListWidgetItem(f"[{_PRIORITY_LABELS[priority]}] {t['title']}{due}")
            item.setData(Qt.UserRole, t["id"])
            item.setForeground(QColor(_PRIORITY_COLORS.get(priority, "#888")))
            self._list.addItem(item)
        self._header.setText(f"{_STATUS_LABELS[self._status]}  ({self._list.count()})")

    def _on_add(self):
        dlg = _TodoDialog(self)
        if dlg.exec_() != QDialog.Accepted:
            return
        data = dlg.get_data()
        data["status"] = self._status
        self._ctrl.add_todo(**data)
        self._board.refresh()

    def _context_menu(self, pos):
        item = self._list.itemAt(pos)
        if not item:
            return
        tid = item.data(Qt.UserRole)
        menu = QMenu(self)
        menu.addAction("编辑", lambda: self._edit(tid))
        menu.addSeparator()
        for s in _COLUMNS:
            if s != self._status:
                menu.addAction(f"移到 {_STATUS_LABELS[s]}", lambda checked=False, st=s: self._move(tid, st))
        menu.addSeparator()
        menu.addAction("删除", lambda: self._delete(tid, item.text()))
        menu.exec_(self._list.viewport().mapToGlobal(pos))

    def _edit(self, tid):
        todos = self._ctrl.list_todos()
        todo = next((t for t in todos if t["id"] == tid), None)
        if not todo:
            return
        dlg = _TodoDialog(self, todo=todo)
        if dlg.exec_() == QDialog.Accepted:
            self._ctrl.update_todo(tid, **dlg.get_data())
            self._board.refresh()

    def _move(self, tid, status):
        self._ctrl.move_todo(tid, status)
        self._board.refresh()

    def _delete(self, tid, text):
        if QMessageBox.question(self, "确认删除", f"删除任务 {text.strip()}？") == QMessageBox.Yes:
            self._ctrl.delete_todo(tid)
            self._board.refresh()


class TodosView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._ctrl = TodoController()
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        header = QHBoxLayout()
        title = QLabel("TODO 看板")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        cols_widget = QWidget()
        cols_layout = QHBoxLayout(cols_widget)
        cols_layout.setContentsMargins(0, 0, 0, 0)
        cols_layout.setSpacing(8)

        self._columns = {}
        for status in _COLUMNS:
            col = _KanbanColumn(status, self._ctrl, self)
            self._columns[status] = col
            cols_layout.addWidget(col)

        layout.addWidget(cols_widget, stretch=1)

    def refresh(self):
        todos = self._ctrl.list_todos()
        for col in self._columns.values():
            col.load(todos)
