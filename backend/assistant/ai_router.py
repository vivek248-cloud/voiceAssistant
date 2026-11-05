import os
import requests


class AIProviderError(Exception):
    """Raised when an AI provider cannot return a valid response."""


def _call_ollama(messages):
    base_url = os.getenv(
        "OLLAMA_BASE_URL", "http://127.0.0.1:11434"
    ).rstrip("/")
    model = os.getenv(
        "OLLAMA_MODEL", "qwen2.5:1.5b-instruct"
    ).strip()

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

        return answer.strip(), model

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


def _call_nvidia(messages):
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

        return answer.strip(), model

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


def generate_reply(messages, privacy_mode="local", allow_cloud=False):
    """
    local:
        Always use Ollama on this VPS.

    cloud:
        Use NVIDIA only when allow_cloud is True.

    hybrid:
        Use NVIDIA only when allow_cloud is True.
        If NVIDIA fails, fall back to local Ollama.
    """

    if not isinstance(privacy_mode, str):
        raise AIProviderError("Invalid privacy_mode.")

    if not isinstance(allow_cloud, bool):
        raise AIProviderError("allow_cloud must be true or false.")

    mode = privacy_mode.strip().lower()

    if mode not in {"local", "cloud", "hybrid"}:
        raise AIProviderError(
            "Invalid privacy_mode. Use local, cloud, or hybrid."
        )

    # Local mode must never contact NVIDIA.
    if mode == "local":
        answer, model = _call_ollama(messages)
        return answer, model, "local"

    # Without explicit cloud permission, remain local.
    if not allow_cloud:
        answer, model = _call_ollama(messages)
        return answer, model, "local"

    # Cloud mode uses NVIDIA only.
    if mode == "cloud":
        answer, model = _call_nvidia(messages)
        return answer, model, "nvidia"

    # Hybrid mode: NVIDIA first, local fallback.
    try:
        answer, model = _call_nvidia(messages)
        return answer, model, "nvidia"

    except AIProviderError as cloud_error:
        try:
            answer, model = _call_ollama(messages)
            return answer, model, "local_fallback"

        except AIProviderError as local_error:
            raise AIProviderError(
                f"Cloud request failed ({cloud_error}). "
                f"Local fallback also failed ({local_error})."
            ) from local_error
