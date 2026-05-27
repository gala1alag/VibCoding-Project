from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QListWidget, QListWidgetItem,
    QLineEdit, QComboBox, QPushButton, QLabel, QPlainTextEdit, QFormLayout,
    QMessageBox, QApplication,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont
from controllers.snippet_ctrl import SnippetController

_LANGUAGES = ["Python", "C++", "Java", "JavaScript", "TypeScript", "C#", "Go", "Rust", "HTML/CSS", "SQL", "Shell", "其他"]
_LANG_COLORS = {
    "Python": "#3572A5", "C++": "#f34b7d", "Java": "#b07219",
    "JavaScript": "#f1e05a", "TypeScript": "#2b7489", "C#": "#178600",
    "Go": "#00ADD8", "Rust": "#dea584", "HTML/CSS": "#e34c26",
    "SQL": "#e38c00", "Shell": "#89e051", "其他": "#888888",
}


class SnippetsView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._ctrl = SnippetController()
        self._current_id = None
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        splitter = QSplitter(Qt.Horizontal)

        # ── left panel ──────────────────────────────────────────────────────
        left = QWidget()
        ll = QVBoxLayout(left)
        ll.setContentsMargins(4, 4, 4, 4)

        self._search = QLineEdit()
        self._search.setPlaceholderText("搜索片段…")
        self._search.textChanged.connect(self.refresh)
        ll.addWidget(self._search)

        self._lang_filter = QComboBox()
        self._lang_filter.addItem("全部")
        self._lang_filter.addItems(_LANGUAGES)
        self._lang_filter.currentTextChanged.connect(self.refresh)
        ll.addWidget(self._lang_filter)

        self._list = QListWidget()
        self._list.currentItemChanged.connect(self._on_select)
        ll.addWidget(self._list)

        btn_row = QHBoxLayout()
        self._btn_add = QPushButton("新建")
        self._btn_del = QPushButton("删除")
        self._btn_add.clicked.connect(self._on_add)
        self._btn_del.clicked.connect(self._on_delete)
        btn_row.addWidget(self._btn_add)
        btn_row.addWidget(self._btn_del)
        ll.addLayout(btn_row)

        # ── right panel ─────────────────────────────────────────────────────
        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(8, 8, 8, 8)

        self._placeholder = QLabel("请在左侧选择或新建代码片段")
        self._placeholder.setAlignment(Qt.AlignCenter)
        self._placeholder.setStyleSheet("color: #666; font-size: 16px;")
        rl.addWidget(self._placeholder)

        self._form = QWidget()
        fl = QVBoxLayout(self._form)
        fl.setContentsMargins(0, 0, 0, 0)

        meta = QFormLayout()
        self._title_edit = QLineEdit()
        self._title_edit.setPlaceholderText("片段标题")
        self._lang_combo = QComboBox()
        self._lang_combo.addItems(_LANGUAGES)
        self._desc_edit = QLineEdit()
        self._desc_edit.setPlaceholderText("简短描述（可选）")
        meta.addRow("标题", self._title_edit)
        meta.addRow("语言", self._lang_combo)
        meta.addRow("描述", self._desc_edit)
        fl.addLayout(meta)

        fl.addWidget(QLabel("代码"))
        self._code_edit = QPlainTextEdit()
        self._code_edit.setFont(QFont("Consolas", 11))
        self._code_edit.setPlaceholderText("在此粘贴代码…")
        fl.addWidget(self._code_edit, stretch=1)

        act = QHBoxLayout()
        self._copy_btn = QPushButton("复制代码")
        self._save_btn = QPushButton("保存")
        self._copy_btn.clicked.connect(self._on_copy)
        self._save_btn.clicked.connect(self._on_save)
        act.addStretch()
        act.addWidget(self._copy_btn)
        act.addWidget(self._save_btn)
        fl.addLayout(act)

        rl.addWidget(self._form)
        self._form.hide()

        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        root.addWidget(splitter)

    def refresh(self):
        lang = self._lang_filter.currentText()
        search = self._search.text().strip()
        snippets = self._ctrl.list_snippets(
            language=lang if lang != "全部" else None,
            search=search or None,
        )
        self._list.clear()
        for s in snippets:
            item = QListWidgetItem()
            lang_label = s.get("language") or "其他"
            item.setText(f"  {s['title']}  [{lang_label}]")
            item.setData(Qt.UserRole, s["id"])
            item.setForeground(QColor(_LANG_COLORS.get(lang_label, "#888888")))
            self._list.addItem(item)
        if self._current_id is not None:
            for i in range(self._list.count()):
                if self._list.item(i).data(Qt.UserRole) == self._current_id:
                    self._list.setCurrentRow(i)
                    break

    def _on_select(self, current, _prev):
        if not current:
            return
        sid = current.data(Qt.UserRole)
        self._current_id = sid
        s = self._ctrl.get_by_id(sid)
        if not s:
            return
        self._title_edit.setText(s.get("title") or "")
        idx = self._lang_combo.findText(s.get("language") or "其他")
        self._lang_combo.setCurrentIndex(idx if idx >= 0 else self._lang_combo.count() - 1)
        self._desc_edit.setText(s.get("description") or "")
        self._code_edit.blockSignals(True)
        self._code_edit.setPlainText(s.get("code") or "")
        self._code_edit.blockSignals(False)
        self._placeholder.hide()
        self._form.show()

    def _on_add(self):
        self._current_id = None
        self._list.clearSelection()
        self._title_edit.clear()
        self._lang_combo.setCurrentIndex(0)
        self._desc_edit.clear()
        self._code_edit.clear()
        self._placeholder.hide()
        self._form.show()
        self._title_edit.setFocus()

    def _on_delete(self):
        item = self._list.currentItem()
        if not item:
            return
        if QMessageBox.question(self, "确认删除", f"删除片段 {item.text().strip()}？") != QMessageBox.Yes:
            return
        self._ctrl.delete_snippet(item.data(Qt.UserRole))
        self._current_id = None
        self._placeholder.show()
        self._form.hide()
        self.refresh()

    def _on_save(self):
        title = self._title_edit.text().strip()
        if not title:
            QMessageBox.warning(self, "提示", "标题不能为空")
            return
        lang = self._lang_combo.currentText()
        code = self._code_edit.toPlainText()
        desc = self._desc_edit.text().strip()
        if self._current_id is None:
            self._ctrl.add_snippet(title, lang, code, desc)
        else:
            self._ctrl.update_snippet(self._current_id, title, lang, code, desc)
        self.refresh()

    def _on_copy(self):
        QApplication.clipboard().setText(self._code_edit.toPlainText())
