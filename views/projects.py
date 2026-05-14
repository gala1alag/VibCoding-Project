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
