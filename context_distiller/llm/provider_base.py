from abc import ABC, abstractmethod

class LLMProvider(ABC):
    @abstractmethod
    def chat(self, messages, temperature, max_tokens, stream):
        pass

    @abstractmethod
    def estimate_tokens(self, text):
        pass
