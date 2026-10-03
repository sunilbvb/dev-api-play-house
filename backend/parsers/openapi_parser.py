import json
from typing import Dict, Any, List

def parse_openapi(spec_data: Dict[str, Any]) -> Dict[str, Any]:
    """Parse OpenAPI v3 / v3.1 or Swagger v2.0 JSON specification."""
    info = spec_data.get("info", {})
    title = info.get("title", "Imported OpenAPI Specification")
    description = info.get("description", "")

    # Base URL extraction
    base_url = "{{base_url}}"
    if "servers" in spec_data and isinstance(spec_data["servers"], list) and spec_data["servers"]:
        base_url = spec_data["servers"][0].get("url", "{{base_url}}")
    elif "host" in spec_data:
        scheme = spec_data.get("schemes", ["https"])[0]
        base_path = spec_data.get("basePath", "")
        base_url = f"{scheme}://{spec_data['host']}{base_path}"

    requests: List[Dict[str, Any]] = []
    paths = spec_data.get("paths", {})

    for path, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue

        for method in ("get", "post", "put", "patch", "delete", "options", "head"):
            if method not in path_item:
                continue

            op = path_item[method]
            if not isinstance(op, dict):
                continue

            op_summary = op.get("summary") or op.get("operationId") or f"{method.upper()} {path}"
            full_url = f"{base_url.rstrip('/')}/{path.lstrip('/')}" if base_url else path

            headers = {}
            extracts = []

            # Check for security requirements
            sec = op.get("security") or spec_data.get("security", [])
            if sec:
                headers["Authorization"] = "Bearer {{jwt_token}}"

            # Parameters (query, header, path)
            params = op.get("parameters", [])
            query_parts = []
            for p in params:
                if not isinstance(p, dict):
                    continue
                p_in = p.get("in")
                p_name = p.get("name")
                if p_in == "header":
                    headers[p_name] = f"{{{{{p_name}}}}}"
                elif p_in == "query":
                    query_parts.append(f"{p_name}={{{{{p_name}}}}}")

            if query_parts and "?" not in full_url:
                full_url += "?" + "&".join(query_parts)

            # Request Body parsing
            body = ""
            body_type = "none"

            # OpenAPI 3 requestBody
            if "requestBody" in op:
                rb = op["requestBody"]
                content = rb.get("content", {})
                if "application/json" in content:
                    headers["Content-Type"] = "application/json"
                    body_type = "json"
                    schema = content["application/json"].get("schema", {})
                    body = json.dumps(_schema_to_sample(schema, spec_data), indent=2)

            # Swagger 2 body parameter
            for p in params:
                if isinstance(p, dict) and p.get("in") == "body":
                    headers["Content-Type"] = "application/json"
                    body_type = "json"
                    schema = p.get("schema", {})
                    body = json.dumps(_schema_to_sample(schema, spec_data), indent=2)

            # Detect auth extracts for login/token
            path_lower = (path + " " + op_summary).lower()
            if any(k in path_lower for k in ("login", "auth", "token", "signin")):
                extracts.append({"target": "jwt_token", "source": "body_json", "path": "token"})
            elif any(k in path_lower for k in ("player", "user", "profile")) and method == "post":
                extracts.append({"target": "player_id", "source": "body_json", "path": "id"})

            requests.append({
                "name": op_summary,
                "method": method.upper(),
                "url": full_url,
                "headers": headers,
                "body": body,
                "body_type": body_type,
                "extracts": extracts
            })

    return {
        "name": title,
        "description": description,
        "requests": requests
    }

def _schema_to_sample(schema: Dict[str, Any], root_spec: Dict[str, Any]) -> Any:
    """Generate sample JSON structure from OpenAPI schema."""
    if not isinstance(schema, dict):
        return {}

    # Resolve $ref
    if "$ref" in schema:
        ref_path = schema["$ref"].lstrip("#/").split("/")
        curr = root_spec
        for part in ref_path:
            if isinstance(curr, dict) and part in curr:
                curr = curr[part]
            else:
                return {}
        return _schema_to_sample(curr, root_spec)

    s_type = schema.get("type", "object")

    if s_type == "object":
        sample_obj = {}
        properties = schema.get("properties", {})
        for prop_name, prop_schema in properties.items():
            sample_obj[prop_name] = _schema_to_sample(prop_schema, root_spec)
        return sample_obj

    elif s_type == "array":
        items_schema = schema.get("items", {})
        return [_schema_to_sample(items_schema, root_spec)]

    elif s_type == "string":
        if "example" in schema:
            return schema["example"]
        if schema.get("format") == "date-time":
            return "2026-10-04T00:00:00Z"
        if schema.get("format") == "uuid":
            return "123e4567-e89b-12d3-a456-426614174000"
        return "sample_string"

    elif s_type in ("integer", "number"):
        return schema.get("example", 42)

    elif s_type == "boolean":
        return schema.get("example", True)

    return {}
