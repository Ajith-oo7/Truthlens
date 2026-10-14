from __future__ import annotations

import asyncio
from collections import defaultdict

from app.models.schemas import PipelineEvent


class EventBroker:
    def __init__(self) -> None:
        self._queues: dict[str, list[asyncio.Queue]] = defaultdict(list)
        self._history: dict[str, list[PipelineEvent]] = defaultdict(list)

    def publish(self, fact_id: str, event: PipelineEvent) -> None:
        self._history[fact_id].append(event)
        for queue in list(self._queues[fact_id]):
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                pass

    def subscribe(self, fact_id: str) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue()
        self._queues[fact_id].append(queue)
        for event in self._history[fact_id]:
            queue.put_nowait(event)
        return queue

    def unsubscribe(self, fact_id: str, queue: asyncio.Queue) -> None:
        if queue in self._queues[fact_id]:
            self._queues[fact_id].remove(queue)


broker = EventBroker()
