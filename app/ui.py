from __future__ import annotations

from PySide6.QtCore import QThread, QTimer, Qt
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
from .memory import MemoryStore
from .reminders import ReminderStore, parse_reminder
from .screen import ScreenCapture
from .speech import SpeechRecognizer
from .tools import DesktopTools
from .voice import Voice
from .worker import ChatWorker

STYLESHEET = """
QMainWindow { background: #0f1419; }
QWidget#root {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #0f1419, stop:0.55 #15202b, stop:1 #1a2733);
}
QLabel#brand { color: #e8eef4; font-size: 28px; font-weight: 700; letter-spacing: 1px; }
QLabel#subtitle { color: #8ba0b2; font-size: 13px; padding-bottom: 8px; }
QTextEdit#log {
    background: rgba(8, 12, 16, 0.72); color: #d7e2ec;
    border: 1px solid #2a3a48; border-radius: 10px; padding: 14px;
    selection-background-color: #2f6fed;
}
QLineEdit#prompt {
    background: #101820; color: #e8eef4; border: 1px solid #2a3a48;
    border-radius: 8px; padding: 10px 12px; font-size: 14px;
}
QLineEdit#prompt:focus { border: 1px solid #3d8bfd; }
QPushButton {
    background: #2f6fed; color: white; border: none; border-radius: 8px;
    padding: 10px 16px; font-weight: 600;
}
QPushButton:hover { background: #4580f5; }
QPushButton:disabled { background: #314357; color: #8ba0b2; }
QPushButton#secondary { background: #1c2a38; border: 1px solid #2a3a48; }
QPushButton#secondary:hover { background: #243647; }
QPushButton#danger { background: #8a3b3b; }
QPushButton#danger:hover { background: #a44848; }
"""


