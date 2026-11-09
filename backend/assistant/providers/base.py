from abc import ABC, abstractmethod
from dataclasses import dataclass


class AIProviderError(Exception):
    """Raised when an AI provider cannot return a valid response."""


@dataclass
class ProviderResult:
    answer: str
    model: str
    provider: str
    latency_ms: int = 0


class BaseProvider(ABC):

    @abstractmethod
    def generate(self, messages) -> ProviderResult:
        """Generate a response using this provider."""
        raise NotImplementedError
