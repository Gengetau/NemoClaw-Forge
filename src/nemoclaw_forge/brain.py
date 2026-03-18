import asyncio
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

class Brain:
    """Pluggable LLM Connector with Multi-Model Failover logic."""
    
    def __init__(self, primary_model: str = "nemotron-3", fallbacks: List[str] = None):
        self.primary_model = primary_model
        self.fallbacks = fallbacks or ["gemini-pro", "gpt-4"]
        
    async def _call_model(self, model: str, prompt: str) -> str:
        # Mocking an async LLM API call using aiohttp in real life
        logger.info(f"Routing request to model: {model}")
        await asyncio.sleep(0.5) # Simulate latency
        
        # Simulate primary model failure
        if model == "nemotron-3" and "fail" in prompt.lower():
            raise TimeoutError(f"{model} timed out or returned an error.")
            
        return f"[{model}] Response to: {prompt}"

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
