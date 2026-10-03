import re
from typing import Dict, Any, List

def parse_http_file(content: str) -> List[Dict[str, Any]]:
    """Parse .http or .rest file containing one or more requests separated by ###."""
    # First extract any file-level @variable=value declarations
    lines = content.splitlines()
    file_vars = {}
    clean_lines = []
    
    for line in lines:
        var_match = re.match(r'^\s*@([a-zA-Z0-9_-]+)\s*=\s*(.+)$', line)
        if var_match:
            file_vars[var_match.group(1)] = var_match.group(2).strip()
        else:
            clean_lines.append(line)
            
    content = "\n".join(clean_lines)
    
    # Split blocks by ###
    blocks = re.split(r'(?m)^###[ \t]*(.*)$', content)
    
    requests: List[Dict[str, Any]] = []
    
    # blocks has alternating [preamble, title1, block1, title2, block2, ...]
    if len(blocks) == 1:
        # Single request without ###
        req = _parse_single_http_block("", blocks[0])
        if req:
            requests.append(req)
    else:
        i = 1
        while i < len(blocks):
            title = blocks[i].strip()
            block_content = blocks[i+1] if i + 1 < len(blocks) else ""
            req = _parse_single_http_block(title, block_content)
            if req:
                requests.append(req)
            i += 2

    return requests

def _parse_single_http_block(title: str, block: str) -> Optional[Dict[str, Any]]:
    lines = [l for l in block.splitlines()]
    # Skip leading empty lines or comments
    start_idx = 0
    extracted_name = title
    
    while start_idx < len(lines):
        line = lines[start_idx].strip()
        if not line:
            start_idx += 1
            continue
        if line.startswith("#") or line.startswith("//"):
            if not extracted_name:
                extracted_name = line.lstrip("#/ ").strip()
            start_idx += 1
            continue
        break
        
    if start_idx >= len(lines):
        return None
        
    # First non-comment line must be: [METHOD] URL [HTTP/1.1]
    first_line = lines[start_idx].strip()
    match = re.match(r'^(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\s+([^\s]+)(?:\s+HTTP/[0-9.]+)?$', first_line, re.IGNORECASE)
    if match:
        method = match.group(1).upper()
        url = match.group(2)
    else:
        # Default GET if only URL provided
        method = "GET"
        url = first_line.split()[0]
        
    if not extracted_name:
        extracted_name = f"{method} {url}"

    # Parse headers until blank line
    start_idx += 1
    headers = {}
    while start_idx < len(lines):
        line = lines[start_idx].strip()
        if not line:
            start_idx += 1
            break
        if ":" in line:
            k, v = line.split(":", 1)
            headers[k.strip()] = v.strip()
        start_idx += 1

    # Remaining lines are the body
    body_lines = lines[start_idx:]
    body = "\n".join(body_lines).strip()
    body_type = "none"
    if body:
        ct = headers.get("Content-Type", headers.get("content-type", ""))
        if "application/json" in ct or (body.startswith("{") and body.endswith("}")) or (body.startswith("[") and body.endswith("]")):
            body_type = "json"
        elif "form" in ct:
            body_type = "form"
        else:
            body_type = "raw"

    return {
        "name": extracted_name,
        "method": method,
        "url": url,
        "headers": headers,
        "body": body,
        "body_type": body_type
    }
