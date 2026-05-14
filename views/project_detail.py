from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel,
    QLineEdit, QComboBox, QPushButton, QPlainTextEdit, QTextEdit,
    QSplitter, QColorDialog, QToolButton, QMenu, QAction, QSizePolicy
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from controllers.project_ctrl import ProjectCtrl

LANGUAGES = ["Python", "C++", "Java", "JavaScript", "TypeScript", "C#", "Go", "Rust", "HTML/CSS", "其他"]


class ProjectDetailWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._ctrl = ProjectCtrl()
        self._project = None
        self._build_ui()
        self._show_placeholder()

    def _build_ui(self):
        self._stack_layout = QVBoxLayout(self)
        self._stack_layout.setContentsMargins(8, 8, 8, 8)

        self._placeholder = QLabel("请在左侧选择项目")
        self._placeholder.setAlignment(Qt.AlignCenter)
        self._placeholder.setStyleSheet("color: #666; font-size: 16px;")
        self._stack_layout.addWidget(self._placeholder)

        self._content = QWidget()
        content_layout = QVBoxLayout(self._content)
        content_layout.setContentsMargins(0, 0, 0, 0)

        form = QFormLayout()
        self._name_edit = QLineEdit()
        self._path_edit = QLineEdit()
        self._path_edit.setReadOnly(True)
        self._type_label = QLabel()
        self._lang_combo = QComboBox()
        self._lang_combo.addItems(LANGUAGES)
        self._color_btn = QPushButton()
        self._color_btn.setFixedWidth(60)
        self._color_btn.clicked.connect(self._pick_color)
        self._memo_edit = QLineEdit()
        self._editor_combo = QComboBox()

        form.addRow("名称", self._name_edit)
        form.addRow("路径", self._path_edit)
        form.addRow("类型", self._type_label)
        form.addRow("语言", self._lang_combo)
        form.addRow("颜色", self._color_btn)
        form.addRow("备注", self._memo_edit)
        form.addRow("默认编辑器", self._editor_combo)
        content_layout.addLayout(form)

        note_splitter = QSplitter(Qt.Horizontal)
        self._note_edit = QPlainTextEdit()
        self._note_edit.setPlaceholderText("在此输入 Markdown 笔记...")
        self._note_preview = QTextEdit()
        self._note_preview.setReadOnly(True)
        self._note_edit.textChanged.connect(self._update_preview)
        note_splitter.addWidget(self._note_edit)
        note_splitter.addWidget(self._note_preview)
        note_splitter.setSizes([1, 1])
        content_layout.addWidget(note_splitter, stretch=1)

        btn_row = QHBoxLayout()
        self._save_btn = QPushButton("保存")
        self._save_btn.clicked.connect(self._on_save)
        self._open_btn = QToolButton()
        self._open_btn.setText("打开编辑器")
        self._open_btn.setPopupMode(QToolButton.MenuButtonPopup)
        self._open_btn.clicked.connect(self._open_default_editor)
        btn_row.addStretch()
        btn_row.addWidget(self._save_btn)
        btn_row.addWidget(self._open_btn)
        content_layout.addLayout(btn_row)

        self._stack_layout.addWidget(self._content)
        self._content.hide()

    def _show_placeholder(self):
        self._placeholder.show()
        self._content.hide()

    def load(self, project_id: int):
        p = self._ctrl.get_by_id(project_id)
        if not p:
            self._show_placeholder()
            return
        self._project = p
        self._name_edit.setText(p.get("name") or "")
        self._path_edit.setText(p.get("path") or "")
        self._type_label.setText("文件夹" if p.get("type") == "folder" else "单文件")
        lang = p.get("language") or "其他"
        idx = self._lang_combo.findText(lang)
        self._lang_combo.setCurrentIndex(idx if idx >= 0 else self._lang_combo.count() - 1)
        color = p.get("color") or "#4A90D9"
        self._color_btn.setStyleSheet(f"background-color: {color};")
        self._color_btn.setProperty("color", color)
        self._memo_edit.setText(p.get("memo") or "")
        self._note_edit.blockSignals(True)
        self._note_edit.setPlainText(p.get("note") or "")
        self._note_edit.blockSignals(False)
        self._update_preview()
        self._load_editors()
        self._placeholder.hide()
        self._content.show()

    def clear(self):
        self._project = None
        self._show_placeholder()

    def _update_preview(self):
        self._note_preview.setMarkdown(self._note_edit.toPlainText())

    def _pick_color(self):
        current = self._color_btn.property("color") or "#4A90D9"
        color = QColorDialog.getColor(QColor(current), self, "选择颜色")
        if color.isValid():
            hex_color = color.name()
            self._color_btn.setStyleSheet(f"background-color: {hex_color};")
            self._color_btn.setProperty("color", hex_color)

    def _load_editors(self):
        self._editor_combo.clear()
        menu = QMenu()
        if not self._project:
            self._open_btn.setMenu(menu)
            return
        editors = self._ctrl.get_editors_for_project(self._project)
        for e in editors:
            self._editor_combo.addItem(e.name, e.path)
            action = QAction(e.name, self)
            action.setData(e.path)
            action.triggered.connect(lambda checked, ep=e.path: self._open_with(ep))
            menu.addAction(action)
        self._open_btn.setMenu(menu)
        default = self._project.get("default_editor")
        if default:
            for i in range(self._editor_combo.count()):
                if self._editor_combo.itemData(i) == default:
                    self._editor_combo.setCurrentIndex(i)
                    break

    def _on_save(self):
        if not self._project:
            return
        self._ctrl.update(
            self._project["id"],
            name=self._name_edit.text().strip(),
            language=self._lang_combo.currentText(),
            color=self._color_btn.property("color"),
            memo=self._memo_edit.text().strip(),
            note=self._note_edit.toPlainText(),
            default_editor=self._editor_combo.currentData(),
        )
        self._project = self._ctrl.get_by_id(self._project["id"])

    def _open_default_editor(self):
        if not self._project:
            return
        path = self._editor_combo.currentData()
        if path:
            self._open_with(path)

    def _open_with(self, editor_path: str):
        if self._project and editor_path:
            self._ctrl.open_in_editor(self._project, editor_path)
