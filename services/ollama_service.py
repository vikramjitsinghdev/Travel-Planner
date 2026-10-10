"""Small client for Ollama Cloud's /api/chat endpoint."""
import json
import os
import requests
from dotenv import load_dotenv


class OllamaCloudService:
    def __init__(self, api_key_env, model_env, default_model, timeout_env=None, default_timeout=180):
        load_dotenv()
        self.api_key = os.getenv(api_key_env) or os.getenv("OLLAMA_API_KEY")
        self.model = os.getenv(model_env, default_model)
        self.base_url = os.getenv("OLLAMA_API_URL", "https://ollama.com/api/chat").rstrip("/")
        timeout_value = os.getenv(timeout_env, str(default_timeout)) if timeout_env else str(default_timeout)
        try:
            self.timeout = max(10, int(timeout_value))
        except (TypeError, ValueError):
            self.timeout = default_timeout
        self.api_key_env = api_key_env
        if not self.api_key:
            raise RuntimeError(f"Missing {api_key_env} (or OLLAMA_API_KEY) in .env.")

    def chat_json(self, system_prompt, user_prompt, temperature=0.2):
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "format": "json",
            "stream": False,
            "options": {"temperature": temperature},
        }
        response = requests.post(
            self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            json=payload,
            timeout=self.timeout,
        )
        response.raise_for_status()
        body = response.json()
        content = (body.get("message") or {}).get("content", "")
        if not isinstance(content, str) or not content.strip():
            raise ValueError(f"{self.model} returned an empty response.")
        try:
            result = json.loads(content)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{self.model} did not return valid JSON: {content[:300]}") from exc
        if not isinstance(result, dict):
            raise ValueError(f"{self.model} must return a JSON object.")
        return result