class MainWindow(QMainWindow):
    def __init__(
        self,
        *,
        client: HermesClient,
        title: str,
        tools: DesktopTools,
        memory: MemoryStore,
        reminders: ReminderStore,
        screen: ScreenCapture,
        speech: SpeechRecognizer,
        voice: Voice,
    ) -> None:
        super().__init__()
        self.client = client
        self.tools = tools
        self.memory = memory
        self.reminders = reminders
        self.screen = screen
        self.speech = speech
        self.voice = voice
        self._busy = False
        self._thread: QThread | None = None
        self._worker: ChatWorker | None = None

        self.setWindowTitle(title)
        self.resize(1000, 720)
        self.setStyleSheet(STYLESHEET)

        brand = QLabel("SirkiAI")
        brand.setObjectName("brand")
        brand.setFont(QFont("Segoe UI", 28, QFont.Weight.Bold))

        flags = []
        flags.append("Hermes" if client.configured else "Demo")
        if memory.enabled:
            flags.append("memory")
        if reminders.enabled:
            flags.append("reminders")
        if settings.tool_calling_enabled:
            flags.append("tools")
        subtitle = QLabel(f"Desktop AI helper · {' · '.join(flags)} · /help for commands")
        subtitle.setObjectName("subtitle")

        self.log = QTextEdit(readOnly=True)
        self.log.setObjectName("log")
        self.log.setAcceptRichText(True)
        self._append_system(
            "SirkiAI roadmap build ready. Try /help, /remember, /remind, /capture, or hold Talk."
        )

        self.input = QLineEdit()
        self.input.setObjectName("prompt")
        self.input.setPlaceholderText("Ask SirkiAI anything...")
        self.input.returnPressed.connect(self.send)

        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send)

        self.talk_button = QPushButton("Talk")
        self.talk_button.setObjectName("secondary")
        self.talk_button.setToolTip("Push-to-talk speech recognition")
        self.talk_button.clicked.connect(self._push_to_talk)

        capture_button = QPushButton("Capture")
        capture_button.setObjectName("secondary")
        capture_button.clicked.connect(lambda: self._handle_command("/capture"))

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
        row.addWidget(self.talk_button)
        row.addWidget(capture_button)
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

        self._reminder_timer = QTimer(self)
        self._reminder_timer.setInterval(5000)
        self._reminder_timer.timeout.connect(self._poll_reminders)
        if reminders.enabled:
            self._reminder_timer.start()

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
        self._start_chat(prompt)

    def _start_chat(self, prompt: str, *, display: str | None = None) -> None:
        self._append_user(display or prompt)
        self._set_busy(True)
        self._append_system("Thinking...")

        thread = QThread(self)
        worker = ChatWorker(self.client)
        worker.set_prompt(prompt)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.consent_requested.connect(self._on_consent_requested, Qt.ConnectionType.QueuedConnection)
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

    def _on_consent_requested(self, name: str, details: str) -> None:
        allowed = self._confirm_tool(name, details)
        if self._worker is not None:
            self._worker.provide_consent(allowed)

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
            self._run_tool("system_info", "Read basic system information?")
            return
        if command == "/open":
            path = argument or self._ask("Open path", "File or folder path:")
            if path and self._confirm_tool("open_path", f"Open this path?\n\n{path}"):
                self._append_tool(self.tools.run("open_path", path).message)
            return
        if command == "/url":
            url = argument or self._ask("Open URL", "https://...")
            if url and self._confirm_tool("open_url", f"Open this URL?\n\n{url}"):
                self._append_tool(self.tools.run("open_url", url).message)
            return
        if command == "/remember":
            self._cmd_remember(argument)
            return
        if command == "/recall":
            self._cmd_recall(argument)
            return
        if command == "/forget":
            self._cmd_forget(argument)
            return
        if command == "/remind":
            self._cmd_remind(argument)
            return
        if command == "/reminders":
            self._cmd_list_reminders()
            return
        if command == "/cancel":
            self._cmd_cancel_reminder(argument)
            return
        if command == "/capture":
            self._cmd_capture(argument)
            return
        if command == "/ask-screen":
            self._cmd_ask_screen(argument)
            return
        if command == "/type":
            text = argument or self._ask("Type text", "Safe text to type:")
            if text and self._confirm_tool("automation_type_text", f"Type this text?\n\n{text}"):
                self._append_tool(self.tools.run("automation_type_text", args={"text": text}).message)
            return
        if command == "/hotkey":
            keys = argument or self._ask("Hotkey", "e.g. ctrl+c")
            if keys and self._confirm_tool("automation_hotkey", f"Press hotkey `{keys}`?"):
                self._append_tool(self.tools.run("automation_hotkey", args={"keys": keys}).message)
            return
        if command == "/click":
            point = argument or self._ask("Click", "x,y")
            if point and self._confirm_tool("automation_click", f"Click at {point}?"):
                self._append_tool(self.tools.run("automation_click", point).message)
            return

        self._append_system(f"Unknown command: {command}. Type /help for available commands.")

    def _cmd_remember(self, argument: str) -> None:
        if not self.memory.enabled:
            self._append_system("Memory disabled. Set MEMORY_ENABLED=true in .env.")
            return
        if "=" in argument:
            key, value = argument.split("=", 1)
        else:
            key = self._ask("Memory key", "Key:")
            value = self._ask("Memory value", "Value:") if key else ""
        if not key or not value:
            return
        if not self._confirm_tool("memory_remember", f"Store memory?\n\n{key.strip()} = {value.strip()}"):
            return
        self._append_tool(self.tools.run("memory_remember", args={"key": key, "value": value}).message)

    def _cmd_recall(self, argument: str) -> None:
        if not self.memory.enabled:
            self._append_system("Memory disabled. Set MEMORY_ENABLED=true in .env.")
            return
        self._append_tool(self.tools.run("memory_recall", args={"query": argument}).message)

    def _cmd_forget(self, argument: str) -> None:
        if not self.memory.enabled:
            self._append_system("Memory disabled. Set MEMORY_ENABLED=true in .env.")
            return
        try:
            memory_id = int(argument)
        except ValueError:
            self._append_system("Usage: /forget <id>")
            return
        if self._confirm_tool("memory_forget", f"Delete memory #{memory_id}?"):
            ok = self.memory.forget(memory_id)
            self._append_tool(f"Forgot #{memory_id}" if ok else f"Memory #{memory_id} not found")

    def _cmd_remind(self, argument: str) -> None:
        if not self.reminders.enabled:
            self._append_system("Reminders disabled. Set REMINDERS_ENABLED=true in .env.")
            return
        spec = argument or self._ask("Reminder", "e.g. in 10m stretch")
        if not spec:
            return
        parsed = parse_reminder(spec)
        if not parsed:
            self._append_system("Could not parse reminder. Try: in 10m stretch")
            return
        if not self._confirm_tool("create_reminder", f"Create reminder?\n\n{spec}"):
            return
        self._append_tool(self.tools.run("create_reminder", args={"spec": spec}).message)

    def _cmd_list_reminders(self) -> None:
        if not self.reminders.enabled:
            self._append_system("Reminders disabled.")
            return
        items = self.reminders.list_pending()
        if not items:
            self._append_tool("No pending reminders.")
            return
        lines = [f"#{item.id} @ {item.due_at}: {item.message}" for item in items]
        self._append_tool("\n".join(lines))

    def _cmd_cancel_reminder(self, argument: str) -> None:
        try:
            reminder_id = int(argument)
        except ValueError:
            self._append_system("Usage: /cancel <reminder_id>")
            return
        if self.reminders.cancel(reminder_id):
            self._append_tool(f"Cancelled reminder #{reminder_id}")
        else:
            self._append_tool(f"Reminder #{reminder_id} not found")

    def _cmd_capture(self, argument: str) -> None:
        if not self._confirm_tool("capture_screen", "Capture the screen now?"):
            return
        result = self.screen.capture(label=argument or "screen")
        self._append_tool(result.message)

    def _cmd_ask_screen(self, argument: str) -> None:
        question = argument or self._ask("Ask about screen", "What should SirkiAI look for?")
        if not question:
            return
        if not self._confirm_tool("capture_screen", "Capture the screen and send it with your question?"):
            return
        capture = self.screen.capture(label="ask")
        self._append_tool(capture.message)
        prompt = self.screen.vision_prompt(question, capture)
        self._start_chat(prompt, display=f"[screen] {question}")

    def _push_to_talk(self) -> None:
        if self._busy:
            return
        self._append_system("Listening...")
        result = self.speech.listen_once()
        if not result.ok:
            self._append_system(result.message)
            return
        self.input.setText(result.text)
        self._append_system(f"Heard: {result.text}")
        self.send()

    def _run_tool(self, name: str, prompt: str) -> None:
        if self._confirm_tool(name, prompt):
            self._append_tool(self.tools.run(name).message)

    def _confirm_tool(self, name: str, message: str) -> bool:
        if not settings.tools_enabled and name not in {"memory_forget"}:
            self._append_system("Tools are disabled. Set TOOLS_ENABLED=true in .env.")
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
            "  /sysinfo — system info\n"
            "  /open [path] — open file/folder\n"
            "  /url [https://...] — open URL\n"
            "  /remember key=value — store memory (opt-in)\n"
            "  /recall [query] — search memories\n"
            "  /forget <id> — delete a memory\n"
            "  /remind in 10m text — schedule reminder\n"
            "  /reminders — list pending reminders\n"
            "  /cancel <id> — cancel reminder\n"
            "  /capture — screenshot\n"
            "  /ask-screen [question] — capture + ask Hermes\n"
            "  /type [text] — allowlisted typing automation\n"
            "  /hotkey [ctrl+c] — allowlisted hotkey\n"
            "  /click x,y — allowlisted click\n"
            "  /clear — clear chat view\n"
            "  /reset — reset Hermes history\n"
            "  Talk button — push-to-talk speech"
        )

    def _poll_reminders(self) -> None:
        for item in self.reminders.due_now():
            self.reminders.mark_delivered(item.id)
            message = f"Reminder #{item.id}: {item.message}"
            self._append_system(message)
            QMessageBox.information(self, "SirkiAI reminder", message)
            if self.voice.available:
                self.voice.speak(item.message)

    def _on_reply(self, reply: str, tool_trace: list) -> None:
        self._remove_trailing_thinking()
        for entry in tool_trace:
            self._append_tool(str(entry))
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
        self.talk_button.setEnabled(not busy)

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

    def closeEvent(self, event) -> None:  # noqa: N802
        self._reminder_timer.stop()
        if self._thread and self._thread.isRunning():
            self._thread.quit()
            self._thread.wait(1000)
        super().closeEvent(event)
