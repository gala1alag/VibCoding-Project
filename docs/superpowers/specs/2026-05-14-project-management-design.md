# 项目管理模块设计文档

**日期：** 2026-05-14
**范围：** P0 — 项目管理模块（`views/projects.py` 及相关文件）

---

## 一、目标

实现项目管理模块完整功能：左侧项目列表（按语言筛选 + 按最近打开排序）+ 右侧详情面板（表单 + Markdown 笔记编辑器）+ 一键用自动检测编辑器打开项目。

---

## 二、文件结构

**新增文件：**
- `views/project_list.py` — 左侧列表组件
- `views/project_detail.py` — 右侧详情 + 笔记编辑器组件
- `utils/editor_detector.py` — 扫描已安装编辑器，按语言推荐

**修改文件：**
- `views/projects.py` — 主容器，`QSplitter` 组合左右两个组件
- `controllers/project_ctrl.py` — 实现 CRUD + 编辑器启动
- `utils/language_detector.py` — 实现语言识别逻辑
- `core/database.py` — 迁移添加 `color`、`memo` 字段

---

## 三、数据库 Schema

使用现有 `projects` 表，通过 `ALTER TABLE ADD COLUMN` 迁移添加两个字段：

```sql
-- 现有字段（不变）
id, name, path, type, language, note, content, default_editor, created_at, last_opened_at

-- 新增字段（迁移）
color  TEXT DEFAULT '#4A90D9'   -- 颜色标签（十六进制）
memo   TEXT DEFAULT ''          -- 单行短备注
```

字段语义：
- `note` — Markdown 笔记内容（长文本）
- `memo` — 单行短备注
- `content` — 保留不动（历史字段，不使用）
- `color` — 项目颜色标签，列表中显示为彩色圆点

迁移方式：`init_db()` 中用 `ALTER TABLE projects ADD COLUMN` + `try/except`（SQLite 不支持 `IF NOT EXISTS`）。

---

## 四、架构与组件

### 4.1 ProjectsView（主容器）

`views/projects.py`

- `QSplitter(Qt.Horizontal)`，左右比例 1:2
- 左：`ProjectListWidget`
- 右：`ProjectDetailWidget`
- 连接信号：`list.project_selected → detail.load(project_id)`

### 4.2 ProjectListWidget（左侧）

`views/project_list.py`

布局（从上到下）：
1. 语言筛选 `QComboBox`（全部 / C++ / Python / Java / JavaScript / TypeScript / C# / Go / Rust / HTML/CSS / 其他）
2. `QListWidget` — 每项显示：彩色圆点 + 项目名 + 语言标签
3. 底部按钮行：添加 + 删除

行为：
- 列表按 `last_opened_at` 降序排列（NULL 排最后）
- 点击"添加"→ `QFileDialog` 选文件夹或文件 → `ProjectCtrl.add()` → 刷新列表
- 点击"删除"→ 确认对话框 → `ProjectCtrl.delete()` → 清空详情
- 语言筛选变化 → 重新查询列表

信号：
- `project_selected = pyqtSignal(int)` — 发出 project_id

### 4.3 ProjectDetailWidget（右侧）

`views/project_detail.py`

布局（从上到下）：
1. **表单区**（`QFormLayout`）：
   - 名称（`QLineEdit`）
   - 路径（`QLineEdit`，只读）
   - 类型（只读标签：文件夹 / 单文件）
   - 语言（`QComboBox`，可手动修改）
   - 颜色（`QPushButton` 点击弹 `QColorDialog`，按钮背景色预览）
   - 备注（`QLineEdit`，单行）
   - 默认编辑器（`QComboBox`，由 `EditorDetector` 填充）
2. **笔记区**（`QSplitter(Qt.Horizontal)`）：
   - 左：`QPlainTextEdit`（编辑）
   - 右：`QTextEdit`（只读，`setMarkdown()` 实时预览）
3. **底部按钮行**：保存 + 打开编辑器（`QToolButton` + 下拉菜单列出所有检测到的编辑器）

行为：
- `load(project_id)` — 从 DB 读取并填充所有字段
- 笔记编辑区 `textChanged` → 实时调用右侧 `setMarkdown()`
- 保存 → `ProjectCtrl.update()`
- 打开编辑器 → `ProjectCtrl.open_in_editor(project, editor_path)` → 更新 `last_opened_at`
- 无选中项时显示空白占位提示

### 4.4 ProjectCtrl

`controllers/project_ctrl.py`

```python
def get_all(language_filter=None) -> list[dict]
def add(name, path, type_) -> int          # 返回新 id，自动识别语言
def update(project_id, **fields) -> None
def delete(project_id) -> None
def open_in_editor(project: dict, editor_path: str) -> None  # subprocess.Popen + 更新 last_opened_at
def get_editors_for_project(project: dict) -> list[EditorInfo]  # 调用 EditorDetector
```

### 4.5 EditorDetector

`utils/editor_detector.py`

扫描路径：
- `C:/Program Files`、`C:/Program Files (x86)`（一级子目录）
- `%LOCALAPPDATA%`（一级子目录）
- 注册表 `HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths`

目标编辑器：VS Code (`Code.exe`)、Cursor (`Cursor.exe`)、PyCharm (`pycharm64.exe`)、Qt Creator (`qtcreator.exe`)、Visual Studio (`devenv.exe`)、Notepad++ (`notepad++.exe`)

语言→编辑器默认优先级映射：
```
Python      → PyCharm > VS Code > Cursor
C++         → Qt Creator > Visual Studio > VS Code
JavaScript/TypeScript → VS Code > Cursor
其他        → VS Code > Cursor > Notepad++
```

返回 `list[EditorInfo]`，`EditorInfo = namedtuple('EditorInfo', ['name', 'path'])`

用户可在 `data/settings.json` 中覆盖映射（`editor_map` 键）。

### 4.6 LanguageDetector

`utils/language_detector.py`

- 单文件：直接按扩展名映射
- 文件夹：扫描一级目录所有文件扩展名，取占比最高的语言
- 扩展名映射表：`.py→Python`、`.cpp/.h/.cc→C++`、`.java→Java`、`.js→JavaScript`、`.ts→TypeScript`、`.cs→C#`、`.go→Go`、`.rs→Rust`、`.html/.css→HTML/CSS`、其他→`其他`

---

## 五、数据流

```
用户点击项目
  → ProjectListWidget.project_selected(id)
  → ProjectDetailWidget.load(id)
  → ProjectCtrl.get_all() / DB query

用户点"添加"
  → QFileDialog → 选路径
  → ProjectCtrl.add() → LanguageDetector.detect()
  → DB INSERT → ProjectListWidget.refresh()

用户点"保存"
  → ProjectDetailWidget 收集表单值
  → ProjectCtrl.update() → DB UPDATE

用户点"打开编辑器"
  → ProjectCtrl.open_in_editor()
  → subprocess.Popen(editor_path, project_path)
  → DB UPDATE last_opened_at
  → ProjectListWidget.refresh()（排序更新）
```

---

## 六、不在本次范围内

- 学习计时器（P2）
- 笔记导出 PDF/HTML（P1）
- 全局搜索（P1）
- 项目活跃度排行（仅按 last_opened_at 排序，不做专门排行页）
