import pytest
import asyncio
from unittest.mock import AsyncMock
from talos_tui.runtime.supervisor import Supervisor

@pytest.mark.asyncio
async def test_supervisor_lifecycle():
    sup = Supervisor()
    await sup.start()
    assert sup.session is not None
    assert sup.active_task_count() == 0
    await sup.stop()
    with pytest.raises(RuntimeError):
        sup.session

@pytest.mark.asyncio
async def test_supervisor_spawn_and_cancel_scope():
    sup = Supervisor()
    await sup.start()
    
    # Create a long-running dummy task
    async def dummy():
        await asyncio.sleep(10)
        
    sup.spawn(dummy(), scope="test_scope")
    assert sup.active_task_count() == 1
    
    await sup.cancel_scope("test_scope")
    # Cancellation happens via callback, give it a tick
    await asyncio.sleep(0)  
    assert sup.active_task_count() == 0
    
    await sup.stop()

@pytest.mark.asyncio
async def test_supervisor_stop_cancels_all():
    sup = Supervisor()
    await sup.start()
    
    sup.spawn(asyncio.sleep(10), scope="A")
    sup.spawn(asyncio.sleep(10), scope="B")
    assert sup.active_task_count() == 2
    
    await sup.stop()
    await asyncio.sleep(0)
    assert sup.active_task_count() == 0
