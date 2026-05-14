# 项目管理模块 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现项目管理模块：左侧项目列表（语言筛选+最近打开排序）+ 右侧详情表单 + Markdown 笔记编辑器 + 自动检测编辑器一键打开。

**Architecture:** MVC 分层，ProjectCtrl 负责所有 DB 操作，ProjectListWidget 和 ProjectDetailWidget 各自独立通过 pyqtSignal 解耦，ProjectsView 作为 QSplitter 容器组合两者。

**Tech Stack:** Python 3.9, PyQt5 5.15.9, SQLite (sqlite3), winreg (注册表扫描), subprocess (启动编辑器)

---

## 文件结构

**新增文件：**
- `views/project_list.py` — 左侧列表组件
- `views/project_detail.py` — 右侧详情 + 笔记编辑器
- `utils/editor_detector.py` — 扫描已安装编辑器

**修改文件：**
- `core/database.py` — 迁移添加 color、memo 字段
- `utils/language_detector.py` — 实现语言识别
- `controllers/project_ctrl.py` — 实现 CRUD + 编辑器启动
- `views/projects.py` — 替换占位为 QSplitter 容器

---

### Task 1: 数据库迁移

**Files:**
- Modify: `core/database.py`

- [ ] **Step 1: 添加迁移代码**

在 `core/database.py` 的 `init_db()` 中，`conn.cursor().executescript(...)` 之后、`finally:` 之前插入：

```python
        cur = conn.cursor()
        for col, definition in [
            ("color", "TEXT DEFAULT '#4A90D9'"),
            ("memo",  "TEXT DEFAULT ''"),
        ]:
            try:
                cur.execute(f"ALTER TABLE projects ADD COLUMN {col} {definition}")
                conn.commit()
            except Exception:
                pass
```

- [ ] **Step 2: 验证**

```bash
python -c "from core.database import init_db, get_connection; init_db(); conn = get_connection(); print([d[1] for d in conn.execute('PRAGMA table_info(projects)').fetchall()]); conn.close()"
```

预期输出末尾包含 `'color', 'memo'`。

- [ ] **Step 3: Commit**

```bash
git add core/database.py
git commit -m "feat: 迁移 projects 表添加 color 和 memo 字段"
```

---

### Task 2: LanguageDetector 实现

**Files:**
- Modify: `utils/language_detector.py`

- [ ] **Step 1: 替换全部内容**

```python
import os

_EXT_MAP = {
    ".py": "Python",
    ".cpp": "C++", ".cc": "C++", ".cxx": "C++", ".h": "C++", ".hpp": "C++",
    ".java": "Java",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".cs": "C#",
    ".go": "Go",
    ".rs": "Rust",
    ".html": "HTML/CSS", ".css": "HTML/CSS",
}

def detect_language(path: str) -> str:
    if os.path.isfile(path):
        return _EXT_MAP.get(os.path.splitext(path)[1].lower(), "其他")
    counts = {}
    try:
        for entry in os.scandir(path):
            if entry.is_file():
                lang = _EXT_MAP.get(os.path.splitext(entry.name)[1].lower())
                if lang:
                    counts[lang] = counts.get(lang, 0) + 1
    except OSError:
        pass
    return max(counts, key=counts.get) if counts else "其他"
```

- [ ] **Step 2: 验证**

```bash
python -c "from utils.language_detector import detect_language; print(detect_language('.'))"
```

预期输出 `Python`。

- [ ] **Step 3: Commit**

```bash
git add utils/language_detector.py
git commit -m "feat: 实现 LanguageDetector 语言识别"
```

---

### Task 3: EditorDetector 实现

**Files:**
- Create: `utils/editor_detector.py`

- [ ] **Step 1: 创建文件**

