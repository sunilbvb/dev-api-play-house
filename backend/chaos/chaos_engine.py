import time
import random
from typing import Dict, Any, Optional

class ChaosEngine:
    """Simulates API failure conditions, network latency, and corruptions."""

    @staticmethod
    def apply_chaos(request_config: Dict[str, Any], chaos_level: str = "medium") -> Optional[Dict[str, Any]]:
        """
        If chaos is triggered, returns a simulated chaotic response or delays execution.
        Returns None if normal execution should proceed.
        """
        if chaos_level == "off":
            return None

        # Chance of failure based on chaos level
        failure_rates = {
            "light": 0.20,
            "medium": 0.40,
            "insane": 0.75
        }
        chance = failure_rates.get(chaos_level, 0.3)

        # Inject latency delay
        latency_boost = 0
        if chaos_level == "light":
            latency_boost = random.uniform(0.1, 0.3)
        elif chaos_level == "medium":
            latency_boost = random.uniform(0.3, 0.9)
        elif chaos_level == "insane":
            latency_boost = random.uniform(0.8, 2.0)

        time.sleep(latency_boost)

        if random.random() < chance:
            chaos_type = random.choice(["rate_limit", "server_error", "timeout", "bad_gateway", "corrupt_token"])

            if chaos_type == "rate_limit":
                return {
                    "status_code": 429,
                    "elapsed_ms": round(latency_boost * 1000, 2),
                    "headers": {"Retry-After": "30", "Content-Type": "application/json"},
                    "body": "{\n  \"error\": \"Too Many Requests\",\n  \"message\": \"[CHAOS ENRAGE] Rate limit triggered by Boss Shield\"\n}",
                    "is_json": True,
                    "error": "Chaos: 429 Too Many Requests",
                    "sent": request_config
                }

            elif chaos_type == "server_error":
                return {
                    "status_code": 500,
                    "elapsed_ms": round(latency_boost * 1000, 2),
                    "headers": {"Content-Type": "application/json"},
                    "body": "{\n  \"error\": \"Internal Server Error\",\n  \"message\": \"[CHAOS ENRAGE] Database deadlock induced by Raid Boss Roar\"\n}",
                    "is_json": True,
                    "error": "Chaos: 500 Server Error",
                    "sent": request_config
                }

            elif chaos_type == "bad_gateway":
                return {
                    "status_code": 502,
                    "elapsed_ms": round(latency_boost * 1000, 2),
                    "headers": {"Content-Type": "text/plain"},
                    "body": "[CHAOS ENRAGE] 502 Bad Gateway: Upstream game server disconnected.",
                    "is_json": False,
                    "error": "Chaos: 502 Bad Gateway",
                    "sent": request_config
                }

            elif chaos_type == "corrupt_token":
                return {
                    "status_code": 401,
                    "elapsed_ms": round(latency_boost * 1000, 2),
                    "headers": {"Content-Type": "application/json"},
                    "body": "{\n  \"error\": \"Unauthorized\",\n  \"message\": \"[CHAOS ENRAGE] Signature corrupted by EMP blast\"\n}",
                    "is_json": True,
                    "error": "Chaos: 401 Token Corruption",
                    "sent": request_config
                }

        return None
