# 开发者工作台骨架框架 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 搭建可运行的 PyQt5 应用骨架：主窗口 + 顶部标签导航 + 8 个占位模块视图 + 深色主题 + SQLite 数据库初始化。

**Architecture:** MVC 分层架构，`core/` 负责数据库和配置，`models/` 定义数据类，`views/` 包含主窗口和各模块占位视图，`controllers/` 和 `utils/` 为空壳。主窗口使用 `QTabWidget` 顶部标签栏切换 `QStackedWidget` 内容区。

**Tech Stack:** Python 3.9, PyQt5 5.15.9, QtAwesome 1.0.3, SQLite (内置 sqlite3)

---

## 文件结构

**新建文件：**
- `main.py` — 程序入口，初始化数据库、加载主题、启动主窗口
- `requirements.txt` — 依赖列表
- `assets/themes/dark.qss` — 深色主题样式表
- `assets/themes/light.qss` — 浅色主题占位文件
- `core/__init__.py`
- `core/database.py` — SQLite 连接与建表
- `core/settings.py` — 全局配置单例
- `models/__init__.py`
- `models/project.py` — 项目数据类
- `models/snippet.py` — 代码片段数据类
- `models/todo.py` — TODO 数据类
- `models/study_log.py` — 学习记录数据类
- `models/tag.py` — 标签数据类
- `views/__init__.py`
- `views/main_window.py` — 主窗口
- `views/overview.py` — 今日概览占位
- `views/projects.py` — 项目管理占位
- `views/snippets.py` — 代码片段库占位
- `views/todos.py` — TODO 看板占位
- `views/stats.py` — 学习统计占位
- `views/launcher.py` — 快速启动占位
- `views/capture.py` — 网络抓包占位
- `views/tags.py` — 知识标签占位
- `controllers/__init__.py`
- `controllers/project_ctrl.py`
- `controllers/snippet_ctrl.py`
- `controllers/todo_ctrl.py`
- `controllers/timer_ctrl.py`
- `controllers/launcher_ctrl.py`
- `controllers/capture_ctrl.py`
- `utils/__init__.py`
- `utils/language_detector.py`
- `utils/app_scanner.py`
- `utils/fuzzy_matcher.py`
- `utils/backup.py`

---

### Task 1: 目录结构与 requirements.txt

**Files:**
- Create: `requirements.txt`
- Create: `core/__init__.py`
- Create: `models/__init__.py`
- Create: `views/__init__.py`
- Create: `controllers/__init__.py`
- Create: `utils/__init__.py`
- Create: `assets/themes/dark.qss` (空占位)
- Create: `assets/themes/light.qss` (空占位)

- [ ] **Step 1: 创建目录结构**

```bash
mkdir -p assets/themes core models views controllers utils data
touch core/__init__.py models/__init__.py views/__init__.py controllers/__init__.py utils/__init__.py
touch assets/themes/dark.qss assets/themes/light.qss
```

- [ ] **Step 2: 写 requirements.txt**

```
PyQt5==5.15.9
QtAwesome==1.0.3
matplotlib==3.8.3
Pillow==9.2.0
psutil==5.9.0
rapidfuzz
```

- [ ] **Step 3: 验证目录结构**

```bash
find . -type f -name "*.py" -o -name "*.txt" -o -name "*.qss" | grep -v ".git" | sort
```

期望输出包含所有 `__init__.py`、`requirements.txt`、两个 `.qss` 文件。

- [ ] **Step 4: Commit**

```bash
git add requirements.txt core/__init__.py models/__init__.py views/__init__.py controllers/__init__.py utils/__init__.py assets/
git commit -m "chore: 初始化目录结构"
```

---

### Task 2: 数据库初始化 (core/database.py)

**Files:**
- Create: `core/database.py`

- [ ] **Step 1: 写 core/database.py**

