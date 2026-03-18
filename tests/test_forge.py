import pytest
import asyncio
from nemoclaw_forge.forge import Forge

@pytest.mark.asyncio
async def test_forge_initialization():
    forge = Forge(redis_url="redis://localhost:6379/15")
    assert forge.redis_url == "redis://localhost:6379/15"
    assert forge._running is False
