import json
import time
import uuid
import random
from typing import Dict, Any

class MockGameServer:
    """Generates dynamic game API simulation responses offline."""

    @staticmethod
    def generate_response(method: str, path: str, body_str: str = "") -> Dict[str, Any]:
        path_lower = path.lower()
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        # 1. Auth & Login
        if any(k in path_lower for k in ("auth", "login", "token", "signin")):
            token = f"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.arcade_{uuid.uuid4().hex[:12]}"
            return {
                "status_code": 200,
                "headers": {"Content-Type": "application/json", "X-Sandbox-Mock": "true"},
                "body": json.dumps({
                    "success": True,
                    "access_token": token,
                    "token_type": "Bearer",
                    "expires_in": 3600,
                    "user": {
                        "id": f"player_{random.randint(100, 999)}",
                        "username": "arcade_champion",
                        "roles": ["player", "warrior"]
                    }
                }, indent=2)
            }

        # 2. Player Profile / Character
        if any(k in path_lower for k in ("player", "character", "profile", "user", "hero")):
            return {
                "status_code": 200,
                "headers": {"Content-Type": "application/json", "X-Sandbox-Mock": "true"},
                "body": json.dumps({
                    "id": "player_99",
                    "character_name": "Shadow Ninja",
                    "level": 42,
                    "health_points": 850,
                    "mana": 420,
                    "inventory": [
                        {"id": "item_01", "name": "Obsidian Blade", "rarity": "Legendary"},
                        {"id": "item_02", "name": "Elixir of Agility", "rarity": "Epic"}
                    ],
                    "gold": 14250,
                    "last_active": now
                }, indent=2)
            }

        # 3. Combat, Raid, Battle
        if any(k in path_lower for k in ("battle", "raid", "match", "dungeon", "action", "combat")):
            boss_damage = random.randint(450, 950)
            return {
                "status_code": 200,
                "headers": {"Content-Type": "application/json", "X-Sandbox-Mock": "true"},
                "body": json.dumps({
                    "match_id": f"raid_{uuid.uuid4().hex[:8]}",
                    "action_status": "CRITICAL_HIT",
                    "damage_dealt": boss_damage,
                    "boss_hp_remaining": max(0, 1000 - boss_damage),
                    "loot_awarded": ["Dragon Scale", "Arcane Core"],
                    "xp_gained": 350,
                    "timestamp": now
                }, indent=2)
            }

        # 4. High Score & Leaderboard
        if any(k in path_lower for k in ("score", "leaderboard", "rank", "stats", "history")):
            return {
                "status_code": 200,
                "headers": {"Content-Type": "application/json", "X-Sandbox-Mock": "true"},
                "body": json.dumps({
                    "leaderboard_id": "arcade_global_top",
                    "season": "Season 4 - Neon Matrix",
                    "rankings": [
                        {"rank": 1, "player": "cyber_phantom", "score": 128450},
                        {"rank": 2, "player": "shadow_ninja", "score": 99420},
                        {"rank": 3, "player": "retro_king", "score": 87310}
                    ],
                    "your_rank": 2
                }, indent=2)
            }

        # Generic default mock
        return {
            "status_code": 200,
            "headers": {"Content-Type": "application/json", "X-Sandbox-Mock": "true"},
            "body": json.dumps({
                "mock_status": "success",
                "method": method.upper(),
                "path": path,
                "timestamp": now
            }, indent=2)
        }
