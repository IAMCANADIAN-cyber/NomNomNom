from abc import ABC, abstractmethod

class LLMProvider(ABC):
    """Base class for LLM providers."""

    @abstractmethod
    def chat(self, messages: list, temperature: float, max_tokens: int, stream: bool) -> str:
        """Chats with the LLM."""
        pass

    @abstractmethod
    def estimate_tokens(self, text: str) -> int:
        """Estimates the number of tokens in a text."""
        pass
