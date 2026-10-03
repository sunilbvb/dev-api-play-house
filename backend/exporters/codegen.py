import json
from typing import Dict, Any, List

def to_curl(req: Dict[str, Any]) -> str:
    """Generate reproducible cURL command string."""
    method = req.get("method", "GET").upper()
    url = req.get("url", "")
    headers = req.get("headers", {})
    if isinstance(headers, str):
        try:
            headers = json.loads(headers)
        except Exception:
            headers = {}
    body = req.get("body", "")

    parts = [f"curl -X {method} '{url}'"]
    for k, v in headers.items():
        parts.append(f"  -H '{k}: {v}'")
        
    if body and method not in ("GET", "HEAD"):
        escaped_body = body.replace("'", "'\\''")
        parts.append(f"  --data-raw '{escaped_body}'")

    return " \\\n".join(parts)

def to_http_raw(req: Dict[str, Any]) -> str:
    """Generate RFC 7230 .http format."""
    name = req.get("name", "Untitled")
    method = req.get("method", "GET").upper()
    url = req.get("url", "")
    headers = req.get("headers", {})
    if isinstance(headers, str):
        try:
            headers = json.loads(headers)
        except Exception:
            headers = {}
    body = req.get("body", "")

    lines = [f"### {name}", f"{method} {url} HTTP/1.1"]
    for k, v in headers.items():
        lines.append(f"{k}: {v}")

    if body:
        lines.append("")
        lines.append(body)

    return "\n".join(lines)

def to_javascript_fetch(req: Dict[str, Any]) -> str:
    """Generate JS fetch code."""
    method = req.get("method", "GET").upper()
    url = req.get("url", "")
    headers = req.get("headers", {})
    if isinstance(headers, str):
        try:
            headers = json.loads(headers)
        except Exception:
            headers = {}
    body = req.get("body", "")

    options: Dict[str, Any] = {"method": method, "headers": headers}
    if body and method not in ("GET", "HEAD"):
        options["body"] = body

    return f"""fetch("{url}", {json.dumps(options, indent=2)})
  .then(response => response.json())
  .then(data => console.log(data))
  .catch(error => console.error('Error:', error));"""

def to_python_urllib(req: Dict[str, Any]) -> str:
    """Generate clean zero-dependency Python code."""
    method = req.get("method", "GET").upper()
    url = req.get("url", "")
    headers = req.get("headers", {})
    if isinstance(headers, str):
        try:
            headers = json.loads(headers)
        except Exception:
            headers = {}
    body = req.get("body", "")

    return f"""import urllib.request
import json

url = "{url}"
headers = {json.dumps(headers, indent=2)}
payload = {json.dumps(body) if body else 'None'}
data = payload.encode('utf-8') if payload else None

req = urllib.request.Request(url, data=data, headers=headers, method="{method}")

with urllib.request.urlopen(req) as resp:
    print(resp.getcode())
    print(resp.read().decode('utf-8'))
"""

def to_postman_collection(name: str, requests: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate Postman Collection v2.1 JSON."""
    items = []
    for r in requests:
        headers = r.get("headers", {})
        if isinstance(headers, str):
            try:
                headers = json.loads(headers)
            except Exception:
                headers = {}
        h_list = [{"key": k, "value": str(v), "type": "text"} for k, v in headers.items()]
        
        body_val = r.get("body", "")
        item = {
            "name": r.get("name", "Request"),
            "request": {
                "method": r.get("method", "GET").upper(),
                "header": h_list,
                "url": {
                    "raw": r.get("url", "")
                }
            }
        }
        if body_val:
            item["request"]["body"] = {
                "mode": "raw",
                "raw": body_val,
                "options": {
                    "raw": {
                        "language": "json" if body_val.strip().startswith(("{", "[")) else "text"
                    }
                }
            }
        items.append(item)

    return {
        "info": {
            "name": name,
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        },
        "item": items
    }
