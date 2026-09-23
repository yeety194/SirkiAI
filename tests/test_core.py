"""Smoke tests for SirkiAI roadmap modules."""

from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

from app.automation import DesktopAutomation
from app.brain import resolve_brain
from app.hermes import HermesClient
from app.memory import MemoryStore
from app.reminders import ReminderStore, parse_reminder
from app.screen import CaptureResult, ScreenCapture
from app.tools import DesktopTools, tool_args_from_call


def _settings(**overrides):
    base = {
        "brain_mode": "auto",
        "local_brain_url": "http://127.0.0.1:11434/v1",
        "local_brain_model": "hermes3:3b",
        "local_brain_api_key": "ollama",
        "hermes_base_url": "",
        "hermes_api_key": "",
        "hermes_model": "hermes-3",
        "hermes_api_endpoint": "/chat/completions",
    }
    base.update(overrides)
    return type("S", (), base)()


class BrainResolveTests(unittest.TestCase):
    def test_local_mode(self) -> None:
        target = resolve_brain(_settings(brain_mode="local"))
        self.assertEqual(target.mode, "local")
        self.assertEqual(target.model, "hermes3:3b")
        self.assertTrue(target.base_url.endswith("/v1"))

    def test_remote_requires_key(self) -> None:
        target = resolve_brain(
            _settings(brain_mode="remote", hermes_base_url="https://example.com/v1", hermes_api_key="")
        )
        self.assertEqual(target.mode, "demo")

    def test_demo_mode(self) -> None:
        target = resolve_brain(
            _settings(brain_mode="demo", hermes_base_url="https://example.com/v1", hermes_api_key="key")
        )
        self.assertEqual(target.mode, "demo")


class HermesClientTests(unittest.TestCase):
    def test_local_url_without_key_is_configured(self) -> None:
        client = HermesClient("http://127.0.0.1:11434/v1", "", "hermes3:3b", "/chat/completions")
        self.assertTrue(client.configured)
    def test_demo_mode_without_credentials(self) -> None:
        client = HermesClient("", "", "hermes-3", "/chat/completions")
        reply = client.chat("hello")
        self.assertIn("Demo mode", reply)
        self.assertEqual(len(client.messages), 2)

    def test_reset_keeps_system_prompt(self) -> None:
        client = HermesClient("", "", "hermes-3", "/chat/completions", system_prompt="sys")
        client.chat("hello")
        client.reset()
        self.assertEqual(client.messages, [{"role": "system", "content": "sys"}])

    @patch("app.hermes.requests.post")
    def test_successful_chat(self, post: MagicMock) -> None:
        post.return_value = MagicMock(
            raise_for_status=MagicMock(),
            json=MagicMock(return_value={"choices": [{"message": {"content": "hi there"}}]}),
        )
        client = HermesClient("https://example.com", "key", "hermes-3", "/chat/completions")
        reply = client.chat("hello")
        self.assertEqual(reply, "hi there")

    @patch("app.hermes.requests.post")
    def test_tool_calling_bridge_with_consent(self, post: MagicMock) -> None:
        tools = DesktopTools(tools_enabled=True)
        post.side_effect = [
            MagicMock(
                raise_for_status=MagicMock(),
                json=MagicMock(
                    return_value={
                        "choices": [
                            {
                                "message": {
                                    "role": "assistant",
                                    "content": None,
                                    "tool_calls": [
                                        {
                                            "id": "call_1",
                                            "type": "function",
                                            "function": {"name": "system_info", "arguments": "{}"},
                                        }
                                    ],
                                }
                            }
                        ]
                    }
                ),
            ),
            MagicMock(
                raise_for_status=MagicMock(),
                json=MagicMock(return_value={"choices": [{"message": {"role": "assistant", "content": "done"}}]}),
            ),
        ]
        client = HermesClient(
            "https://example.com",
            "key",
            "hermes-3",
            "/chat/completions",
            tools=tools,
            tool_calling_enabled=True,
        )
        consents: list[str] = []

        def consent(name: str, details: str) -> bool:
            consents.append(name)
            return True

        outcome = client.chat_detailed("need info", consent=consent)
        self.assertEqual(outcome.text, "done")
        self.assertEqual(consents, ["system_info"])
        self.assertTrue(any("system_info" in item for item in outcome.tool_trace))


