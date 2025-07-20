from .provider_base import LLMProvider

class LMStudioProvider(LLMProvider):
    """LM Studio provider."""

    def chat(self, messages: list, temperature: float, max_tokens: int, stream: bool) -> str:
        """Chats with the LLM."""
        pass

    def estimate_tokens(self, text: str) -> int:
        """Estimates the number of tokens in a text."""
        pass
