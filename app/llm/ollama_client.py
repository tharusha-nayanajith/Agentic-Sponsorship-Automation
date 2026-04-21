"""Small Ollama client wrapper for local model access."""

from __future__ import annotations

import os
from typing import Any

import requests


DEFAULT_OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
DEFAULT_OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
REQUEST_TIMEOUT_SECONDS = 60


class OllamaClient:
    """Minimal Ollama REST client for local generation and health checks."""

    def __init__(
        self,
        base_url: str = DEFAULT_OLLAMA_BASE_URL,
        model: str = DEFAULT_OLLAMA_MODEL,
        timeout_seconds: int = REQUEST_TIMEOUT_SECONDS,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.session = requests.Session()

    def health_check(self) -> bool:
        """Return whether the local Ollama API is reachable."""

        try:
            response = self.session.get(
                f"{self.base_url}/api/tags",
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
        except requests.RequestException:
            return False
        return True

    def list_models(self) -> list[str]:
        """Return locally available Ollama model names."""

        response = self.session.get(
            f"{self.base_url}/api/tags",
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        return [model["name"] for model in payload.get("models", [])]

    def generate(
        self,
        prompt: str,
        model: str | None = None,
        system: str | None = None,
        stream: bool = False,
        options: dict[str, Any] | None = None,
    ) -> str:
        """Generate text from the Ollama `/api/generate` endpoint."""

        payload: dict[str, Any] = {
            "model": model or self.model,
            "prompt": prompt,
            "stream": stream,
        }
        if system:
            payload["system"] = system
        if options:
            payload["options"] = options

        response = self.session.post(
            f"{self.base_url}/api/generate",
            json=payload,
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        data = response.json()
        return data.get("response", "").strip()

    def chat(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        stream: bool = False,
        options: dict[str, Any] | None = None,
    ) -> str:
        """Generate chat output from the Ollama `/api/chat` endpoint."""

        payload: dict[str, Any] = {
            "model": model or self.model,
            "messages": messages,
            "stream": stream,
        }
        if options:
            payload["options"] = options

        response = self.session.post(
            f"{self.base_url}/api/chat",
            json=payload,
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        data = response.json()
        return data.get("message", {}).get("content", "").strip()
