import json
import re
from typing import Dict, Any, List, Optional

def extract_nested_value(data: Any, path: str) -> Any:
    """Traverse a Python object using dot-notation, e.g. 'data.user.id' or 'items[0].id'."""
    if not path or data is None:
        return data

    # Normalize array brackets: items[0] -> items.0
    normalized_path = re.sub(r'\[(\d+)\]', r'.\1', path)
    parts = normalized_path.split('.')
    
    current = data
    for part in parts:
        if not part:
            continue
        if isinstance(current, dict):
            if part in current:
                current = current[part]
            else:
                return None
        elif isinstance(current, (list, tuple)):
            try:
                idx = int(part)
                if 0 <= idx < len(current):
                    current = current[idx]
                else:
                    return None
            except ValueError:
                return None
        else:
            return None
            
    return current

def extract_variables(
    extract_rules: List[Dict[str, Any]], 
    status_code: int, 
    headers: Dict[str, str], 
    response_body: str
) -> Dict[str, Any]:
    """
    Execute extraction rules against response data.
    Rule format:
    {
      "target": "jwt_token",
      "source": "body_json" | "header" | "regex" | "status",
      "path": "data.token" | "Authorization" | "token=([a-zA-Z0-9]+)"
    }
    """
    extracted = {}
    parsed_json = None
    
    for rule in extract_rules:
        target = rule.get("target")
        source = rule.get("source", "body_json")
        path = rule.get("path", "")
        
        if not target:
            continue

        if source == "status":
            extracted[target] = status_code

        elif source == "header":
            # Case-insensitive header lookup
            header_key_lower = path.lower()
            val = None
            for hk, hv in headers.items():
                if hk.lower() == header_key_lower:
                    val = hv
                    break
            if val is not None:
                extracted[target] = val

        elif source == "body_json":
            if parsed_json is None:
                try:
                    parsed_json = json.loads(response_body)
                except Exception:
                    parsed_json = {}
            val = extract_nested_value(parsed_json, path)
            if val is not None:
                extracted[target] = val

        elif source == "regex":
            try:
                match = re.search(path, response_body)
                if match:
                    extracted[target] = match.group(1) if match.groups() else match.group(0)
            except Exception:
                pass

    return extracted
