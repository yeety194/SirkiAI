"""Smoke tests for SirkiAI core modules. Run: python -m unittest discover -s tests -v"""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from app.hermes import HermesClient
from app.tools import DesktopTools


class HermesClientTests(unittest.TestCase):
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
        self.assertEqual(client.messages[-1]["content"], "hi there")


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


if __name__ == "__main__":
    unittest.main()
