# 开发者工作台 — 项目开发 Prompt 文档

**版本：** v1.0  
**日期：** 2026-04-29  
**用途：** 向 AI 编程助手描述项目背景、技术约束和开发任务，确保每次对话都能快速进入状态

---

## 一、项目背景

你正在帮我开发一个名为**开发者工作台**的 Windows 桌面应用。

这是一个面向个人开发者的本地工具，将代码项目管理、学习笔记、快速启动、网络抓包等功能整合进同一个界面，数据全部本地 SQLite 存储，完全离线可用，不依赖任何云服务。

---

## 二、技术栈（固定，不得更改）

| 层级 | 技术 | 版本 |
|------|------|------|
| 界面框架 | PyQt5 | 5.15.9 |
| 图标库 | QtAwesome | 1.0.3 |
| 图表渲染 | matplotlib | 3.8.3 |
| 图片处理 | Pillow | 9.2.0 |
| 系统信息 | psutil | 5.9.0 |
| 数据存储 | SQLite（sqlite3） | 内置 |
| 模糊匹配 | rapidfuzz | latest |
| 网络抓包 | scapy + pyshark | latest |
| 运行环境 | Python | 3.9.13 |
| 操作系统 | Windows 10/11 | — |

**不要引入上表以外的第三方库。**

---

## 三、架构约束

- 采用 **MVC 三层架构**，严格分离 View / Controller / Model
- 目录结构如下，新文件必须放在对应目录：

```
开发者工作台/
├── main.py                  # 程序入口
├── requirements.txt
├── data/
│   └── devhub.db            # SQLite 数据库
├── assets/
│   ├── icons/
│   ├── theme_dark.qss
│   └── theme_light.qss
├── core/
│   ├── database.py          # 数据库连接与初始化
│   └── settings.py          # 全局配置
├── models/
│   ├── project.py
│   ├── snippet.py
│   ├── todo.py
│   ├── study_log.py
│   └── tag.py
├── views/
│   ├── main_window.py       # 主窗口（导航栏 + 内容区）
│   ├── overview.py
│   ├── projects.py
│   ├── snippets.py
│   ├── todos.py
│   ├── timer.py
│   ├── tags.py
│   ├── launcher.py
│   ├── capture.py
│   ├── stats.py
│   └── leetcode.py
├── controllers/
│   ├── project_ctrl.py
│   ├── snippet_ctrl.py
│   ├── todo_ctrl.py
│   ├── timer_ctrl.py
│   ├── launcher_ctrl.py
│   ├── capture_ctrl.py
│   └── leetcode_ctrl.py
└── utils/
    ├── language_detector.py
    ├── app_scanner.py
    ├── fuzzy_matcher.py
    └── backup.py
```

---

## 四、数据库设计

数据库文件：`data/devhub.db`

```sql
-- 项目与单文件
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

-- 代码片段
CREATE TABLE IF NOT EXISTS snippets (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT NOT NULL,
    language    TEXT,
    code        TEXT,
    description TEXT,
    project_id  INTEGER REFERENCES projects(id) ON DELETE SET NULL,
    created_at  TEXT DEFAULT (datetime('now', 'localtime'))
);

-- TODO 任务
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

-- 学习记录
CREATE TABLE IF NOT EXISTS study_logs (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id       INTEGER REFERENCES projects(id) ON DELETE SET NULL,
    duration_minutes INTEGER NOT NULL,
    date             TEXT NOT NULL,
    created_at       TEXT DEFAULT (datetime('now', 'localtime'))
);

-- 知识标签
CREATE TABLE IF NOT EXISTS tags (
    id    INTEGER PRIMARY KEY AUTOINCREMENT,
    name  TEXT NOT NULL UNIQUE,
    color TEXT DEFAULT '#4A90D9'
);

-- 笔记与标签关联
CREATE TABLE IF NOT EXISTS note_tags (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    tag_id     INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    UNIQUE(project_id, tag_id)
);

-- 快速启动器程序索引
CREATE TABLE IF NOT EXISTS app_index (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL,
    path            TEXT NOT NULL,
    last_scanned_at TEXT DEFAULT (datetime('now', 'localtime'))
);

-- LeetCode 刷题进度
CREATE TABLE IF NOT EXISTS leetcode_progress (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    problem_id   INTEGER NOT NULL UNIQUE,
    status       TEXT DEFAULT 'todo' CHECK(status IN ('todo', 'doing', 'done')),
    note         TEXT,
    file_path    TEXT,
    created_at   TEXT DEFAULT (datetime('now', 'localtime')),
    completed_at TEXT
);
```

---

## 五、UI 规范

**整体布局：**
```
┌──────────────────────────────────────────────────────────────────┐
│  顶部导航栏：模块切换 Tab + 全局搜索框 + 今日学习时长              │
├──────────────┬───────────────────────────────────────────────────┤
│              │                                                   │
│  左侧列表    │         右侧详情 / 操作面板                         │
│              │                                                   │
└──────────────┴───────────────────────────────────────────────────┘
```