```python
import os
import winreg
from collections import namedtuple

EditorInfo = namedtuple("EditorInfo", ["name", "path"])

_TARGETS = {
    "Code.exe":       "VS Code",
    "Cursor.exe":     "Cursor",
    "pycharm64.exe":  "PyCharm",
    "qtcreator.exe":  "Qt Creator",
    "devenv.exe":     "Visual Studio",
    "notepad++.exe":  "Notepad++",
}

_LANG_PRIORITY = {
    "Python":     ["PyCharm", "VS Code", "Cursor"],
    "C++":        ["Qt Creator", "Visual Studio", "VS Code"],
    "JavaScript": ["VS Code", "Cursor"],
    "TypeScript": ["VS Code", "Cursor"],
}
_DEFAULT_PRIORITY = ["VS Code", "Cursor", "Notepad++"]


def _scan_dirs() -> dict:
    found = {}
    roots = [
        os.environ.get("PROGRAMFILES", "C:/Program Files"),
        os.environ.get("PROGRAMFILES(X86)", "C:/Program Files (x86)"),
        os.environ.get("LOCALAPPDATA", ""),
    ]
    for root in roots:
        if not root or not os.path.isdir(root):
            continue
        try:
            for entry in os.scandir(root):
                if not entry.is_dir():
                    continue
                for exe, name in _TARGETS.items():
                    candidate = os.path.join(entry.path, exe)
                    if os.path.isfile(candidate) and name not in found:
                        found[name] = candidate
        except OSError:
            pass
    return found


def _scan_registry() -> dict:
    found = {}
    try:
        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths"
        )
        i = 0
        while True:
            try:
                subname = winreg.EnumKey(key, i)
                i += 1
                for exe, name in _TARGETS.items():
                    if subname.lower() == exe.lower():
                        sub = winreg.OpenKey(key, subname)
                        val, _ = winreg.QueryValueEx(sub, "")
                        if val and os.path.isfile(val) and name not in found:
                            found[name] = val
                        winreg.CloseKey(sub)
            except OSError:
                break
        winreg.CloseKey(key)
    except OSError:
        pass
    return found


def scan() -> dict:
    found = _scan_dirs()
    found.update(_scan_registry())
    return found


def get_editors_for_language(language: str, settings_editor_map: dict = None) -> list:
    found = scan()
    priority = (
        (settings_editor_map or {}).get(language)
        or _LANG_PRIORITY.get(language, _DEFAULT_PRIORITY)
    )
    result = [EditorInfo(name, found[name]) for name in priority if name in found]
    for name, path in found.items():
        if not any(e.name == name for e in result):
            result.append(EditorInfo(name, path))
    return result
```

- [ ] **Step 2: 验证**

```bash
python -c "from utils.editor_detector import scan; print(scan())"
```

预期：打印出机器上已安装编辑器的字典，如 `{'VS Code': 'C:/...', 'Cursor': 'C:/...'}`。

- [ ] **Step 3: Commit**

```bash
git add utils/editor_detector.py
git commit -m "feat: 实现 EditorDetector 扫描已安装编辑器"
```

---

### Task 4: ProjectCtrl 实现

**Files:**
- Modify: `controllers/project_ctrl.py`

- [ ] **Step 1: 替换全部内容**

```python
import subprocess
from datetime import datetime
from core.database import get_connection
from utils.language_detector import detect_language
from utils.editor_detector import get_editors_for_language
from core.settings import Settings


class ProjectCtrl:

    def get_all(self, language_filter: str = None) -> list:
        conn = get_connection()
        try:
            if language_filter and language_filter != "全部":
                rows = conn.execute(
                    "SELECT * FROM projects WHERE language=? ORDER BY last_opened_at DESC NULLS LAST",
                    (language_filter,)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM projects ORDER BY last_opened_at DESC"
                ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get_by_id(self, project_id: int) -> dict:
        conn = get_connection()
        try:
            row = conn.execute(
                "SELECT * FROM projects WHERE id=?", (project_id,)
            ).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def add(self, name: str, path: str, type_: str) -> int:
        language = detect_language(path)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = get_connection()
        try:
            cur = conn.execute(
                "INSERT INTO projects (name, path, type, language, created_at) VALUES (?,?,?,?,?)",
                (name, path, type_, language, now)
            )
            conn.commit()
            return cur.lastrowid
        finally:
            conn.close()

    def update(self, project_id: int, **fields) -> None:
        allowed = {"name", "language", "color", "memo", "note", "default_editor"}
        data = {k: v for k, v in fields.items() if k in allowed}
        if not data:
            return
        sets = ", ".join(f"{k}=?" for k in data)
        conn = get_connection()
        try:
            conn.execute(
                f"UPDATE projects SET {sets} WHERE id=?",
                (*data.values(), project_id)
            )
            conn.commit()
        finally:
            conn.close()

    def delete(self, project_id: int) -> None:
        conn = get_connection()
        try:
            conn.execute("DELETE FROM projects WHERE id=?", (project_id,))
            conn.commit()
        finally:
            conn.close()

    def open_in_editor(self, project: dict, editor_path: str) -> None:
        subprocess.Popen([editor_path, project["path"]])
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = get_connection()
        try:
            conn.execute(
                "UPDATE projects SET last_opened_at=? WHERE id=?",
                (now, project["id"])
            )
            conn.commit()
        finally:
            conn.close()

    def get_editors_for_project(self, project: dict) -> list:
        settings = Settings()
        editor_map = settings.get("editor_map") or {}
        return get_editors_for_language(project.get("language", ""), editor_map)
```

