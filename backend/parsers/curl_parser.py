import re
import shlex
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse

def parse_curl(curl_command: str) -> Dict[str, Any]:
    """Parse a cURL command into an API request dictionary."""
    text = curl_command.strip()
    # Normalize escaped newlines
    text = text.replace('\\\n', ' ').replace('\\\r\n', ' ')
    
    # Try shlex split
    try:
        tokens = shlex.split(text)
    except Exception:
        tokens = text.split()

    method = "GET"
    url = ""
    headers: Dict[str, str] = {}
    data_parts: List[str] = []
    
    i = 0
    while i < len(tokens):
        token = tokens[i]
        
        if token == "curl":
            i += 1
            continue
            
        if token in ("-X", "--request") and i + 1 < len(tokens):
            method = tokens[i + 1].upper()
            i += 2
            continue
            
        if token in ("-H", "--header") and i + 1 < len(tokens):
            header_val = tokens[i + 1]
            if ":" in header_val:
                k, v = header_val.split(":", 1)
                headers[k.strip()] = v.strip()
            i += 2
            continue
            
        if token in ("-d", "--data", "--data-raw", "--data-binary", "--data-urlencode") and i + 1 < len(tokens):
            data_parts.append(tokens[i + 1])
            if method == "GET":
                method = "POST"
            i += 2
            continue
            
        if token in ("-u", "--user") and i + 1 < len(tokens):
            auth_val = tokens[i + 1]
            headers["Authorization"] = f"Basic {auth_val}"
            i += 2
            continue

        if not token.startswith("-") and (token.startswith("http://") or token.startswith("https://") or "{{" in token or token.startswith("/")):
            if not url:
                url = token
        
        i += 1

    # Fallback url search if not identified
    if not url:
        for t in tokens:
            if not t.startswith("-") and t != "curl" and ("://" in t or t.startswith("localhost") or t.startswith("127.0.0.1")):
                url = t
                break
                
    if not url and tokens:
        # Check last token
        candidate = tokens[-1]
        if not candidate.startswith("-") and candidate != "curl":
            url = candidate

    body = "&".join(data_parts) if data_parts else ""
    body_type = "none"
    if body:
        ct = headers.get("Content-Type", headers.get("content-type", ""))
        if "application/json" in ct or (body.strip().startswith("{") and body.strip().endswith("}")):
            body_type = "json"
        elif "form" in ct:
            body_type = "form"
        else:
            body_type = "raw"

    name = f"{method} {urlparse(url).path or url}"
    
    return {
        "name": name.strip(),
        "method": method,
        "url": url,
        "headers": headers,
        "body": body,
        "body_type": body_type
    }
