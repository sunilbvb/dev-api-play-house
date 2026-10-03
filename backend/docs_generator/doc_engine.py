import json
import re
import urllib.parse
from typing import Dict, Any, List

class ApiDocGenerator:
    """Auto-generates comprehensive technical API documentation by inspecting the API structure."""

    @classmethod
    def generate_markdown_docs(cls, request_data: Dict[str, Any]) -> str:
        name = request_data.get("name", "API Endpoint")
        method = (request_data.get("method") or "GET").upper()
        raw_url = request_data.get("url", "")
        headers = request_data.get("headers", {})
        if isinstance(headers, str):
            try: headers = json.loads(headers)
            except Exception: headers = {}

        body = request_data.get("body", "")
        extracts = request_data.get("extracts", [])
        if isinstance(extracts, str):
            try: extracts = json.loads(extracts)
            except Exception: extracts = []

        parsed_url = urllib.parse.urlparse(raw_url)
        path = parsed_url.path or raw_url
        query_params = urllib.parse.parse_qs(parsed_url.query)

        # Detect Path Parameters (e.g. {id} or :id or {{var}})
        path_params = re.findall(r'\{([a-zA-Z0-9_-]+)\}|:([a-zA-Z0-9_-]+)|\{\{([a-zA-Z0-9_-]+)\}\}', path)
        flat_path_params = [p[0] or p[1] or p[2] for p in path_params if p[0] or p[1] or p[2]]

        # Parse Request Body JSON schema
        body_fields = []
        parsed_body = None
        if body and body.strip().startswith(("{", "[")):
            try:
                parsed_body = json.loads(body)
                if isinstance(parsed_body, dict):
                    for k, v in parsed_body.items():
                        v_type = type(v).__name__
                        if v is None: v_type = "null"
                        elif isinstance(v, (int, float)): v_type = "number"
                        elif isinstance(v, list): v_type = "array"
                        elif isinstance(v, dict): v_type = "object"
                        body_fields.append({
                            "name": k,
                            "type": v_type,
                            "sample": json.dumps(v) if isinstance(v, (dict, list)) else str(v)
                        })
            except Exception:
                pass

        # Build Markdown Document
        doc = []
        doc.append(f"# 📘 {name}")
        doc.append(f"**Method**: `{method}` | **Endpoint**: `{raw_url}`\n")
        doc.append("## 1. Description & Purpose")
        doc.append(f"Provides access to `{path}`. Used by frontend/game clients to perform `{method}` actions.")
        doc.append("")

        # Path & Query Parameters Table
        if flat_path_params or query_params:
            doc.append("## 2. Request Parameters")
            doc.append("| Parameter | In | Type | Required | Description |")
            doc.append("|---|---|---|---|---|")
            for pp in flat_path_params:
                doc.append(f"| `{pp}` | Path | `string` | **Yes** | Identifier injected into path |")
            for qk, qv in query_params.items():
                val_sample = qv[0] if qv else ""
                doc.append(f"| `{qk}` | Query | `string` | Optional | Query filter parameter (e.g. `{val_sample}`) |")
            doc.append("")

        # Headers Table
        doc.append("## 3. Headers")
        doc.append("| Header | Value / Format | Required | Description |")
        doc.append("|---|---|---|---|")
        if headers:
            for hk, hv in headers.items():
                req_str = "**Yes**" if hk.lower() in ("authorization", "x-api-key", "content-type") else "Optional"
                doc.append(f"| `{hk}` | `{hv}` | {req_str} | Header value |")
        else:
            doc.append("| `Content-Type` | `application/json` | Optional | Default request encoding |")
        doc.append("")

        # Request Body Schema
        if body_fields:
            doc.append("## 4. Request Body Schema (`application/json`)")
            doc.append("| Field | Type | Sample Value | Description |")
            doc.append("|---|---|---|---|")
            for bf in body_fields:
                doc.append(f"| `{bf['name']}` | `{bf['type']}` | `{bf['sample']}` | Input parameter payload |")
            doc.append("")
            doc.append("### Example Payload:")
            doc.append(f"```json\n{json.dumps(parsed_body, indent=2)}\n```\n")
        elif body and body.strip():
            doc.append("## 4. Request Body (Raw)")
            doc.append(f"```text\n{body}\n```\n")

        # Response Status Codes
        doc.append("## 5. Expected Status Codes & QA Response Reference")
        doc.append("| HTTP Code | Status | When Triggered |")
        doc.append("|---|---|---|")
        doc.append("| `200 OK` / `201 Created` | Success | Request valid, server processed successfully |")
        doc.append("| `400 Bad Request` | Client Error | Malformed body, missing required fields, or invalid types |")
        doc.append("| `401 Unauthorized` | Security | Missing or expired Authorization header / JWT token |")
        doc.append("| `403 Forbidden` | Access Denied | Authenticated user lacks permission for this action |")
        doc.append("| `404 Not Found` | Route Error | Resource or entity does not exist |")
        doc.append("| `422 Unprocessable` | Validation | Semantic validation failure on fields |")
        doc.append("| `500 Server Error` | Backend Failure | Uncaught exception or database deadlock |")
        doc.append("")

        # Chained Variables / Extractions
        if extracts:
            doc.append("## 6. Chained Variables (For Automated Quests)")
            doc.append("| Target Variable | Extraction Source | Path / Key |")
            doc.append("|---|---|---|")
            for ex in extracts:
                doc.append(f"| `{{{{{ex.get('target')}}}}}` | `{ex.get('source')}` | `{ex.get('path')}` |")
            doc.append("")

        # Tester Advice
        doc.append("## 7. QA Testing Checklist")
        doc.append("- [ ] Verify `200 OK` on valid payload and valid auth token.")
        doc.append("- [ ] Verify `401 Unauthorized` when Authorization header omitted.")
        doc.append("- [ ] Verify `400 Bad Request` when JSON payload is empty `{}`.")
        doc.append("- [ ] Verify boundary resilience with extreme numbers and string overflow.")
        doc.append("- [ ] Verify latency meets SLA target (< 400ms).")

        return "\n".join(doc)
