from __future__ import annotations

from urllib.parse import urljoin

import requests


class HermesClient:
    """Thin Hermes-compatible chat adapter with local conversation history."""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        endpoint: str,
        *,
        timeout_seconds: int = 30,
        system_prompt: str | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.endpoint = endpoint
        self.timeout_seconds = timeout_seconds
        self.messages: list[dict[str, str]] = []
        if system_prompt:
            self.messages.append({"role": "system", "content": system_prompt})

    @property
    def configured(self) -> bool:
        return bool(self.base_url and self.api_key)

    def reset(self) -> None:
        system = [m for m in self.messages if m.get("role") == "system"]
        self.messages = system

    def chat(self, prompt: str) -> str:
        self.messages.append({"role": "user", "content": prompt})

        if not self.configured:
            reply = (
                "Demo mode: SirkiAI is running locally without Hermes credentials. "
                "Set HERMES_BASE_URL and HERMES_API_KEY in .env to connect your agent. "
                "Try asking about system info, or type /help for starter commands."
            )
            self.messages.append({"role": "assistant", "content": reply})
            return reply

        url = urljoin(self.base_url + "/", self.endpoint.lstrip("/"))
        try:
            response = requests.post(
                url,
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"model": self.model, "messages": self.messages},
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            data = response.json()
            reply = data["choices"][0]["message"]["content"]
            if not isinstance(reply, str):
                raise TypeError("assistant content was not a string")
            self.messages.append({"role": "assistant", "content": reply})
            return reply
        except (requests.RequestException, KeyError, IndexError, TypeError, ValueError) as exc:
            # Drop the failed user turn so retries stay clean.
            self.messages.pop()
            return f"Hermes request failed: {exc}"
