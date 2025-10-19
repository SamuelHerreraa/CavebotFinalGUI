# gui/widgets/log_console.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPlainTextEdit, QHBoxLayout, QPushButton, QFileDialog
from PySide6.QtCore import Qt
from pathlib import Path

class LogConsole(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("LogConsole")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(4, 4, 4, 4)
        lay.setSpacing(4)

        self.text = QPlainTextEdit(self)
        self.text.setReadOnly(True)
        self.text.setMaximumBlockCount(2000)
        lay.addWidget(self.text)

        btns = QHBoxLayout()
        self.btn_copy = QPushButton("Copiar todo")
        self.btn_save = QPushButton("Guardar...")
        btns.addWidget(self.btn_copy)
        btns.addWidget(self.btn_save)
        lay.addLayout(btns)

        self.btn_copy.clicked.connect(self._on_copy)
        self.btn_save.clicked.connect(self._on_save)

    def append_line(self, line: str):
        self.text.appendPlainText(line)

    def _on_copy(self):
        self.text.selectAll()
        self.text.copy()
        self.text.moveCursor(self.text.textCursor().End)

    def _on_save(self):
        path, _ = QFileDialog.getSaveFileName(self, "Guardar logs", str(Path.cwd() / "logs.txt"), "Text (*.txt)")
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.text.toPlainText())
