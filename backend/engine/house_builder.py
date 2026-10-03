import os
import re
import json
import urllib.parse
from typing import List, Dict, Any, Optional

from ..parsers.curl_parser import parse_curl
from ..parsers.http_file_parser import parse_http_file
from ..parsers.markdown_parser import parse_markdown
from ..parsers.postman_parser import parse_postman_collection
from .dependency_graph import categorize_endpoint, analyze_workflow_dag

THEMES = {
    "fantasy": {
        "name": "Fantasy Dungeon & Dragons",
        "room_auth": "The Citadel Gates",
        "quest_auth": "Bypass the Gatekeeper and claim the Access Sigil",
        "room_setup": "The Armory & Sanctuary",
        "quest_setup": "Equip armor, load character stats, and inspect inventory",
        "room_action": "The Dragon's Lair",
        "quest_action": "Strike the Raid Boss with tactical battle commands",
        "room_summary": "The Hall of Champions",
        "quest_summary": "Engrave your high score and loot into the ancient ledger",
        "boss_title": "Ancient Crimson Dragon"
    },
    "cyberpunk": {
        "name": "Cyberpunk Neon Matrix",
        "room_auth": "The Firewall Breach",
        "quest_auth": "Hack mainframe security and decrypt JWT cipher",
        "room_setup": "Neural Rig & Cyberware",
        "quest_setup": "Synchronize cyberdeck specs and overclock bio-monitors",
        "room_action": "Corporate Grid Infiltration",
        "quest_action": "Overload ICE counter-measures and extract classified data",
        "room_summary": "Darknet Bounty Ledger",
        "quest_summary": "Publish exploit proof and collect cyber-credits",
        "boss_title": "Quantum ICE Guardian"
    },
    "arcade": {
        "name": "Retro 80s Arcade",
        "room_auth": "Insert Coin (Auth)",
        "quest_auth": "Drop coin in slot and verify session credit",
        "room_setup": "Select Player 1",
        "quest_setup": "Choose fighter character and load combo controls",
        "room_action": "Stage 1 Boss Fight",
        "quest_action": "Execute special moves and dodge attacks",
        "room_summary": "High Score Hall of Fame",
        "quest_summary": "Enter initials on the 3-letter high score screen",
        "boss_title": "Mecha Cyber-Demon"
    }
}

def parse_raw_api_list(text: str) -> List[Dict[str, Any]]:
    """Parse raw text containing URLs, 'METHOD URL', or mixed API references."""
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    apis = []
    
    for line in lines:
        if line.startswith("#") or line.startswith("//"):
            continue
            
        # Check if line is a cURL command
        if line.startswith("curl "):
            try:
                apis.append(parse_curl(line))
                continue
            except Exception:
                pass

        # Check if line matches 'METHOD URL'
        method_url_match = re.match(r'^(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\s+([^\s]+)$', line, re.IGNORECASE)
        if method_url_match:
            method = method_url_match.group(1).upper()
            url = method_url_match.group(2)
            parsed_path = urllib.parse.urlparse(url).path or url
            name = f"{method} {parsed_path}"
            apis.append({
                "name": name,
                "method": method,
                "url": url,
                "headers": {"Content-Type": "application/json"} if method in ("POST", "PUT", "PATCH") else {},
                "body": "{\n  \"action\": \"execute\"\n}" if method in ("POST", "PUT", "PATCH") else "",
                "body_type": "json" if method in ("POST", "PUT", "PATCH") else "none"
            })
            continue

        # If it's just a raw URL
        if line.startswith("http://") or line.startswith("https://") or line.startswith("{{") or line.startswith("/"):
            method = "POST" if any(k in line.lower() for k in ("create", "add", "send", "login", "auth", "post", "submit")) else "GET"
            parsed_path = urllib.parse.urlparse(line).path or line
            name = f"{method} {parsed_path}"
            apis.append({
                "name": name,
                "method": method,
                "url": line,
                "headers": {"Content-Type": "application/json"} if method == "POST" else {},
                "body": "{}" if method == "POST" else "",
                "body_type": "json" if method == "POST" else "none"
            })

    return apis

