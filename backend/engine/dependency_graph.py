import re
import json
from typing import List, Dict, Any, Set

AUTH_KEYWORDS = ["auth", "login", "token", "signin", "oauth", "session", "authenticate", "register"]
PLAYER_KEYWORDS = ["player", "user", "profile", "character", "hero", "avatar", "account", "wallet"]
GAMEPLAY_KEYWORDS = ["game", "play", "match", "dungeon", "battle", "raid", "quest", "inventory", "item", "action", "level", "spawn"]
SUMMARY_KEYWORDS = ["score", "leaderboard", "rank", "result", "stats", "logout", "history", "achievement"]

def extract_used_variables(req: Dict[str, Any]) -> Set[str]:
    """Find all {{var_name}} references in url, headers, and body."""
    found = set()
    pattern = re.compile(r'\{\{([a-zA-Z0-9_\-\$]+)\}\}')
    
    # Check URL
    url = req.get("url", "")
    for m in pattern.finditer(url):
        if not m.group(1).startswith("$"):
            found.add(m.group(1))
            
    # Check Headers
    headers = req.get("headers", {})
    if isinstance(headers, str):
        try:
            headers = json.loads(headers)
        except Exception:
            headers = {}
    for k, v in headers.items():
        for m in pattern.finditer(f"{k} {v}"):
            if not m.group(1).startswith("$"):
                found.add(m.group(1))

    # Check Body
    body = req.get("body", "")
    for m in pattern.finditer(body):
        if not m.group(1).startswith("$"):
            found.add(m.group(1))
            
    return found

def extract_produced_variables(req: Dict[str, Any]) -> Set[str]:
    """Find all variables that this request extracts or produces."""
    produced = set()
    extracts = req.get("extracts", [])
    if isinstance(extracts, str):
        try:
            extracts = json.loads(extracts)
        except Exception:
            extracts = []
            
    for item in extracts:
        if isinstance(item, dict) and item.get("target"):
            produced.add(item.get("target"))

    # Implicit production based on common endpoints
    name_lower = (req.get("name", "") + " " + req.get("url", "")).lower()
    if any(k in name_lower for k in AUTH_KEYWORDS):
        produced.add("jwt_token")
        produced.add("auth_token")
        produced.add("token")
        
    return produced

def categorize_endpoint(req: Dict[str, Any]) -> str:
    """Classify endpoint into game lifecycle category."""
    text = f"{req.get('name', '')} {req.get('url', '')}".lower()
    
    if any(k in text for k in AUTH_KEYWORDS):
        return "Authentication & Session"
    if any(k in text for k in PLAYER_KEYWORDS):
        return "Player & Character Setup"
    if any(k in text for k in GAMEPLAY_KEYWORDS):
        return "Gameplay & Mechanics"
    if any(k in text for k in SUMMARY_KEYWORDS):
        return "Leaderboard & Scoring"
        
    method = req.get("method", "GET").upper()
    if method == "POST":
        return "Game Action / Command"
    return "Data Explorer"

def analyze_workflow_dag(requests: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Build dependency graph and determine optimal execution order.
    Returns nodes, edges, categories, and suggested execution sequence.
    """
    nodes = []
    node_map = {}
    
    for r in requests:
        req_id = r.get("id") or r.get("name")
        consumed = extract_used_variables(r)
        produced = extract_produced_variables(r)
        category = categorize_endpoint(r)
        
        # Calculate base priority level
        if category == "Authentication & Session":
            base_tier = 0
        elif category == "Player & Character Setup":
            base_tier = 1
        elif category == "Gameplay & Mechanics" or category == "Game Action / Command":
            base_tier = 2
        elif category == "Leaderboard & Scoring":
            base_tier = 3
        else:
            base_tier = 4

        node = {
            "id": req_id,
            "name": r.get("name"),
            "method": r.get("method", "GET"),
            "url": r.get("url"),
            "category": category,
            "base_tier": base_tier,
            "consumed_variables": list(consumed),
            "produced_variables": list(produced),
            "original_request": r
        }
        nodes.append(node)
        node_map[req_id] = node

    # Construct directed edges based on variable dependencies
    edges = []
    dep_graph: Dict[Any, Set[Any]] = {n["id"]: set() for n in nodes}

    for consumer in nodes:
        for consumed_var in consumer["consumed_variables"]:
            # Find producers of this variable
            for producer in nodes:
                if producer["id"] != consumer["id"] and consumed_var in producer["produced_variables"]:
                    edges.append({
                        "from": producer["id"],
                        "to": consumer["id"],
                        "variable": consumed_var
                    })
                    dep_graph[consumer["id"]].add(producer["id"])

    # Topological Sort with tie-breaking by base_tier and order_idx
    visited = set()
    visiting = set()
    order = []

    def visit(node_id):
        if node_id in visiting:
            # Cycle detected, break to avoid infinite loop
            return
        if node_id not in visited:
            visiting.add(node_id)
            # Visit all dependencies first
            for dep_id in sorted(dep_graph.get(node_id, []), key=lambda x: node_map[x]["base_tier"]):
                visit(dep_id)
            visiting.remove(node_id)
            visited.add(node_id)
            order.append(node_map[node_id])

    # Sort initial candidates by base_tier to prioritize auth -> player -> game -> leaderboard
    sorted_nodes = sorted(nodes, key=lambda x: (x["base_tier"], x.get("original_request", {}).get("order_idx", 0)))
    
    for n in sorted_nodes:
        if n["id"] not in visited:
            visit(n["id"])

    return {
        "nodes": nodes,
        "edges": edges,
        "recommended_sequence": [n["id"] for n in order],
        "ordered_requests": [n["original_request"] for n in order]
    }
