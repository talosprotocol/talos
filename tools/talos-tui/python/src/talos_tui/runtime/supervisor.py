from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Awaitable, Callable, Dict, Optional, Set
from aiohttp import ClientSession

TaskFactory = Callable[[], Awaitable[None]]

@dataclass
class Supervisor:
    _tasks: Set[asyncio.Task] = field(default_factory=set)
    _scoped: Dict[str, Set[asyncio.Task]] = field(default_factory=dict)
    _closed: bool = False
    _session: Optional[ClientSession] = None

    async def start(self) -> None:
        """Initialize resources."""
        self._session = ClientSession()

    def spawn(self, coro: Awaitable[None], *, scope: Optional[str] = None) -> asyncio.Task:
        if self._closed:
            raise RuntimeError("Supervisor is closed")

        task = asyncio.create_task(coro)
        self._tasks.add(task)
        if scope:
            self._scoped.setdefault(scope, set()).add(task)

        def _done(_t: asyncio.Task) -> None:
            self._tasks.discard(_t)
            for s in list(self._scoped.keys()):
                if s in self._scoped:
                    self._scoped[s].discard(_t)
                    if not self._scoped[s]:
                        self._scoped.pop(s, None)

        task.add_done_callback(_done)
        return task

    async def cancel_scope(self, scope: str) -> None:
        tasks = list(self._scoped.get(scope, set()))
        for t in tasks:
            t.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        self._scoped.pop(scope, None)

    async def cancel_all(self) -> None:
        tasks = list(self._tasks)
        for t in tasks:
            t.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        self._tasks.clear()
        self._scoped.clear()

    async def stop(self) -> None:
        self._closed = True
        await self.cancel_all()
        if self._session and not self._session.closed:
            await self._session.close()
        self._session = None

    @property
    def session(self) -> ClientSession:
        if not self._session:
            raise RuntimeError("Supervisor not started")
        return self._session

    def active_task_count(self) -> int:
        return len(self._tasks)