def scan_workspace_for_apis(workspace_dir: str) -> List[Dict[str, Any]]:
    """Recursively scan a folder for .http, .rest, Postman .json, and .md files."""
    if not os.path.exists(workspace_dir):
        return []

    collected_apis = []

    for root, _, files in os.walk(workspace_dir):
        for file in files:
            file_path = os.path.join(root, file)
            ext = os.path.splitext(file)[1].lower()

            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                if ext in (".http", ".rest"):
                    collected_apis.extend(parse_http_file(content))
                elif ext == ".json":
                    try:
                        data = json.loads(content)
                        if isinstance(data, dict) and ("item" in data or "info" in data):
                            parsed_col = parse_postman_collection(data)
                            collected_apis.extend(parsed_col.get("requests", []))
                    except Exception:
                        pass
                elif ext in (".md", ".markdown"):
                    collected_apis.extend(parse_markdown(content))
            except Exception:
                pass

    return collected_apis

def auto_generate_game_house(
    raw_apis: List[Dict[str, Any]], 
    house_name: str = "Arcade Game House", 
    theme_key: str = "arcade"
) -> Dict[str, Any]:
    """
    Transform raw list of APIs into a structured Game House with Rooms, Quests, XP and Boss Battle.
    """
    theme = THEMES.get(theme_key, THEMES["arcade"])
    dag_analysis = analyze_workflow_dag(raw_apis)
    ordered = dag_analysis.get("ordered_requests", raw_apis)

    rooms = {
        "gatekeeper": {
            "room_name": theme["room_auth"],
            "quest_desc": theme["quest_auth"],
            "tier": 0,
            "xp_reward": 100,
            "requests": []
        },
        "armory": {
            "room_name": theme["room_setup"],
            "quest_desc": theme["quest_setup"],
            "tier": 1,
            "xp_reward": 200,
            "requests": []
        },
        "coliseum": {
            "room_name": theme["room_action"],
            "quest_desc": theme["quest_action"],
            "tier": 2,
            "xp_reward": 350,
            "requests": []
        },
        "vault": {
            "room_name": theme["room_summary"],
            "quest_desc": theme["quest_summary"],
            "tier": 3,
            "xp_reward": 500,
            "requests": []
        }
    }

    # Distribute requests into rooms
    for req in ordered:
        cat = categorize_endpoint(req)
        # Ensure extracts for auth
        extracts = req.get("extracts", [])
        if isinstance(extracts, str):
            try: extracts = json.loads(extracts)
            except Exception: extracts = []

        if cat == "Authentication & Session":
            if not any(e.get("target") == "jwt_token" for e in extracts):
                extracts.append({"target": "jwt_token", "source": "body_json", "path": "token"})
            req["extracts"] = extracts
            req["quest_title"] = f"Quest: Authenticate & Loot Token"
            rooms["gatekeeper"]["requests"].append(req)

        elif cat == "Player & Character Setup":
            if not any(e.get("target") == "player_id" for e in extracts):
                extracts.append({"target": "player_id", "source": "body_json", "path": "id"})
            req["extracts"] = extracts
            req["quest_title"] = f"Quest: Synchronize Player Stats"
            rooms["armory"]["requests"].append(req)

        elif cat == "Leaderboard & Scoring":
            req["quest_title"] = f"Quest: Engrave Record in Vault"
            rooms["vault"]["requests"].append(req)

        else:
            # Action / Gameplay
            req["quest_title"] = f"Quest: Execute Battle Move"
            rooms["coliseum"]["requests"].append(req)

    # Designate a Raid Boss
    boss_request = None
    if rooms["coliseum"]["requests"]:
        boss_request = rooms["coliseum"]["requests"][-1]
    elif rooms["armory"]["requests"]:
        boss_request = rooms["armory"]["requests"][-1]
    elif ordered:
        boss_request = ordered[-1]

    boss_info = {
        "name": theme["boss_title"],
        "request_id": boss_request.get("id") if boss_request else None,
        "request_name": boss_request.get("name") if boss_request else "Boss Strike API",
        "boss_hp": 1000,
        "weakness": "Requires Bearer token and latency < 400ms"
    }

    total_quests = sum(len(r["requests"]) for r in rooms.values())
    total_xp = sum(len(r["requests"]) * r["xp_reward"] for r in rooms.values())

    return {
        "house_name": house_name,
        "theme": theme["name"],
        "theme_key": theme_key,
        "boss": boss_info,
        "stats": {
            "total_rooms": 4,
            "total_quests": total_quests,
            "total_xp_possible": total_xp,
            "starting_hp": 100
        },
        "rooms": rooms,
        "ordered_sequence": ordered
    }
