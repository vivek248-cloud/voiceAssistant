import os
import time
import requests

from .base import BaseProvider, AIProviderError, ProviderResult


class OllamaProvider(BaseProvider):

    def generate(self, messages):
        base_url = os.getenv(
            "OLLAMA_BASE_URL",
            "http://127.0.0.1:11434"
        ).rstrip("/")

        model = os.getenv(
            "OLLAMA_MODEL",
            "qwen2.5:1.5b-instruct"
        ).strip()

        if not model:
            raise AIProviderError("OLLAMA_MODEL is not configured.")

        started = time.monotonic()

        try:
            response = requests.post(
                f"{base_url}/api/chat",
                json={
                    "model": model,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "num_ctx": 2048,
                        "num_predict": 700,
                    },
                },
                timeout=(5, 120),
            )

            if response.status_code >= 400:
                raise AIProviderError(
                    f"Ollama returned HTTP {response.status_code}. "
                    "Check that the model is installed on the VPS."
                )

            data = response.json()
            answer = data.get("message", {}).get("content", "")

            if not isinstance(answer, str) or not answer.strip():
                raise AIProviderError(
                    "Ollama returned an empty or invalid response."
                )

            return ProviderResult(
                answer=answer.strip(),
                model=model,
                provider="local",
                latency_ms=int((time.monotonic() - started) * 1000),
            )

        except requests.Timeout as exc:
            raise AIProviderError(
                "The local Ollama request timed out."
            ) from exc

        except requests.RequestException as exc:
            raise AIProviderError(
                "Cannot reach local Ollama. Make sure Ollama is running on this VPS."
            ) from exc

        except ValueError as exc:
            raise AIProviderError(
                "Ollama returned invalid JSON."
            ) from exc