**主题（深色，默认）：**
- 背景：`#1E1E1E`
- 强调色：`#4A90D9`
- 文字：`#D4D4D4`
- 次级背景：`#252526`
- 边框：`#3C3C3C`
- 样式通过 `QApplication.setStyleSheet()` 全局应用 QSS

**图标：** 使用 QtAwesome，不使用图片文件作为图标

---

## 六、功能模块列表

| 模块 | 优先级 | 状态 |
|------|--------|------|
| 项目管理 | P0 | 待开发 |
| 快速启动器 | P0 | 待开发 |
| 学习笔记（含 Markdown） | P1 | 待开发 |
| 代码片段库 | P1 | 待开发 |
| TODO 看板 | P1 | 待开发 |
| 全局搜索 | P1 | 待开发 |
| 学习计时器 | P2 | 待开发 |
| 知识标签系统 | P2 | 待开发 |
| 今日概览 | P2 | 待开发 |
| 学习统计（热力图等） | P2 | 待开发 |
| 网络抓包 | P3 | 待开发 |
| 数据备份与恢复 | P3 | 待开发 |
| 主题切换 | P3 | 待开发 |
| 专注模式 | P3 | 待开发 |
| LeetCode Hot 100 | P3 | 待开发 |

---

## 七、各模块详细需求

### 模块 1：项目管理（P0）

**条目类型：**
- 文件夹项目：关联本地文件夹路径
- 单文件代码：关联单个源代码文件

**自动语言识别：**
- 文件夹：扫描目录内扩展名，统计占比，自动打语言标签
- 单文件：直接根据扩展名识别
- 支持：C++、Python、Java、JavaScript、TypeScript、C#、Go、Rust、HTML/CSS、其他

**每个条目字段：**
- 名称、路径、类型（folder/file）
- 语言标签（自动识别，可手动修改）
- 自定义颜色标签
- 备注（单行短文本）
- 学习笔记（Markdown 富文本，存 `projects.content`）
- 默认编辑器（可单独设置）
- 创建时间 / 最后访问时间

**操作：**
- 添加、编辑、删除
- 一键用指定编辑器打开（PyCharm / Cursor / Qt Creator / Visual Studio / 自定义）
- 项目活跃度排行（按最近打开时间或累计学习时长）

---

### 模块 2：快速启动器（P0）

**扫描路径：**
- `C:/ProgramData/Microsoft/Windows/Start Menu`
- `C:/Users/{用户名}/AppData/Roaming/Microsoft/Windows/Start Menu`
- 用户桌面 + 公共桌面
- `C:/Program Files` / `C:/Program Files (x86)`（仅一级目录）

**功能：**
- 收集所有 `.exe` 和 `.lnk`，提取程序名，存入 `app_index` 表
- 用户输入关键词，`rapidfuzz` 模糊匹配，返回 Top 10
- 点击或回车启动程序（`subprocess.Popen`）
- 全局快捷键 `Alt + Space` 呼出（不需要打开主窗口）
- 支持手动刷新索引

---

### 模块 3：学习笔记（P1）

- 每个项目拥有独立笔记页
- Markdown 语法，编辑区与预览区左右分栏
- 笔记内容存入 `projects.content`
- 一键导出为 PDF（`QPrinter`）或 HTML（`QTextEdit.toHtml()`）

---

### 模块 4：代码片段库（P1）

- 新建片段：标题、语言、代码内容、描述
- 按语言分类浏览
- 代码内容语法高亮（`QTextEdit` + 自定义高亮器）
- 一键复制到剪贴板
- 支持搜索标题和内容
- 片段可关联到某个项目（可选）

---

### 模块 5：TODO 看板（P1）

- 每个项目拥有独立看板
- 三列状态：待办 / 进行中 / 已完成
- 任务卡片：标题、描述（可选）、优先级（高/中/低）、截止日期（可选）
- 支持拖拽卡片在列间移动（`QListWidget` + `DragDropMode`）
- 今日视图：只显示截止日期为今天或已逾期的任务
- 汇总视图：所有项目未完成任务，按项目分组展示

---

### 模块 6：全局搜索（P1）

**搜索范围：** 项目名称、备注、笔记内容、代码片段标题和内容、知识标签、语言标签

**功能：**
- 顶部搜索栏，实时过滤结果
- 按语言标签筛选
- 搜索结果高亮显示匹配关键词

---

### 模块 7：学习计时器（P2）

- 番茄钟模式：25 分钟专注 + 5 分钟休息，可自定义时长
- 在项目详情页一键启动，自动关联当前项目
- 计时结束后自动写入 `study_logs` 表
- 专注模式：只显示当前项目 TODO 和计时器

