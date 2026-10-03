import re
from typing import Dict, Any, List
from .curl_parser import parse_curl
from .http_file_parser import parse_http_file

def parse_markdown(markdown_text: str) -> List[Dict[str, Any]]:
    """Extract API definitions from markdown files (codeblocks like ```curl, ```bash, ```http)."""
    requests: List[Dict[str, Any]] = []
    
    # Pattern to find codeblocks with language tags
    pattern = re.compile(r'```([a-zA-Z0-9_-]+)?\n(.*?)```', re.DOTALL)
    
    for match in pattern.finditer(markdown_text):
        lang = (match.group(1) or "").lower()
        snippet = match.group(2).strip()
        
        if "curl" in lang or snippet.startswith("curl "):
            try:
                req = parse_curl(snippet)
                if req.get("url"):
                    requests.append(req)
            except Exception:
                pass
        elif lang in ("http", "rest") or ("HTTP/" in snippet and "\n" in snippet):
            try:
                parsed_http = parse_http_file(snippet)
                requests.extend(parsed_http)
            except Exception:
                pass

    return requests
