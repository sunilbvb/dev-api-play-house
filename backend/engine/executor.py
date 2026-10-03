import time
import json
import ssl
import urllib.request
import urllib.error
import urllib.parse
from typing import Dict, Any, Tuple
from .interpolator import interpolate_text, interpolate_dict

def execute_request(
    method: str,
    url: str,
    headers: Dict[str, str],
    body: str,
    variables: Dict[str, Any] = None,
    timeout: int = 15,
    verify_ssl: bool = True
) -> Dict[str, Any]:
    """Execute an HTTP request using Python standard library urllib."""
    if variables is None:
        variables = {}

    # Interpolate dynamic & environment variables
    interpolated_url = interpolate_text(url, variables).strip()
    interpolated_headers = interpolate_dict(headers, variables)
    interpolated_body = interpolate_text(body, variables) if body else ""

    # Ensure URL has scheme
    if not interpolated_url.startswith(("http://", "https://")):
        interpolated_url = "http://" + interpolated_url

    req_data = None
    if interpolated_body and method.upper() not in ("GET", "HEAD"):
        req_data = interpolated_body.encode("utf-8")

    # SSL Context
    if not verify_ssl:
        ssl_ctx = ssl._create_unverified_context()
    else:
        ssl_ctx = ssl.create_default_context()

    # Prepare standard urllib Request
    parsed_req = urllib.request.Request(
        url=interpolated_url,
        data=req_data,
        headers=interpolated_headers,
        method=method.upper()
    )

    start_time = time.perf_counter()
    status_code = 0
    resp_headers = {}
    resp_body = ""
    error_message = None

    try:
        with urllib.request.urlopen(parsed_req, timeout=timeout, context=ssl_ctx) as response:
            status_code = response.getcode()
            # Capture headers
            for k, v in response.headers.items():
                resp_headers[k] = v
            # Read payload
            raw_body = response.read()
            charset = response.headers.get_content_charset() or "utf-8"
            resp_body = raw_body.decode(charset, errors="replace")

    except urllib.error.HTTPError as e:
        status_code = e.code
        for k, v in e.headers.items():
            resp_headers[k] = v
        try:
            raw_body = e.read()
            charset = e.headers.get_content_charset() or "utf-8"
            resp_body = raw_body.decode(charset, errors="replace")
        except Exception:
            resp_body = str(e)
            
    except urllib.error.URLError as e:
        error_message = f"Network Error: {e.reason}"
        status_code = 0
        resp_body = error_message

    except Exception as e:
        error_message = f"Execution Error: {str(e)}"
        status_code = 0
        resp_body = error_message

    elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

    # Format JSON if valid
    is_json = False
    try:
        if resp_body and (resp_body.strip().startswith("{") or resp_body.strip().startswith("[")):
            parsed = json.loads(resp_body)
            resp_body = json.dumps(parsed, indent=2)
            is_json = True
    except Exception:
        pass

    return {
        "status_code": status_code,
        "elapsed_ms": elapsed_ms,
        "headers": resp_headers,
        "body": resp_body,
        "is_json": is_json,
        "error": error_message,
        "sent": {
            "method": method.upper(),
            "url": interpolated_url,
            "headers": interpolated_headers,
            "body": interpolated_body
        }
    }
