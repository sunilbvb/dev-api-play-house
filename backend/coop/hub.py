import time
import json
from typing import List, Dict, Any

class CoopHub:
    """In-memory event broadcaster for local co-op multi-developer pairing."""
    _events: List[Dict[str, Any]] = []

    @classmethod
    def publish(cls, event_type: str, actor: str, message: str, meta: Dict[str, Any] = None):
        event = {
            "id": len(cls._events) + 1,
            "type": event_type,
            "actor": actor,
            "message": message,
            "meta": meta or {},
            "timestamp": time.strftime("%H:%M:%S", time.localtime())
        }
        cls._events.append(event)
        # Keep last 100 events
        if len(cls._events) > 100:
            cls._events.pop(0)
        return event

    @classmethod
    def get_events(cls, since_id: int = 0) -> List[Dict[str, Any]]:
        return [e for e in cls._events if e["id"] > since_id]