```python
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "devhub.db")

def get_connection() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS projects (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            name            TEXT NOT NULL,
            path            TEXT NOT NULL,
            type            TEXT NOT NULL CHECK(type IN ('folder', 'file')),
            language        TEXT,
            note            TEXT,
            content         TEXT,
            default_editor  TEXT,
            created_at      TEXT DEFAULT (datetime('now', 'localtime')),
            last_opened_at  TEXT
        );

        CREATE TABLE IF NOT EXISTS snippets (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            title       TEXT NOT NULL,
            language    TEXT,
            code        TEXT,
            description TEXT,
            project_id  INTEGER REFERENCES projects(id) ON DELETE SET NULL,
            created_at  TEXT DEFAULT (datetime('now', 'localtime'))
        );

        CREATE TABLE IF NOT EXISTS todos (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id  INTEGER REFERENCES projects(id) ON DELETE CASCADE,
            title       TEXT NOT NULL,
            description TEXT,
            status      TEXT DEFAULT 'todo' CHECK(status IN ('todo', 'doing', 'done')),
            priority    TEXT DEFAULT 'medium' CHECK(priority IN ('high', 'medium', 'low')),
            due_date    TEXT,
            created_at  TEXT DEFAULT (datetime('now', 'localtime'))
        );

        CREATE TABLE IF NOT EXISTS study_logs (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id       INTEGER REFERENCES projects(id) ON DELETE SET NULL,
            duration_minutes INTEGER NOT NULL,
            date             TEXT NOT NULL,
            created_at       TEXT DEFAULT (datetime('now', 'localtime'))
        );

        CREATE TABLE IF NOT EXISTS tags (
            id    INTEGER PRIMARY KEY AUTOINCREMENT,
            name  TEXT NOT NULL UNIQUE,
            color TEXT DEFAULT '#4A90D9'
        );

        CREATE TABLE IF NOT EXISTS note_tags (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            tag_id     INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
            UNIQUE(project_id, tag_id)
        );

        CREATE TABLE IF NOT EXISTS app_index (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            name            TEXT NOT NULL,
            path            TEXT NOT NULL,
            last_scanned_at TEXT DEFAULT (datetime('now', 'localtime'))
        );
    """)
    conn.commit()
    conn.close()
```

- [ ] **Step 2: 手动验证数据库初始化**

```bash
python -c "from core.database import init_db; init_db(); print('OK')"
```

期望输出：`OK`，且 `data/devhub.db` 文件被创建。

```bash
python -c "
from core.database import get_connection
conn = get_connection()
tables = conn.execute(\"SELECT name FROM sqlite_master WHERE type='table'\").fetchall()
print([t['name'] for t in tables])
"
```

期望输出：`['projects', 'snippets', 'todos', 'study_logs', 'tags', 'note_tags', 'app_index']`

- [ ] **Step 3: Commit**

```bash
git add core/database.py data/.gitkeep
git commit -m "feat: 数据库初始化，建所有表"
```

---

### Task 3: 全局配置 (core/settings.py)

**Files:**
- Create: `core/settings.py`

- [ ] **Step 1: 写 core/settings.py**

```python
import json
import os

_SETTINGS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "settings.json")

_DEFAULTS = {
    "theme": "dark",
    "default_editor": "",
    "db_path": os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "devhub.db"),
}

class Settings:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._data = dict(_DEFAULTS)
            cls._instance._load()
        return cls._instance

    def _load(self):
        if os.path.exists(_SETTINGS_PATH):
            with open(_SETTINGS_PATH, "r", encoding="utf-8") as f:
                self._data.update(json.load(f))

    def save(self):
        os.makedirs(os.path.dirname(_SETTINGS_PATH), exist_ok=True)
        with open(_SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)

    def get(self, key: str):
        return self._data.get(key)

    def set(self, key: str, value):
        self._data[key] = value
        self.save()
```

- [ ] **Step 2: 验证配置单例**

```bash
python -c "
from core.settings import Settings
s = Settings()
print(s.get('theme'))
s.set('theme', 'light')
s2 = Settings()
print(s2.get('theme'))
"
```

期望输出：
```
dark
light
```

- [ ] **Step 3: Commit**

```bash
git add core/settings.py
git commit -m "feat: 全局配置单例 Settings"
```

---

### Task 4: 数据模型 (models/)

**Files:**
- Create: `models/project.py`
- Create: `models/snippet.py`
- Create: `models/todo.py`
- Create: `models/study_log.py`
- Create: `models/tag.py`

- [ ] **Step 1: 写 models/project.py**

