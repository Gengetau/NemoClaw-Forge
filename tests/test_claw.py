import pytest
import asyncio
from nemoclaw_forge.claw import Claw
from nemoclaw_forge.brain import Brain
from nemoclaw_forge.sandbox import Sandbox

@pytest.mark.asyncio
async def test_claw_initialization():
    claw = Claw(worker_id="test-worker", redis_url="redis://localhost:6379/15")
    assert claw.worker_id == "test-worker"
    assert claw._running is False
    assert isinstance(claw.brain, Brain)
    assert isinstance(claw.sandbox, Sandbox)

@pytest.mark.asyncio
async def test_brain_failover():
    brain = Brain(primary_model="nemotron-3", fallbacks=["gemini-pro"])
    
    # Test primary fail
    result = await brain.execute("trigger fail please")
    assert "[gemini-pro]" in result
    
    # Test primary success
    result = await brain.execute("normal prompt")
    assert "[nemotron-3]" in result
