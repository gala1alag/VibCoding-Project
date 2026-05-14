# 开发者工作台 — 骨架框架设计文档

**日期：** 2026-05-13  
**范围：** 骨架框架（可运行主窗口 + 导航 + 占位模块 + 数据库初始化）

---

## 一、目标

搭建可运行的应用骨架：主窗口启动、顶部标签导航切换 8 个模块、深色主题、SQLite 数据库初始化。各模块视图为占位符，后续逐步填充功能。

---

## 二、目录结构

```
VibeCoding/
├── main.py                        # 程序入口
├── requirements.txt               # 依赖列表
├── data/                          # 运行时创建，存放 devhub.db
├── assets/
│   └── themes/
│       ├── dark.qss               # 深色主题（默认）
│       └── light.qss              # 浅色主题（占位）
├── core/
│   ├── database.py                # 数据库连接与建表
│   └── settings.py                # 全局配置
├── models/
│   ├── project.py
│   ├── snippet.py
│   ├── todo.py
│   ├── study_log.py
│   └── tag.py
├── views/
│   ├── main_window.py             # 主窗口
│   ├── overview.py                # 今日概览（占位）
│   ├── projects.py                # 项目管理（占位）
│   ├── snippets.py                # 代码片段库（占位）
│   ├── todos.py                   # TODO 看板（占位）
│   ├── stats.py                   # 学习统计（占位）
│   ├── launcher.py                # 快速启动（占位）
│   ├── capture.py                 # 网络抓包（占位）
│   └── tags.py                    # 知识标签（占位）
├── controllers/
│   ├── project_ctrl.py
│   ├── snippet_ctrl.py
│   ├── todo_ctrl.py
│   ├── timer_ctrl.py
│   ├── launcher_ctrl.py
│   └── capture_ctrl.py
└── utils/
    ├── language_detector.py
    ├── app_scanner.py
    ├── fuzzy_matcher.py
    └── backup.py
```

---

## 三、主窗口设计

- `MainWindow(QMainWindow)`
- 顶部：`QTabBar` 或 `QTabWidget`，8 个标签：今日概览 / 项目管理 / 代码片段库 / TODO 看板 / 学习统计 / 快速启动 / 网络抓包 / 知识标签
- 内容区：`QStackedWidget`，每个标签对应一个视图组件
- 标签切换信号连接到 `QStackedWidget.setCurrentIndex()`

---

## 四、主题方案

- 默认加载 `assets/themes/dark.qss`，通过 `QApplication.setStyleSheet()` 全局应用
- 深色：背景 `#1E1E1E`，强调色 `#4A90D9`，文字 `#D4D4D4`，边框 `#3C3C3C`
- QSS 按组件分块注释，便于后期维护
- `light.qss` 骨架阶段为空文件占位

---

## 五、数据库初始化

- `core/database.py` 提供 `get_connection()` 和 `init_db()`
- `init_db()` 在 `main.py` 启动时调用，使用 `CREATE TABLE IF NOT EXISTS` 建所有表
- 表：`projects`、`snippets`、`todos`、`study_logs`、`tags`、`note_tags`、`app_index`
- 数据库文件路径：`data/devhub.db`，`data/` 目录不存在时自动创建

---

## 六、全局配置

`core/settings.py` 提供 `Settings` 单例：
- `theme`：`"dark"` / `"light"`
- `default_editor`：默认编辑器路径
- `db_path`：数据库文件路径
- 配置持久化到 `data/settings.json`

---

## 七、各模块占位视图

每个视图文件导出一个 `QWidget` 子类，内容为居中 `QLabel` 显示模块名称，供后续替换为真实实现。

---

## 八、模型与控制器

- 模型：定义数据类（`dataclass` 或普通类），字段与数据库表对应，不含数据库操作
- 控制器：定义类骨架和方法签名，方法体为 `pass`，供后续实现

---

## 九、启动流程

```
main.py
  → init_db()          # 建表
  → 加载 dark.qss      # 主题
  → MainWindow()       # 主窗口
  → app.exec_()
```

---

## 十、不在本次范围内

- 任何模块的实际功能实现
- rapidfuzz / scapy / pyshark 的安装与使用
- 打包（PyInstaller）
- LeetCode 模块

---

## 十一、后续开发状态

| 阶段 | 模块 | 设计文档 | 状态 |
|------|------|----------|------|
| P0 | 项目管理 | `2026-05-14-project-management-design.md` | 设计完成，待实现 |
| P0 | 快速启动器 | — | 待设计 |
