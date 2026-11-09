import os
import time
import requests

from .base import BaseProvider, AIProviderError, ProviderResult


class NvidiaProvider(BaseProvider):

    def generate(self, messages):
        api_key = os.getenv("NVIDIA_API_KEY", "").strip()

        base_url = os.getenv(
            "NVIDIA_BASE_URL",
            "https://integrate.api.nvidia.com/v1",
        ).rstrip("/")

        model = os.getenv(
            "NVIDIA_MODEL",
            "nvidia/nemotron-3-ultra-550b-a55b",
        ).strip()

        if (
            not api_key
            or api_key.startswith("replace_")
            or not model
        ):
            raise AIProviderError(
                "NVIDIA is not configured. Set NVIDIA_API_KEY and "
                "NVIDIA_MODEL in backend/.env."
            )

        started = time.monotonic()

        try:
            response = requests.post(
                f"{base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": 0.6,
                    "max_tokens": 900,
                    "stream": False,
                },
                timeout=(10, 120),
            )

            if response.status_code >= 400:
                raise AIProviderError(
                    f"NVIDIA API returned HTTP {response.status_code}. "
                    "Check the model ID, API key, and account access."
                )

            data = response.json()
            answer = data["choices"][0]["message"]["content"]

            if not isinstance(answer, str) or not answer.strip():
                raise AIProviderError(
                    "NVIDIA returned an empty or invalid response."
                )

            return ProviderResult(
                answer=answer.strip(),
                model=model,
                provider="nvidia",
                latency_ms=int((time.monotonic() - started) * 1000),
            )

        except requests.Timeout as exc:
            raise AIProviderError(
                "The NVIDIA request timed out."
            ) from exc

        except requests.RequestException as exc:
            raise AIProviderError(
                "Could not connect to the NVIDIA API."
            ) from exc

        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise AIProviderError(
                "NVIDIA returned an invalid response format."
            ) from exc
