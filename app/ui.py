from __future__ import annotations

from PySide6.QtCore import QThread
from PySide6.QtGui import QFont, QTextCursor
from PySide6.QtWidgets import (
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .config import settings
from .hermes import HermesClient
from .tools import DesktopTools
from .voice import Voice
from .worker import ChatWorker

STYLESHEET = """
QMainWindow {
    background: #0f1419;
}
QWidget#root {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:1,
        stop:0 #0f1419,
        stop:0.55 #15202b,
        stop:1 #1a2733
    );
}
QLabel#brand {
    color: #e8eef4;
    font-size: 28px;
    font-weight: 700;
    letter-spacing: 1px;
}
QLabel#subtitle {
    color: #8ba0b2;
    font-size: 13px;
    padding-bottom: 8px;
}
QTextEdit#log {
    background: rgba(8, 12, 16, 0.72);
    color: #d7e2ec;
    border: 1px solid #2a3a48;
    border-radius: 10px;
    padding: 14px;
    selection-background-color: #2f6fed;
}
QLineEdit#prompt {
    background: #101820;
    color: #e8eef4;
    border: 1px solid #2a3a48;
    border-radius: 8px;
    padding: 10px 12px;
    font-size: 14px;
}
QLineEdit#prompt:focus {
    border: 1px solid #3d8bfd;
}
QPushButton {
    background: #2f6fed;
    color: white;
    border: none;
    border-radius: 8px;
    padding: 10px 16px;
    font-weight: 600;
}
QPushButton:hover {
    background: #4580f5;
}
QPushButton:disabled {
    background: #314357;
    color: #8ba0b2;
}
QPushButton#secondary {
    background: #1c2a38;
    border: 1px solid #2a3a48;
}
QPushButton#secondary:hover {
    background: #243647;
}
"""


class MainWindow(QMainWindow):
    def __init__(self, client: HermesClient, title: str) -> None:
        super().__init__()
        self.client = client
        self.tools = DesktopTools()
        self.voice = Voice()
        self._busy = False
        self._thread: QThread | None = None
        self._worker: ChatWorker | None = None

        self.setWindowTitle(title)
        self.resize(960, 700)
        self.setStyleSheet(STYLESHEET)

        brand = QLabel("SirkiAI")
        brand.setObjectName("brand")
        brand.setFont(QFont("Segoe UI", 28, QFont.Weight.Bold))

        mode = "Hermes connected" if client.configured else "Demo mode"
        subtitle = QLabel(f"Desktop AI helper · {mode} · type /help for commands")
        subtitle.setObjectName("subtitle")

        self.log = QTextEdit(readOnly=True)
        self.log.setObjectName("log")
        self.log.setAcceptRichText(True)
        self._append_system(
            "SirkiAI is ready. Ask a question, or use /help, /sysinfo, /open, /url, /clear, /reset."
        )

        self.input = QLineEdit()
        self.input.setObjectName("prompt")
        self.input.setPlaceholderText("Ask SirkiAI anything...")
        self.input.returnPressed.connect(self.send)

        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send)

        help_button = QPushButton("Help")
        help_button.setObjectName("secondary")
        help_button.clicked.connect(self._show_help)

        clear_button = QPushButton("Clear")
        clear_button.setObjectName("secondary")
        clear_button.clicked.connect(self._clear_log)

        row = QHBoxLayout()
        row.setSpacing(8)
        row.addWidget(self.input, stretch=1)
        row.addWidget(self.send_button)
        row.addWidget(help_button)
        row.addWidget(clear_button)

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(10)
        layout.addWidget(brand)
        layout.addWidget(subtitle)
        layout.addWidget(self.log, stretch=1)
        layout.addLayout(row)

        root = QWidget()
        root.setObjectName("root")
        root.setLayout(layout)
        self.setCentralWidget(root)

    def send(self) -> None:
        if self._busy:
            return
        prompt = self.input.text().strip()
        if not prompt:
            return
        self.input.clear()

        if prompt.startswith("/"):
            self._handle_command(prompt)
            return

        self._append_user(prompt)
        self._set_busy(True)
        self._append_system("Thinking...")

        thread = QThread(self)
        worker = ChatWorker(self.client)
        worker.set_prompt(prompt)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished.connect(self._on_reply)
        worker.failed.connect(self._on_error)
        worker.finished.connect(thread.quit)
        worker.failed.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(self._on_thread_finished)
        self._thread = thread
        self._worker = worker
        thread.start()

    def _handle_command(self, raw: str) -> None:
        parts = raw.split(maxsplit=1)
        command = parts[0].lower()
        argument = parts[1].strip() if len(parts) > 1 else ""

        if command in {"/help", "/?"}:
            self._show_help()
            return
        if command == "/clear":
            self._clear_log()
            return
        if command == "/reset":
            self.client.reset()
            self._append_system("Conversation history reset.")
            return
        if command == "/sysinfo":
            if not self._confirm_tool("system_info", "Read basic system information?"):
                return
            result = self.tools.run("system_info")
            self._append_tool(result.message)
            return
        if command == "/open":
            path = argument or self._ask("Open path", "File or folder path:")
            if not path:
                return
            if not self._confirm_tool("open_path", f"Open this path?\n\n{path}"):
                return
            result = self.tools.run("open_path", path)
            self._append_tool(result.message)
            return
        if command == "/url":
            url = argument or self._ask("Open URL", "https://...")
            if not url:
                return
            if not self._confirm_tool("open_url", f"Open this URL in your browser?\n\n{url}"):
                return
            result = self.tools.run("open_url", url)
            self._append_tool(result.message)
            return

        self._append_system(f"Unknown command: {command}. Type /help for available commands.")

    def _confirm_tool(self, name: str, message: str) -> bool:
        if not settings.tools_enabled:
            self._append_system("Tools are disabled. Set TOOLS_ENABLED=true in .env.")
            return False
        if name not in DesktopTools.ALLOWED:
            self._append_system(f"Tool not allowed: {name}")
            return False
        answer = QMessageBox.question(
            self,
            "Permission required",
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return answer == QMessageBox.StandardButton.Yes

    def _ask(self, title: str, label: str) -> str:
        text, ok = QInputDialog.getText(self, title, label)
        return text.strip() if ok else ""

    def _show_help(self) -> None:
        self._append_system(
            "Commands:\n"
            "  /help — show this help\n"
            "  /sysinfo — permission-gated system info\n"
            "  /open [path] — open a local file or folder\n"
            "  /url [https://...] — open a URL\n"
            "  /clear — clear the chat view\n"
            "  /reset — reset Hermes conversation history"
        )

    def _on_reply(self, reply: str) -> None:
        self._remove_trailing_thinking()
        self._append_assistant(reply)
        if self.voice.available:
            self.voice.speak(reply)

    def _on_error(self, message: str) -> None:
        self._remove_trailing_thinking()
        self._append_system(f"Error: {message}")

    def _on_thread_finished(self) -> None:
        self._thread = None
        self._worker = None
        self._set_busy(False)

    def _set_busy(self, busy: bool) -> None:
        self._busy = busy
        self.send_button.setEnabled(not busy)
        self.input.setEnabled(not busy)

    def _clear_log(self) -> None:
        self.log.clear()
        self._append_system("Chat view cleared.")

    def _append_user(self, text: str) -> None:
        self.log.append(f"<p><b style='color:#7eb6ff'>You</b><br>{self._escape(text)}</p>")
        self._scroll_to_end()

    def _append_assistant(self, text: str) -> None:
        self.log.append(f"<p><b style='color:#6fd3a0'>SirkiAI</b><br>{self._escape(text)}</p>")
        self._scroll_to_end()

    def _append_system(self, text: str) -> None:
        self.log.append(f"<p><i style='color:#8ba0b2'>{self._escape(text)}</i></p>")
        self._scroll_to_end()

    def _append_tool(self, text: str) -> None:
        self.log.append(
            f"<p><b style='color:#e0b35a'>Tool</b><br><pre style='color:#d7e2ec'>{self._escape(text)}</pre></p>"
        )
        self._scroll_to_end()

    def _remove_trailing_thinking(self) -> None:
        cursor = self.log.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.log.setTextCursor(cursor)
        # Best-effort visual cleanup; leave prior history intact if pattern missing.
        html = self.log.toHtml()
        marker = "<i style='color:#8ba0b2'>Thinking...</i>"
        if marker in html:
            self.log.setHtml(html.replace(marker, "", 1))

    def _scroll_to_end(self) -> None:
        self.log.moveCursor(QTextCursor.MoveOperation.End)

    @staticmethod
    def _escape(text: str) -> str:
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace("\n", "<br>")
        )

    def closeEvent(self, event) -> None:  # noqa: N802 — Qt API
        if self._thread and self._thread.isRunning():
            self._thread.quit()
            self._thread.wait(1000)
        super().closeEvent(event)
