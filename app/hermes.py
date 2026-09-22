from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Callable
from urllib.parse import urljoin

import requests

from .tools import TOOL_DEFINITIONS, DesktopTools, tool_args_from_call


ConsentCallback = Callable[[str, str], bool]


@dataclass
class ChatOutcome:
    text: str
    tool_trace: list[str]


class HermesClient:
    """Hermes-compatible chat adapter with history and optional tool-calling bridge."""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        endpoint: str,
        *,
        timeout_seconds: int = 30,
        system_prompt: str | None = None,
        tools: DesktopTools | None = None,
        tool_calling_enabled: bool = False,
        max_tool_rounds: int = 3,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.endpoint = endpoint
        self.timeout_seconds = timeout_seconds
        self.tools = tools
        self.tool_calling_enabled = tool_calling_enabled
        self.max_tool_rounds = max_tool_rounds
        self.messages: list[dict[str, Any]] = []
        if system_prompt:
            self.messages.append({"role": "system", "content": system_prompt})

    @property
    def configured(self) -> bool:
        return bool(self.base_url and self.api_key)

    def reset(self) -> None:
        system = [m for m in self.messages if m.get("role") == "system"]
        self.messages = system

    def inject_system_note(self, note: str) -> None:
        if note.strip():
            self.messages.append({"role": "system", "content": note.strip()})

    def chat(self, prompt: str, *, consent: ConsentCallback | None = None) -> str:
        return self.chat_detailed(prompt, consent=consent).text

    def chat_detailed(self, prompt: str, *, consent: ConsentCallback | None = None) -> ChatOutcome:
        self.messages.append({"role": "user", "content": prompt})
        trace: list[str] = []

        if not self.configured:
            reply = (
                "Demo mode: SirkiAI is running locally without Hermes credentials. "
                "Set HERMES_BASE_URL and HERMES_API_KEY in .env to connect your agent. "
                "Use /help for memory, reminders, capture, speech, and automation commands."
            )
            self.messages.append({"role": "assistant", "content": reply})
            return ChatOutcome(reply, trace)

        url = urljoin(self.base_url + "/", self.endpoint.lstrip("/"))
        try:
            for _ in range(max(1, self.max_tool_rounds + 1)):
                payload: dict[str, Any] = {"model": self.model, "messages": self.messages}
                if self.tool_calling_enabled and self.tools is not None:
                    payload["tools"] = TOOL_DEFINITIONS
                    payload["tool_choice"] = "auto"

                response = requests.post(
                    url,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json=payload,
                    timeout=self.timeout_seconds,
                )
                response.raise_for_status()
                data = response.json()
                message = data["choices"][0]["message"]
                tool_calls = message.get("tool_calls") or []

                if tool_calls and self.tool_calling_enabled and self.tools is not None:
                    self.messages.append(message)
                    for call in tool_calls:
                        name, args, call_id = self._parse_tool_call(call)
                        summary = f"Hermes requested `{name}` with {json.dumps(args)}"
                        result = self.tools.execute_with_consent(
                            name,
                            args=args,
                            consent=consent,
                            summary=summary,
                        )
                        trace.append(f"{name}: {result.message}")
                        self.messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": call_id,
                                "name": name,
                                "content": result.message,
                            }
                        )
                    continue

                reply = message.get("content") or ""
                if not isinstance(reply, str):
                    raise TypeError("assistant content was not a string")
                self.messages.append({"role": "assistant", "content": reply})
                return ChatOutcome(reply, trace)

            return ChatOutcome("Stopped after max tool rounds without a final answer.", trace)
        except (requests.RequestException, KeyError, IndexError, TypeError, ValueError) as exc:
            if self.messages and self.messages[-1].get("role") == "user":
                self.messages.pop()
            return ChatOutcome(f"Hermes request failed: {exc}", trace)

    @staticmethod
    def _parse_tool_call(call: dict[str, Any]) -> tuple[str, dict[str, Any], str]:
        if "function" in call:
            function = call.get("function") or {}
            name = str(function.get("name") or "")
            args = tool_args_from_call(function.get("arguments"))
            call_id = str(call.get("id") or name)
            return name, args, call_id
        name = str(call.get("name") or "")
        args = tool_args_from_call(call.get("arguments"))
        return name, args, str(call.get("id") or name)