class DesktopToolsTests(unittest.TestCase):
    def test_system_info(self) -> None:
        result = DesktopTools().run("system_info")
        self.assertTrue(result.ok)
        self.assertIn("system:", result.message)

    def test_disallows_unknown_tool(self) -> None:
        result = DesktopTools().run("delete_disk")
        self.assertFalse(result.ok)

    def test_open_url_requires_http(self) -> None:
        result = DesktopTools().run("open_url", "ftp://example.com")
        self.assertFalse(result.ok)

    def test_tool_args_from_call(self) -> None:
        self.assertEqual(tool_args_from_call('{"path":"C:/"}'), {"path": "C:/"})
        self.assertEqual(tool_args_from_call({"url": "https://x"}), {"url": "https://x"})


class MemoryStoreTests(unittest.TestCase):
    def test_opt_in_required(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = MemoryStore(Path(tmp) / "db.sqlite3", enabled=False)
            self.assertIsNone(store.remember("k", "v"))
            self.assertEqual(store.list_recent(), [])

    def test_remember_recall_forget(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = MemoryStore(Path(tmp) / "db.sqlite3", enabled=True)
            item = store.remember("favorite", "espresso")
            assert item is not None
            hits = store.recall("espresso")
            self.assertEqual(len(hits), 1)
            self.assertTrue(store.forget(item.id))
            self.assertEqual(store.list_recent(), [])


class ReminderTests(unittest.TestCase):
    def test_parse_reminder(self) -> None:
        now = datetime(2026, 1, 1, tzinfo=timezone.utc)
        parsed = parse_reminder("in 10m stretch", now=now)
        assert parsed is not None
        due, text = parsed
        self.assertEqual(text, "stretch")
        self.assertEqual(due, now + timedelta(minutes=10))

    def test_store_due_and_deliver(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = ReminderStore(Path(tmp) / "db.sqlite3", enabled=True)
            due = datetime.now(timezone.utc) - timedelta(seconds=1)
            item = store.add("ping", due)
            assert item is not None
            due_items = store.due_now()
            self.assertEqual(len(due_items), 1)
            self.assertTrue(store.mark_delivered(item.id))
            self.assertEqual(store.due_now(), [])


class ScreenCaptureTests(unittest.TestCase):
    def test_disabled(self) -> None:
        capture = ScreenCapture(enabled=False)
        result = capture.capture()
        self.assertFalse(result.ok)

    def test_vision_prompt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "shot.png"
            path.write_bytes(b"\x89PNG\r\n\x1a\n" + b"0" * 32)
            result = CaptureResult(True, "ok", path=path)
            prompt = ScreenCapture(enabled=True).vision_prompt("What is open?", result)
            self.assertIn("What is open?", prompt)
            self.assertIn("Screenshot attached", prompt)


class AutomationTests(unittest.TestCase):
    def test_disabled(self) -> None:
        auto = DesktopAutomation(enabled=False)
        result = auto.run("type_text", "hello")
        self.assertFalse(result.ok)

    def test_rejects_unknown_action(self) -> None:
        auto = DesktopAutomation(enabled=True)
        result = auto.run("drag_everywhere", "1,1")
        self.assertFalse(result.ok)

    def test_rejects_unsafe_hotkey(self) -> None:
        auto = DesktopAutomation(enabled=True)
        result = auto.run("hotkey", "ctrl+alt+delete")
        self.assertFalse(result.ok)


if __name__ == "__main__":
    unittest.main()
