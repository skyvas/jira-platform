"""Server-Sent Events (SSE) Broadcaster for real-time board updates."""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Dict, Set

logger = logging.getLogger(__name__)


class EventBroadcaster:
    """Manages active SSE client subscriber queues and event dispatching."""

    def __init__(self) -> None:
        self._subscribers: Set[asyncio.Queue] = set()

    def subscribe(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=100)
        self._subscribers.add(q)
        return q

    def unsubscribe(self, q: asyncio.Queue) -> None:
        self._subscribers.discard(q)

    def publish(self, event_type: str, data: Dict[str, Any]) -> None:
        """Publish an event to all active SSE subscribers."""
        payload = {
            "type": event_type,
            "data": data,
        }
        message = f"event: {event_type}\ndata: {json.dumps(payload)}\n\n"
        dead_queues = []
        for q in list(self._subscribers):
            try:
                q.put_nowait(message)
            except asyncio.QueueFull:
                dead_queues.append(q)
            except Exception:
                dead_queues.append(q)

        for q in dead_queues:
            self.unsubscribe(q)

    def subscriber_count(self) -> int:
        return len(self._subscribers)


broadcaster = EventBroadcaster()
