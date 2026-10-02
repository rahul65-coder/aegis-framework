"""Real Gemini Provider Adapter for Phase 11."""
import os
import requests

class RealGeminiProvider:
    def __init__(self, model_id="gemini-2.5-flash"):
        self.api_key = os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not set in environment")
        self.model_id = model_id
        self.url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_id}:generateContent?key={self.api_key}"
        
    def call(self, prompt: str) -> dict:
        headers = {
            "Content-Type": "application/json"
        }
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }
        response = requests.post(self.url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()
        
        content = data["candidates"][0]["content"]["parts"][0]["text"]
        usage = data.get("usageMetadata", {})
        input_tokens = usage.get("promptTokenCount", 0)
        output_tokens = usage.get("candidatesTokenCount", 0)
        
        return {
            "content": content,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens
        }