```python
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class Project:
    name: str
    path: str
    type: str  # 'folder' | 'file'
    id: Optional[int] = None
    language: Optional[str] = None
    note: Optional[str] = None
    content: Optional[str] = None
    default_editor: Optional[str] = None
    created_at: Optional[str] = None
    last_opened_at: Optional[str] = None
```

- [ ] **Step 2: 写 models/snippet.py**

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class Snippet:
    title: str
    id: Optional[int] = None
    language: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    project_id: Optional[int] = None
    created_at: Optional[str] = None
```

- [ ] **Step 3: 写 models/todo.py**

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class Todo:
    title: str
    id: Optional[int] = None
    project_id: Optional[int] = None
    description: Optional[str] = None
    status: str = "todo"  # 'todo' | 'doing' | 'done'
    priority: str = "medium"  # 'high' | 'medium' | 'low'
    due_date: Optional[str] = None
    created_at: Optional[str] = None
```

- [ ] **Step 4: 写 models/study_log.py**

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class StudyLog:
    duration_minutes: int
    date: str
    id: Optional[int] = None
    project_id: Optional[int] = None
    created_at: Optional[str] = None
```

- [ ] **Step 5: 写 models/tag.py**

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class Tag:
    name: str
    id: Optional[int] = None
    color: str = "#4A90D9"
```

- [ ] **Step 6: 验证模型可导入**

```bash
python -c "
from models.project import Project
from models.snippet import Snippet
from models.todo import Todo
from models.study_log import StudyLog
from models.tag import Tag
p = Project(name='test', path='/tmp', type='folder')
print(p)
"
```

期望输出：`Project(name='test', path='/tmp', type='folder', id=None, ...)`

- [ ] **Step 7: Commit**

```bash
git add models/
git commit -m "feat: 数据模型定义（Project/Snippet/Todo/StudyLog/Tag）"
```

---

### Task 5: 深色主题 QSS (assets/themes/dark.qss)

**Files:**
- Modify: `assets/themes/dark.qss`

- [ ] **Step 1: 写 dark.qss**

```css
/* ===== 全局 ===== */
QWidget {
    background-color: #1E1E1E;
    color: #D4D4D4;
    font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
    font-size: 13px;
}

/* ===== 主窗口 ===== */
QMainWindow {
    background-color: #1E1E1E;
}

/* ===== 标签栏 ===== */
QTabWidget::pane {
    border: none;
    background-color: #1E1E1E;
}

QTabBar {
    background-color: #252526;
}

QTabBar::tab {
    background-color: #252526;
    color: #9D9D9D;
    padding: 8px 20px;
    border: none;
    border-bottom: 2px solid transparent;
}

QTabBar::tab:selected {
    color: #D4D4D4;
    border-bottom: 2px solid #4A90D9;
    background-color: #1E1E1E;
}

QTabBar::tab:hover:!selected {
    color: #D4D4D4;
    background-color: #2D2D2D;
}

/* ===== 按钮 ===== */
QPushButton {
    background-color: #3C3C3C;
    color: #D4D4D4;
    border: 1px solid #555555;
    border-radius: 4px;
    padding: 5px 12px;
}

QPushButton:hover {
    background-color: #4A90D9;
    border-color: #4A90D9;
    color: #FFFFFF;
}

QPushButton:pressed {
    background-color: #357ABD;
}

/* ===== 输入框 ===== */
QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #2D2D2D;
    color: #D4D4D4;
    border: 1px solid #3C3C3C;
    border-radius: 4px;
    padding: 4px 8px;
    selection-background-color: #4A90D9;
}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border-color: #4A90D9;
}

/* ===== 列表 ===== */
QListWidget, QTreeWidget, QTableWidget {
    background-color: #252526;
    border: 1px solid #3C3C3C;
    alternate-background-color: #2A2A2A;
}

QListWidget::item:selected, QTreeWidget::item:selected, QTableWidget::item:selected {
    background-color: #094771;
    color: #FFFFFF;
}

QListWidget::item:hover, QTreeWidget::item:hover {
    background-color: #2D2D2D;
}

/* ===== 滚动条 ===== */
QScrollBar:vertical {
    background-color: #1E1E1E;
    width: 8px;
    border: none;
}

QScrollBar::handle:vertical {
    background-color: #424242;
    border-radius: 4px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background-color: #686868;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    background-color: #1E1E1E;
    height: 8px;
    border: none;
}

QScrollBar::handle:horizontal {
    background-color: #424242;
    border-radius: 4px;
    min-width: 20px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #686868;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

/* ===== 菜单 ===== */
QMenuBar {
    background-color: #252526;
    color: #D4D4D4;
}

QMenuBar::item:selected {
    background-color: #3C3C3C;
}

QMenu {
    background-color: #252526;
    border: 1px solid #3C3C3C;
}

QMenu::item:selected {
    background-color: #094771;
}

/* ===== 状态栏 ===== */
QStatusBar {
    background-color: #007ACC;
    color: #FFFFFF;
    font-size: 12px;
}

/* ===== 分割线 ===== */
QFrame[frameShape="4"], QFrame[frameShape="5"] {
    color: #3C3C3C;
}

/* ===== 标签文字 ===== */
QLabel {
    color: #D4D4D4;
    background-color: transparent;
}
```

