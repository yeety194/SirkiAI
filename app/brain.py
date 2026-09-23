from __future__ import annotations

from dataclasses import dataclass

import requests

from .config import Settings


@dataclass(frozen=True)
class BrainTarget:
    mode: str  # local | remote | demo
    base_url: str
    api_key: str
    model: str
    endpoint: str
    label: str


def ollama_reachable(base_url: str, timeout: float = 1.5) -> bool:
    root = base_url.rstrip("/")
    if root.endswith("/v1"):
        root = root[:-3]
    try:
        response = requests.get(f"{root}/api/tags", timeout=timeout)
        return response.ok
    except requests.RequestException:
        return False


def resolve_brain(settings: Settings) -> BrainTarget:
    """Pick local Ollama, remote Hermes, or demo mode."""
    mode = settings.brain_mode.lower().strip()
    local_url = settings.local_brain_url.rstrip("/")

    if mode == "demo":
        return BrainTarget("demo", "", "", settings.hermes_model, settings.hermes_api_endpoint, "Demo")

    if mode == "remote":
        if settings.hermes_base_url and settings.hermes_api_key:
            return BrainTarget(
                "remote",
                settings.hermes_base_url,
                settings.hermes_api_key,
                settings.hermes_model,
                settings.hermes_api_endpoint,
                "Remote Hermes",
            )
        return BrainTarget("demo", "", "", settings.hermes_model, settings.hermes_api_endpoint, "Demo")

    if mode == "local" or (mode == "auto" and ollama_reachable(local_url)):
        return BrainTarget(
            "local",
            local_url,
            settings.local_brain_api_key or "ollama",
            settings.local_brain_model,
            settings.hermes_api_endpoint,
            f"Local brain ({settings.local_brain_model})",
        )

    if settings.hermes_base_url and settings.hermes_api_key:
        return BrainTarget(
            "remote",
            settings.hermes_base_url,
            settings.hermes_api_key,
            settings.hermes_model,
            settings.hermes_api_endpoint,
            "Remote Hermes",
        )

    # Default for auto when nothing is up yet: still target local brain so setup docs apply.
    return BrainTarget(
        "local",
        local_url,
        settings.local_brain_api_key or "ollama",
        settings.local_brain_model,
        settings.hermes_api_endpoint,
        f"Local brain ({settings.local_brain_model})",
    )
