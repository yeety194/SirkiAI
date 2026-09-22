from __future__ import annotations

from PySide6.QtWidgets import QHBoxLayout, QLineEdit, QMainWindow, QPushButton, QTextEdit, QVBoxLayout, QWidget

from .hermes import HermesClient


class MainWindow(QMainWindow):
    def __init__(self, client: HermesClient, title: str) -> None:
        super().__init__()
        self.client = client
        self.setWindowTitle(title)
        self.resize(900, 650)

        self.log = QTextEdit(readOnly=True)
        self.log.append("<i>SirkiAI is ready. Ask a question to begin.</i>")
        self.input = QLineEdit(placeholderText="Ask SirkiAI anything...")
        self.input.returnPressed.connect(self.send)
        send = QPushButton("Send")
        send.clicked.connect(self.send)

        row = QHBoxLayout()
        row.addWidget(self.input)
        row.addWidget(send)
        layout = QVBoxLayout()
        layout.addWidget(self.log)
        layout.addLayout(row)
        root = QWidget()
        root.setLayout(layout)
        self.setCentralWidget(root)

    def send(self) -> None:
        prompt = self.input.text().strip()
        if not prompt:
            return
        self.input.clear()
        self.log.append(f"<b>You:</b> {prompt}")
        self.log.append(f"<b>SirkiAI:</b> {self.client.chat(prompt)}")