---

### 模块 8：知识标签系统（P2）

- 给项目笔记打自定义标签
- 标签管理页：列出所有标签及关联笔记数量
- 点击标签，聚合显示所有带该标签的笔记片段（跨项目）
- 标签支持颜色自定义

---

### 模块 9：今日概览（P2）

- 今日学习时长
- 待办任务数量
- 最近打开的项目列表
- 快速跳转入口

---

### 模块 10：学习统计（P2）

- 学习热力图（类似 GitHub contribution graph，`matplotlib` 自绘）
- 最近 7 天 / 30 天学习时长趋势图
- 各语言学习时长占比饼图
- 今日学习总时长（顶部导航栏常驻显示）
- 周报摘要：本周时长、完成 TODO 数、新增笔记数、最活跃项目

---

### 模块 11：网络抓包（P3）

**依赖：** scapy + pyshark，需 Npcap 驱动，需管理员权限运行

**全局抓包模式：**
- 列出本机所有网卡，用户选择后开始抓包
- 实时显示数据包列表：序号、时间、协议、源IP、源端口、目标IP、目标端口、数据长度
- 开始 / 停止 按钮
- 按协议过滤：TCP / UDP / HTTP / ICMP / DNS / 全部
- 点击单条数据包，右侧显示原始包详情
- 导出为 `.pcap` 文件

**指定目标模式：**
- 用户输入域名或 IP
- 自动解析域名为 IP（`socket.gethostbyname()`）
- 只捕获与该 IP 相关的数据包
- 显示发送/接收方向标识

**实现：** `QThread` 子线程运行 `scapy.sniff()`，通过 `pyqtSignal` 推送数据到主线程

---

### 模块 12：LeetCode Hot 100（P3）

**题目数据：** 内置完整 100 题，硬编码为 Python 字典，字段：`problem_id, title_en, title_zh, difficulty, tags`

**功能：**
- 题目列表：按难度/标签筛选，显示完成状态
- 一键生成 `.cpp` 文件，自动生成注释模板：
  ```cpp
  /*
   * LeetCode #1 - 两数之和 (Two Sum)
   * 难度: Easy
   * 标签: 数组, 哈希表
   */
  #include <bits/stdc++.h>
  using namespace std;

  class Solution {
  public:

  };
  ```
- 生成后自动用指定编辑器打开
- 一键编译（调用 `g++`）、一键运行，输出显示在内嵌终端区域
- 每道题支持添加笔记、标记完成状态
- 统计：已完成题数、各难度完成比例、连续刷题天数

**文件路径：** 用户可自定义，默认 `~/LeetCode/`  
**依赖：** 系统需安装 `g++`（MinGW 或 MSVC）

---

### 模块 13：数据备份与恢复（P3）

- 导出全部数据为单个 JSON 文件
- 从备份 JSON 文件恢复数据

---

## 八、开发规范

1. **每次只实现一个模块**，实现完成后告知，等待确认再继续
2. **不要超前实现**未要求的功能
3. **不要修改已完成模块**的代码，除非明确要求
4. **数据库初始化**在 `core/database.py` 中统一处理，使用 `CREATE TABLE IF NOT EXISTS`
5. **样式**统一写在 QSS 文件中，不在 Python 代码里硬编码颜色
6. **线程安全**：耗时操作（抓包、扫描、编译）必须放在 `QThread` 子线程，通过 `pyqtSignal` 与主线程通信
7. **错误处理**：文件不存在、路径无效、权限不足等边界情况必须处理，用 `QMessageBox` 提示用户
8. **代码注释**：只在逻辑非显而易见时添加，不写废话注释

---

## 九、当前开发状态

| 阶段 | 内容 | 状态 |
|------|------|------|
| 文档阶段 | 需求文档、技术框架、头脑风暴 | ✅ 完成 |
| 第一阶段 | 骨架 + 项目管理 + 快速启动器 | ⬜ 待开发 |
| 第二阶段 | 笔记 + 片段库 + TODO + 全局搜索 | ⬜ 待开发 |
| 第三阶段 | 计时器 + 标签 + 概览 + 统计 | ⬜ 待开发 |
| 第四阶段 | 抓包 + 备份 + 主题 + 专注 + LeetCode | ⬜ 待开发 |

---

## 十、启动新对话时的 Prompt 模板

每次开启新的 AI 对话，将以下内容粘贴到对话开头：

```
我正在开发一个名为"开发者工作台"的 Windows 桌面应用。
技术栈：Python 3.9 + PyQt5 5.15.9 + SQLite + rapidfuzz + scapy/pyshark + matplotlib。
架构：MVC 三层，目录结构见技术框架文档。
当前任务：[填写本次要做的具体任务]
已完成模块：[填写已完成的模块列表]
请参考 docs/开发prompt文档.md 了解完整项目背景后再开始。
```