- [ ] **Step 2: Commit**

```bash
git add assets/themes/dark.qss assets/themes/light.qss
git commit -m "feat: 深色主题 QSS"
```

---

### Task 6: 占位视图 (views/)

**Files:**
- Create: `views/overview.py`
- Create: `views/projects.py`
- Create: `views/snippets.py`
- Create: `views/todos.py`
- Create: `views/stats.py`
- Create: `views/launcher.py`
- Create: `views/capture.py`
- Create: `views/tags.py`

- [ ] **Step 1: 写所有占位视图**

每个文件结构相同，以 `views/overview.py` 为例：

```python
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt

class OverviewView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        label = QLabel("今日概览")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size: 24px; color: #4A90D9;")
        layout.addWidget(label)
```

`views/projects.py` — 类名 `ProjectsView`，标签文字 `"项目管理"`

`views/snippets.py` — 类名 `SnippetsView`，标签文字 `"代码片段库"`

`views/todos.py` — 类名 `TodosView`，标签文字 `"TODO 看板"`

`views/stats.py` — 类名 `StatsView`，标签文字 `"学习统计"`

`views/launcher.py` — 类名 `LauncherView`，标签文字 `"快速启动"`

`views/capture.py` — 类名 `CaptureView`，标签文字 `"网络抓包"`

`views/tags.py` — 类名 `TagsView`，标签文字 `"知识标签"`

- [ ] **Step 2: 验证可导入**

```bash
python -c "
from views.overview import OverviewView
from views.projects import ProjectsView
from views.snippets import SnippetsView
from views.todos import TodosView
from views.stats import StatsView
from views.launcher import LauncherView
from views.capture import CaptureView
from views.tags import TagsView
print('all views imported OK')
"
```

期望输出：`all views imported OK`

- [ ] **Step 3: Commit**

```bash
git add views/
git commit -m "feat: 8 个占位模块视图"
```

---

### Task 7: 主窗口 (views/main_window.py)

**Files:**
- Create: `views/main_window.py`

- [ ] **Step 1: 写 views/main_window.py**

```python
from PyQt5.QtWidgets import QMainWindow, QTabWidget, QStackedWidget, QWidget
from PyQt5.QtCore import Qt

from views.overview import OverviewView
from views.projects import ProjectsView
from views.snippets import SnippetsView
from views.todos import TodosView
from views.stats import StatsView
from views.launcher import LauncherView
from views.capture import CaptureView
from views.tags import TagsView


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("开发者工作台")
        self.setMinimumSize(1200, 700)
        self.resize(1400, 800)

        self._tabs = QTabWidget()
        self._tabs.setTabPosition(QTabWidget.North)
        self._tabs.setDocumentMode(True)

        self._views = [
            ("今日概览", OverviewView()),
            ("项目管理", ProjectsView()),
            ("代码片段库", SnippetsView()),
            ("TODO 看板", TodosView()),
            ("学习统计", StatsView()),
            ("快速启动", LauncherView()),
            ("网络抓包", CaptureView()),
            ("知识标签", TagsView()),
        ]

        for name, view in self._views:
            self._tabs.addTab(view, name)

        self.setCentralWidget(self._tabs)
        self.statusBar().showMessage("就绪")
```

- [ ] **Step 2: Commit**

```bash
git add views/main_window.py
git commit -m "feat: 主窗口，顶部标签导航 + 8 个模块视图"
```

