import re
import time
import uuid
import random
from typing import Dict, Any

def interpolate_text(text: str, variables: Dict[str, Any]) -> str:
    """Replace {{variable_name}} with corresponding value from variables or dynamic generators."""
    if not text:
        return ""
    
    def replacer(match):
        key = match.group(1).strip()
        
        # Dynamic generators
        if key == "$timestamp":
            return str(int(time.time()))
        if key == "$isoTimestamp":
            return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        if key == "$guid" or key == "$uuid":
            return str(uuid.uuid4())
        if key == "$randomInt":
            return str(random.randint(100, 999999))
            
        # Lookup in user/environment variables
        if key in variables:
            val = variables[key]
            return str(val) if val is not None else ""
            
        # Preserve original if not found
        return match.group(0)

    return re.sub(r'\{\{([^{}]+)\}\}', replacer, text)

def interpolate_dict(data: Dict[str, Any], variables: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively interpolate string values inside a dictionary."""
    result = {}
    for k, v in data.items():
        interpolated_key = interpolate_text(str(k), variables)
        if isinstance(v, str):
            result[interpolated_key] = interpolate_text(v, variables)
        elif isinstance(v, dict):
            result[interpolated_key] = interpolate_dict(v, variables)
        elif isinstance(v, list):
            result[interpolated_key] = [
                interpolate_text(item, variables) if isinstance(item, str) else item for item in v
            ]
        else:
            result[interpolated_key] = v
    return result
