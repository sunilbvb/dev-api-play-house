import copy
from typing import Dict, Any, List

class SideQuestGenerator:
    """Generates automated fuzzing and boundary-test side quests for APIs."""

    @staticmethod
    def generate_quests(req: Dict[str, Any]) -> List[Dict[str, Any]]:
        base_req = copy.deepcopy(req)
        quests = []

        # 1. Ghost Attack (Null / Empty Payload)
        ghost = copy.deepcopy(base_req)
        ghost["name"] = f"🎯 Side Quest 1: Ghost Attack (Null Test)"
        ghost["description"] = "Send completely blank / empty payload. Ensure backend yields proper 4xx without 500 crash."
        ghost["body"] = "{}"
        ghost["order_idx"] = 901
        ghost["xp_reward"] = 150
        quests.append(ghost)

        # 2. Armor Pierce (Boundary & Injection Fuzz)
        armor = copy.deepcopy(base_req)
        armor["name"] = f"🎯 Side Quest 2: Armor Pierce (Sanitization Fuzz)"
        armor["description"] = "Inject boundary characters, quotes, and script tags to verify backend security filters."
        armor["body"] = "{\n  \"input\": \"' OR '1'='1' -- <script>alert(1)</script>\\u0000\",\n  \"limit\": -999999\n}"
        armor["order_idx"] = 902
        armor["xp_reward"] = 250
        quests.append(armor)

        # 3. Speed Sprint (Header Stress Test)
        sprint = copy.deepcopy(base_req)
        sprint["name"] = f"🎯 Side Quest 3: Overclock Sprint (Extreme Headers)"
        sprint["description"] = "Attach oversized custom debug tracking headers to verify gateway resilience."
        headers = sprint.get("headers", {})
        headers["X-Stress-Trace"] = "A" * 512
        headers["X-Game-Overclock"] = "turbo_max_9000"
        sprint["headers"] = headers
        sprint["order_idx"] = 903
        sprint["xp_reward"] = 200
        quests.append(sprint)

        return quests
