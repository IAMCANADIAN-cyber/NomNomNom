import requests
from .provider_base import LLMProvider

class LMStudioClient(LLMProvider):
    def __init__(self, base_url="http://127.0.0.1:1234/v1"):
        self.base_url = base_url

    def chat(self, messages, temperature=0.7, max_tokens=2048, stream=False):
        """
        Sends a chat request to the LM Studio server.
        """
        # This is a stub and does not actually make a request yet.
        print("Stub: Would make a request to LM Studio")
        return {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "This is a stub response from LM Studio."
                    }
                }
            ]
        }

    def estimate_tokens(self, text):
        """
        Estimates the number of tokens in a text.
        A simple rule of thumb is that one token is approximately 4 characters.
        """
        return len(text) // 4