- [ ] **Step 2: 验证导入**

```bash
python -c "from controllers.project_ctrl import ProjectCtrl; print('ok')"
```

预期输出 `ok`。

- [ ] **Step 3: Commit**

```bash
git add controllers/project_ctrl.py
git commit -m "feat: 实现 ProjectCtrl CRUD 与编辑器启动"
```

---

### Task 5: ProjectListWidget

**Files:**
- Create: `views/project_list.py`

- [ ] **Step 1: 创建文件**

```python
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
```

- [ ] **Step 2: 验证导入**

```bash
python -c "from views.project_list import ProjectListWidget; print('ok')"
```

预期输出 `ok`。

- [ ] **Step 3: Commit**

```bash
git add views/project_list.py
git commit -m "feat: 实现 ProjectListWidget 左侧项目列表"
```

---

### Task 6: ProjectDetailWidget

**Files:**
- Create: `views/project_detail.py`

- [ ] **Step 1: 创建文件**

```python
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
        self._open_btn_menu = QMenu()
        if not self._project:
            return
        editors = self._ctrl.get_editors_for_project(self._project)
        for e in editors:
            self._editor_combo.addItem(e.name, e.path)
            action = QAction(e.name, self)
            action.setData(e.path)
            action.triggered.connect(lambda checked, ep=e.path: self._open_with(ep))
            self._open_btn_menu.addAction(action)
        self._open_btn.setMenu(self._open_btn_menu)
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
```

- [ ] **Step 2: 验证导入**

```bash
python -c "from views.project_detail import ProjectDetailWidget; print('ok')"
```

预期输出 `ok`。

- [ ] **Step 3: Commit**

```bash
git add views/project_detail.py
git commit -m "feat: 实现 ProjectDetailWidget 详情面板与笔记编辑器"
```

---

### Task 7: ProjectsView 容器组装

**Files:**
- Modify: `views/projects.py`

- [ ] **Step 1: 替换 projects.py 全部内容**

```python
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QSplitter
from PyQt5.QtCore import Qt
from views.project_list import ProjectListWidget
from views.project_detail import ProjectDetailWidget


class ProjectsView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Horizontal)
        self._list = ProjectListWidget()
        self._detail = ProjectDetailWidget()

        splitter.addWidget(self._list)
        splitter.addWidget(self._detail)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        layout.addWidget(splitter)

        self._list.project_selected.connect(self._detail.load)
        self._list.project_deleted.connect(self._detail.clear)
```

- [ ] **Step 2: 验证导入**

```bash
python -c "from views.projects import ProjectsView; print('ok')"
```

预期输出 `ok`。

- [ ] **Step 3: Commit**

```bash
git add views/projects.py
git commit -m "feat: 组装 ProjectsView QSplitter 容器"
```

---

### Task 8: 端到端验证

- [ ] **Step 1: 启动应用**

```bash
python main.py
```

验证：
- 应用正常启动，无报错
- 切换到"项目管理"标签，左侧显示列表（初始为空），右侧显示"请在左侧选择项目"
- 点击"添加项目"，选择一个文件夹，列表出现新条目
- 点击条目，右侧详情面板填充数据，笔记区可编辑，右侧实时预览 Markdown
- 修改字段后点"保存"，重新点击条目确认数据已持久化
- 点"打开编辑器"按钮，若检测到编辑器则启动，否则按钮菜单为空
- 点"删除"，确认后条目消失，右侧回到占位提示

- [ ] **Step 2: Commit**

```bash
git add .
git commit -m "feat: P0 项目管理模块完成"
```