---

### Task 8: 控制器与工具类空壳

**Files:**
- Create: `controllers/project_ctrl.py`
- Create: `controllers/snippet_ctrl.py`
- Create: `controllers/todo_ctrl.py`
- Create: `controllers/timer_ctrl.py`
- Create: `controllers/launcher_ctrl.py`
- Create: `controllers/capture_ctrl.py`
- Create: `utils/language_detector.py`
- Create: `utils/app_scanner.py`
- Create: `utils/fuzzy_matcher.py`
- Create: `utils/backup.py`

- [ ] **Step 1: 写控制器空壳**

`controllers/project_ctrl.py`:
```python
class ProjectController:
    def list_projects(self):
        pass

    def add_project(self, project):
        pass

    def update_project(self, project):
        pass

    def delete_project(self, project_id: int):
        pass

    def open_project(self, project_id: int):
        pass
```

`controllers/snippet_ctrl.py`:
```python
class SnippetController:
    def list_snippets(self):
        pass

    def add_snippet(self, snippet):
        pass

    def update_snippet(self, snippet):
        pass

    def delete_snippet(self, snippet_id: int):
        pass
```

`controllers/todo_ctrl.py`:
```python
class TodoController:
    def list_todos(self, project_id: int = None):
        pass

    def add_todo(self, todo):
        pass

    def update_todo(self, todo):
        pass

    def delete_todo(self, todo_id: int):
        pass

    def move_todo(self, todo_id: int, status: str):
        pass
```

`controllers/timer_ctrl.py`:
```python
class TimerController:
    def start_timer(self, project_id: int, duration_minutes: int):
        pass

    def stop_timer(self):
        pass

    def log_session(self, project_id: int, duration_minutes: int):
        pass
```

`controllers/launcher_ctrl.py`:
```python
class LauncherController:
    def scan_apps(self):
        pass

    def search(self, query: str):
        pass

    def launch(self, app_path: str):
        pass
```

`controllers/capture_ctrl.py`:
```python
class CaptureController:
    def start_capture(self, interface: str, filter_ip: str = None):
        pass

    def stop_capture(self):
        pass

    def export_pcap(self, path: str):
        pass
```

- [ ] **Step 2: 写工具类空壳**

`utils/language_detector.py`:
```python
def detect_language(path: str) -> str:
    """扫描路径，返回主要编程语言名称。"""
    pass
```

`utils/app_scanner.py`:
```python
def scan_apps() -> list:
    """扫描系统程序，返回 {'name': str, 'path': str} 列表。"""
    pass
```

`utils/fuzzy_matcher.py`:
```python
def match(query: str, candidates: list, limit: int = 10) -> list:
    """模糊匹配，返回 Top N 结果列表。"""
    pass
```

`utils/backup.py`:
```python
def export_backup(output_path: str):
    """导出全部数据为 JSON 文件。"""
    pass

def import_backup(input_path: str):
    """从 JSON 备份文件恢复数据。"""
    pass
```

- [ ] **Step 3: Commit**

```bash
git add controllers/ utils/
git commit -m "feat: 控制器与工具类空壳"
```

---

### Task 9: 程序入口 (main.py)

**Files:**
- Create: `main.py`

- [ ] **Step 1: 写 main.py**

```python
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
```

- [ ] **Step 2: 运行程序验证**

```bash
python main.py
```

期望：主窗口弹出，顶部显示 8 个标签，深色主题，点击标签切换显示对应模块名称，状态栏显示"就绪"。

- [ ] **Step 3: Commit**

```bash
git add main.py
git commit -m "feat: 程序入口，骨架框架完成"
```

---

### Task 10: 添加 data/.gitkeep

**Files:**
- Create: `data/.gitkeep`

- [ ] **Step 1: 确保 data/ 目录被 git 追踪但 db 文件被忽略**

检查 `.gitignore` 是否已包含 `data/devhub.db` 和 `data/settings.json`：

```bash
cat .gitignore
```

如果没有，追加：

```
data/devhub.db
data/settings.json
```

创建 `.gitkeep`：

```bash
touch data/.gitkeep
```

- [ ] **Step 2: Commit**

```bash
git add .gitignore data/.gitkeep
git commit -m "chore: 忽略运行时数据文件，保留 data/ 目录"
```
