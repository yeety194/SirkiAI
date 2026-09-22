from __future__ import annotations

from urllib.parse import urljoin

import requests


class HermesClient:
    def __init__(self, base_url: str, api_key: str, model: str, endpoint: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.endpoint = endpoint

    def chat(self, prompt: str) -> str:
        if not self.base_url or not self.api_key:
            return "Demo mode: configure HERMES_BASE_URL and HERMES_API_KEY in .env to connect Hermes Agent."

        url = urljoin(self.base_url + "/", self.endpoint.lstrip("/"))
        try:
            response = requests.post(
                url,
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"model": self.model, "messages": [{"role": "user", "content": prompt}]},
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except (requests.RequestException, KeyError, IndexError, TypeError, ValueError) as exc:
            return f"Hermes request failed: {exc}"
