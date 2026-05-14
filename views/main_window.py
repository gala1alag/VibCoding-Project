from PyQt5.QtWidgets import QMainWindow, QTabWidget, QWidget
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
