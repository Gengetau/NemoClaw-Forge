import asyncio
import logging
import aiohttp
import os
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

class Brain:
    """Pluggable LLM Connector with Multi-Model Failover and real API support."""
    
    def __init__(self, primary_model: str = "nvidia/nemotron-3-super-120b-a12b", fallbacks: List[str] = None):
        self.primary_model = primary_model
        self.fallbacks = fallbacks or ["nvidia/minimaxai/minimax-m2.5"]
        self.api_key = os.environ.get("NVIDIA_API_KEY")
        self.base_url = "https://integrate.api.nvidia.com/v1"
        
    async def _call_model(self, model: str, prompt: str) -> str:
        if not self.api_key:
            # Fallback to mock if no API key
            logger.warning("No NVIDIA_API_KEY found, falling back to mock response.")
            return f"[MOCK:{model}] Data: {prompt[:100]}..."

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.5,
            "max_tokens": 1024
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(f"{self.base_url}/chat/completions", headers=headers, json=payload) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data['choices'][0]['message']['content']
                    else:
                        err_text = await resp.text()
                        raise RuntimeError(f"API Error ({resp.status}): {err_text}")
            except Exception as e:
                logger.error(f"Error calling model {model}: {e}")
                raise

    async def execute(self, prompt: str) -> str:
        """Execute prompt with failover."""
        models_to_try = [self.primary_model] + self.fallbacks
        
        for model in models_to_try:
            try:
                result = await self._call_model(model, prompt)
                return result
            except Exception as e:
                logger.warning(f"Model {model} failed: {e}. Falling back...")
                continue
                
        raise RuntimeError("All models failed to process the request.")
