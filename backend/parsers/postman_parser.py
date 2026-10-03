import json
from typing import Dict, Any, List

def parse_postman_collection(collection_data: Dict[str, Any]) -> Dict[str, Any]:
    """Parse Postman Collection (v2.0 / v2.1) into collection and requests."""
    info = collection_data.get("info", {})
    col_name = info.get("name", "Imported Postman Collection")
    col_desc = info.get("description", "")
    
    requests: List[Dict[str, Any]] = []

    def walk_items(items: List[Dict[str, Any]], folder_prefix: str = ""):
        for item in items:
            name = item.get("name", "Untitled Request")
            full_name = f"{folder_prefix}/{name}" if folder_prefix else name
            
            if "request" in item:
                req_obj = item["request"]
                if isinstance(req_obj, str):
                    # Simple URL string
                    requests.append({
                        "name": full_name,
                        "method": "GET",
                        "url": req_obj,
                        "headers": {},
                        "body": "",
                        "body_type": "none"
                    })
                    continue
                
                method = req_obj.get("method", "GET").upper()
                
                # Extract URL
                url_obj = req_obj.get("url", "")
                if isinstance(url_obj, dict):
                    url = url_obj.get("raw", "")
                else:
                    url = str(url_obj)
                    
                # Extract headers
                headers = {}
                for h in req_obj.get("header", []):
                    if isinstance(h, dict) and not h.get("disabled", False):
                        headers[h.get("key", "")] = h.get("value", "")
                        
                # Extract body
                body = ""
                body_type = "none"
                b_obj = req_obj.get("body", {})
                if isinstance(b_obj, dict):
                    mode = b_obj.get("mode", "")
                    if mode == "raw":
                        body = b_obj.get("raw", "")
                        options = b_obj.get("options", {}).get("raw", {})
                        if options.get("language") == "json" or body.strip().startswith("{"):
                            body_type = "json"
                        else:
                            body_type = "raw"
                    elif mode == "urlencoded":
                        body_type = "form"
                        params = [f"{p.get('key')}={p.get('value')}" for p in b_obj.get("urlencoded", []) if not p.get("disabled")]
                        body = "&".join(params)
                    elif mode == "formdata":
                        body_type = "form"
                        params = [f"{p.get('key')}={p.get('value')}" for p in b_obj.get("formdata", []) if not p.get("disabled")]
                        body = "&".join(params)

                # Check for test scripts with token extraction
                extracts = []
                events = item.get("event", [])
                for ev in events:
                    if ev.get("listen") == "test":
                        script_lines = ev.get("script", {}).get("exec", [])
                        script_text = "\n".join(script_lines) if isinstance(script_lines, list) else str(script_lines)
                        # Detect pm.environment.set("...", ...) or token patterns
                        import re
                        matches = re.findall(r'pm\.(?:environment|variables)\.set\(["\']([^"\']+)["\'],\s*([^)]+)\)', script_text)
                        for var_name, source_expr in matches:
                            extracts.append({
                                "target": var_name,
                                "source": "body_json",
                                "path": var_name
                            })

                requests.append({
                    "name": full_name,
                    "method": method,
                    "url": url,
                    "headers": headers,
                    "body": body,
                    "body_type": body_type,
                    "extracts": extracts
                })
            elif "item" in item:
                # Sub-folder
                walk_items(item["item"], full_name)

    walk_items(collection_data.get("item", []))
    
    return {
        "name": col_name,
        "description": col_desc,
        "requests": requests
    }

def parse_postman_environment(env_data: Dict[str, Any]) -> Dict[str, Any]:
    """Parse Postman Environment JSON."""
    name = env_data.get("name", "Imported Environment")
    values = env_data.get("values", [])
    variables = {}
    for v in values:
        if isinstance(v, dict) and v.get("enabled", True):
            variables[v.get("key", "")] = v.get("value", "")
    return {
        "name": name,
        "variables": variables
    }
