from typing import List, Dict, Any

TROPHIES_CATALOG = [
    {
        "id": "speed_demon",
        "icon": "🏎️",
        "title": "Speed Demon",
        "description": "Cleared entire quest pipeline in under 250 milliseconds.",
        "xp": 300
    },
    {
        "id": "iron_gatekeeper",
        "icon": "🛡️",
        "title": "Iron Gatekeeper",
        "description": "Successfully authenticated and extracted Bearer token without flaws.",
        "xp": 200
    },
    {
        "id": "dragon_slayer",
        "icon": "🐉",
        "title": "Dragon Slayer",
        "description": "Defeated Raid Boss API with 100% pipeline victory.",
        "xp": 500
    },
    {
        "id": "archmage_variables",
        "icon": "🧙‍♂️",
        "title": "Archmage of Variables",
        "description": "Chained 3 or more dynamic variables across quest steps.",
        "xp": 350
    },
    {
        "id": "chaos_survivor",
        "icon": "⚡",
        "title": "Chaos Survivor",
        "description": "Survived and cleared the pipeline under active Boss Enrage mode!",
        "xp": 600
    }
]

class TrophyEngine:
    _unlocked: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def evaluate(cls, run_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        newly_unlocked = []
        steps = run_results.get("steps", [])
        total_steps = len(steps)
        if total_steps == 0:
            return []

        all_ok = all(200 <= (s.get("status_code") or 0) < 300 for s in steps)
        total_time = sum(s.get("elapsed_ms", 0) for s in steps)
        chained_vars = run_results.get("final_variables", {})

        # 1. Speed Demon
        if all_ok and total_time < 250 and "speed_demon" not in cls._unlocked:
            badge = next(t for t in TROPHIES_CATALOG if t["id"] == "speed_demon")
            cls._unlocked["speed_demon"] = badge
            newly_unlocked.append(badge)

        # 2. Iron Gatekeeper
        has_auth_extract = any("jwt" in str(s.get("extracted", {})).lower() or "token" in str(s.get("extracted", {})).lower() for s in steps)
        if has_auth_extract and "iron_gatekeeper" not in cls._unlocked:
            badge = next(t for t in TROPHIES_CATALOG if t["id"] == "iron_gatekeeper")
            cls._unlocked["iron_gatekeeper"] = badge
            newly_unlocked.append(badge)

        # 3. Dragon Slayer
        if all_ok and total_steps >= 2 and "dragon_slayer" not in cls._unlocked:
            badge = next(t for t in TROPHIES_CATALOG if t["id"] == "dragon_slayer")
            cls._unlocked["dragon_slayer"] = badge
            newly_unlocked.append(badge)

        # 4. Archmage of Variables
        if len(chained_vars) >= 3 and "archmage_variables" not in cls._unlocked:
            badge = next(t for t in TROPHIES_CATALOG if t["id"] == "archmage_variables")
            cls._unlocked["archmage_variables"] = badge
            newly_unlocked.append(badge)

        # 5. Chaos Survivor
        if run_results.get("chaos_mode") and all_ok and "chaos_survivor" not in cls._unlocked:
            badge = next(t for t in TROPHIES_CATALOG if t["id"] == "chaos_survivor")
            cls._unlocked["chaos_survivor"] = badge
            newly_unlocked.append(badge)

        return newly_unlocked

    @classmethod
    def get_all_trophies(cls) -> List[Dict[str, Any]]:
        result = []
        for t in TROPHIES_CATALOG:
            item = dict(t)
            item["unlocked"] = t["id"] in cls._unlocked
            result.append(item)
        return result
