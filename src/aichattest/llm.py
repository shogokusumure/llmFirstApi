import os

import httpx


class OllamaResponseError(Exception):
    pass


def generate_assistant_reply(messages: list[dict[str, str]]) -> str:
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
    model = os.getenv("OLLAMA_MODEL", "gemma2:2b")
    response = httpx.post(
        f"{base_url}/api/chat",
        json={"model": model, "messages": messages, "stream": False},
        timeout=120.0,
    )
    response.raise_for_status()

    try:
        data = response.json()
    except ValueError as exc:
        raise OllamaResponseError("Ollama returned invalid JSON") from exc

    if not isinstance(data, dict):
        raise OllamaResponseError("Ollama returned an invalid response")

    message = data.get("message")
    if not isinstance(message, dict):
        raise OllamaResponseError("Ollama response is missing a message")

    content = message.get("content")
    if not isinstance(content, str) or not content.strip():
        raise OllamaResponseError("Ollama response is missing message content")

    return content
