from ..providers.base import AIProviderError
from ..providers.ollama import OllamaProvider
from ..providers.nvidia import NvidiaProvider


class AIRouter:

    def __init__(self):
        self.local_provider = OllamaProvider()
        self.nvidia_provider = NvidiaProvider()

    def generate(self, messages, privacy_mode="local", allow_cloud=False):
        if not isinstance(privacy_mode, str):
            raise AIProviderError("Invalid privacy_mode.")

        if not isinstance(allow_cloud, bool):
            raise AIProviderError("allow_cloud must be true or false.")

        mode = privacy_mode.strip().lower()

        if mode not in {"local", "cloud", "hybrid"}:
            raise AIProviderError(
                "Invalid privacy_mode. Use local, cloud, or hybrid."
            )

        # Local mode never contacts a cloud provider.
        if mode == "local":
            return self.local_provider.generate(messages)

        # Explicit permission is mandatory for every cloud request.
        if not allow_cloud:
            return self.local_provider.generate(messages)

        # Cloud mode: NVIDIA only.
        if mode == "cloud":
            return self.nvidia_provider.generate(messages)

        # Hybrid mode: NVIDIA first, local fallback.
        try:
            return self.nvidia_provider.generate(messages)

        except AIProviderError as cloud_error:
            try:
                result = self.local_provider.generate(messages)
                result.provider = "local_fallback"
                return result

            except AIProviderError as local_error:
                raise AIProviderError(
                    f"Cloud request failed ({cloud_error}). "
                    f"Local fallback also failed ({local_error})."
                ) from local_error


_default_router = AIRouter()


def generate_reply(messages, privacy_mode="local", allow_cloud=False):
    result = _default_router.generate(
        messages,
        privacy_mode=privacy_mode,
        allow_cloud=allow_cloud,
    )

    return result.answer, result.model, result.provider
