import json
import time
from typing import List, Dict, Any

class ReplayRecorder:
    """Records session frames for time-travel replay and debug scrub."""
    _current_session_frames: List[Dict[str, Any]] = []

    @classmethod
    def record_frame(cls, step_num: int, request_meta: Dict[str, Any], response_meta: Dict[str, Any], variables_snapshot: Dict[str, Any]):
        frame = {
            "frame_id": len(cls._current_session_frames) + 1,
            "step": step_num,
            "timestamp": time.time(),
            "time_str": time.strftime("%H:%M:%S", time.localtime()),
            "request": request_meta,
            "response": response_meta,
            "variables": variables_snapshot
        }
        cls._current_session_frames.append(frame)
        return frame

    @classmethod
    def get_frames(cls) -> List[Dict[str, Any]]:
        return cls._current_session_frames

    @classmethod
    def clear(cls):
        cls._current_session_frames = []

    @classmethod
    def export_session(cls) -> str:
        return json.dumps({
            "replay_format": "playhouse_tape_v1",
            "recorded_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            "total_frames": len(cls._current_session_frames),
            "frames": cls._current_session_frames
        }, indent=2)
