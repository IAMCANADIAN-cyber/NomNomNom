import requests
import json
import hashlib
from sqlalchemy.orm import Session
from context_distiller.core.db import LLMCache

class LMStudioClient:
    def __init__(self, session: Session, base_url: str = "http://localhost:1234/v1"):
        self.base_url = base_url
        self.session = session

    def _get_cache(self, key_hash: str):
        return self.session.query(LLMCache).filter_by(key_hash=key_hash).first()

    def _set_cache(self, key_hash: str, request_json: dict, response_text: str, usage: dict):
        new_cache_entry = LLMCache(
            key_hash=key_hash,
            request_json=request_json,
            response_text=response_text,
            input_tokens=usage.get('prompt_tokens', 0),
            output_tokens=usage.get('completion_tokens', 0)
        )
        self.session.add(new_cache_entry)
        self.session.commit()

    def chat(self, messages: list, temperature: float = 0.7, max_tokens: int = 2000):
        """
        Sends a chat completion request to the LM Studio server.
        """
        endpoint = f"{self.base_url}/chat/completions"

        request_data = {
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        # Check cache
        request_string = json.dumps(request_data, sort_keys=True)
        key_hash = hashlib.sha256(request_string.encode('utf-8')).hexdigest()

        cached_response = self._get_cache(key_hash)
        if cached_response:
            print("Returning cached LLM response.")
            return cached_response.response_text

        headers = {"Content-Type": "application/json"}

        try:
            print("Querying LLM...")
            response = requests.post(endpoint, headers=headers, json=request_data, timeout=120) # 120-second timeout
            response.raise_for_status() # Raise an exception for bad status codes

            data = response.json()
            response_text = data['choices'][0]['message']['content']
            usage = data.get('usage', {})

            # Save to cache
            self._set_cache(key_hash, request_data, response_text, usage)

            return response_text

        except requests.exceptions.RequestException as e:
            print(f"Error connecting to LM Studio server: {e}")
            return None
        except (KeyError, IndexError) as e:
            print(f"Error parsing LLM response: {e}")
            print(f"Response JSON: {response.text}")
            return None
