# Placeholder — implemented in Issue #6
from PySide6.QtWidgets import QMainWindow, QLabel
from PySide6.QtCore import Qt


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Intercompany Eliminator")
        self.resize(800, 600)
        placeholder = QLabel("Intercompany Eliminator — coming soon", self)
        placeholder.setAlignment(Qt.AlignCenter)
        self.setCentralWidget(placeholder)
