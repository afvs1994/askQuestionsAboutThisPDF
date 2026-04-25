from __future__ import annotations

from dataclasses import dataclass

import httpx


class OllamaUnavailableError(RuntimeError):
    pass


@dataclass(slots=True)
class OllamaClient:
    base_url: str
    model: str
    timeout_seconds: float

    def generate(self, prompt: str) -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }
        try:
            with httpx.Client(base_url=self.base_url.rstrip("/"), timeout=self.timeout_seconds) as client:
                response = client.post("/api/generate", json=payload)
                response.raise_for_status()
                data = response.json()
        except (httpx.RequestError, httpx.HTTPStatusError, ValueError, AttributeError) as exc:
            raise OllamaUnavailableError(
                f"Unable to reach Ollama at '{self.base_url}'. The backend will use a deterministic fallback answer."
            ) from exc

        answer = str(data.get("response", "")).strip()
        if not answer:
            raise OllamaUnavailableError(
                f"Ollama at '{self.base_url}' returned an empty response."
            )
        return answer