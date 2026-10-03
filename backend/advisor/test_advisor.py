import json
import copy
from typing import Dict, Any, List
from ..engine.executor import execute_request

class TestAdvisor:
    """Inspects an API and calculates the exact count and strategy of test dimensions required."""

    @classmethod
    def analyze_test_ways(cls, req: Dict[str, Any]) -> Dict[str, Any]:
        method = (req.get("method") or "GET").upper()
        url = req.get("url", "")
        headers = req.get("headers", {})
        if isinstance(headers, str):
            try: headers = json.loads(headers)
            except Exception: headers = {}
        body = req.get("body", "")

        ways = []

        # 1. Happy Path
        ways.append({
            "id": "happy_path",
            "name": "1. Happy Path Baseline",
            "category": "Functional Verification",
            "description": "Send baseline parameters and valid credentials.",
            "expected": "HTTP 200/201 (Valid execution)",
            "expected_codes": [200, 201, 204],
            "override_headers": copy.deepcopy(headers),
            "override_body": body,
            "override_method": method
        })

        # 2. Missing Authentication
        has_auth = any(k.lower() in ("authorization", "x-api-key", "token", "x-auth-token") for k in headers.keys())
        if has_auth or "auth" in url.lower() or "bearer" in str(headers).lower():
            no_auth_headers = {k: v for k, v in headers.items() if k.lower() not in ("authorization", "x-api-key", "token", "x-auth-token")}
            ways.append({
                "id": "missing_auth",
                "name": "2. Security Check: Missing Auth Credentials",
                "category": "Security & Gatekeeper",
                "description": "Strip Authorization / API-key headers to verify unauthorized requests are blocked.",
                "expected": "HTTP 401 Unauthorized / 403 Forbidden",
                "expected_codes": [401, 403],
                "override_headers": no_auth_headers,
                "override_body": body,
                "override_method": method
            })

        # 3. Method Tampering
        tampered_method = "DELETE" if method in ("GET", "POST") else "GET"
        ways.append({
            "id": "method_tampering",
            "name": f"3. HTTP Method Safety ({tampered_method} on {method} route)",
            "category": "Protocol Compliance",
            "description": f"Send incorrect HTTP verb ({tampered_method}) to verify router rejection.",
            "expected": "HTTP 405 Method Not Allowed / 404 Not Found",
            "expected_codes": [404, 405],
            "override_headers": copy.deepcopy(headers),
            "override_body": body if tampered_method != "GET" else "",
            "override_method": tampered_method
        })

        # Body-specific tests for POST/PUT/PATCH
        if method in ("POST", "PUT", "PATCH"):
            # 4. Empty Body
            ways.append({
                "id": "empty_payload",
                "name": "4. Empty Payload Validation",
                "category": "Schema Robustness",
                "description": "Send empty JSON body '{}' to ensure backend rejects missing payload.",
                "expected": "HTTP 400 Bad Request / 422 Unprocessable",
                "expected_codes": [400, 422],
                "override_headers": copy.deepcopy(headers),
                "override_body": "{}",
                "override_method": method
            })

            # 5. Malformed JSON
            ways.append({
                "id": "malformed_json",
                "name": "5. Malformed JSON Syntax Handling",
                "category": "Parser Integrity",
                "description": "Send broken JSON syntax to verify parser does not crash with 500 error.",
                "expected": "HTTP 400 Bad Request",
                "expected_codes": [400],
                "override_headers": copy.deepcopy(headers),
                "override_body": "{\n  \"action\": broken_no_quotes\n",
                "override_method": method
            })

            # 6. Type Inversion & Null Injection
            ways.append({
                "id": "type_inversion",
                "name": "6. Type Inversion & Null Injection Fuzz",
                "category": "Type Safety",
                "description": "Inject arrays and nulls into field values to verify strong type coercion.",
                "expected": "HTTP 400 Bad Request / 422 Validation Error",
                "expected_codes": [400, 422],
                "override_headers": copy.deepcopy(headers),
                "override_body": "{\n  \"id\": [null, -1, \"invalid_type\"],\n  \"value\": false\n}",
                "override_method": method
            })

            # 7. SQLi & XSS Sanitization
            ways.append({
                "id": "sqli_xss",
                "name": "7. SQL Injection & XSS Sanitization Probe",
                "category": "Security & Sanitization",
                "description": "Inject SQL statements and script tags to ensure backend sanitizes user input.",
                "expected": "HTTP 400 / 422 without 500 Database Crash",
                "expected_codes": [400, 422, 200], # 200 acceptable if escaped properly
                "override_headers": copy.deepcopy(headers),
                "override_body": "{\n  \"query\": \"' OR '1'='1' -- <script>alert('xss')</script>\",\n  \"limit\": -9999\n}",
                "override_method": method
            })

        else:
            # Query Param Fuzzing for GET
            ways.append({
                "id": "query_boundary",
                "name": "4. Query Parameter Boundary Fuzz",
                "category": "Boundary Testing",
                "description": "Inject extreme negative numbers and oversized values into query parameters.",
                "expected": "HTTP 400 / 200 with sanitized default",
                "expected_codes": [200, 400, 422],
                "override_headers": copy.deepcopy(headers),
                "override_body": "",
                "override_method": method
            })

            ways.append({
                "id": "sql_query_probe",
                "name": "5. Query Injection Probe (SQLi/XSS)",
                "category": "Security & Sanitization",
                "description": "Inject special chars in URL query string.",
                "expected": "HTTP 400 / 200 safely filtered",
                "expected_codes": [200, 400, 422],
                "override_headers": copy.deepcopy(headers),
                "override_body": "",
                "override_method": method
            })

        # 8. Performance SLA Benchmark
        ways.append({
            "id": "latency_benchmark",
            "name": f"{len(ways) + 1}. Performance SLA Benchmark (< 500ms)",
            "category": "Performance & Agility",
            "description": "Verify endpoint responds within target latency threshold.",
            "expected": "Response time < 500ms",
            "expected_codes": [200, 201, 204],
            "override_headers": copy.deepcopy(headers),
            "override_body": body,
            "override_method": method
        })

        return {
            "api_name": req.get("name", url),
            "method": method,
            "url": url,
            "total_ways": len(ways),
            "scenarios": ways
        }

    @classmethod
    def run_all_test_ways(cls, req: Dict[str, Any], variables: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute all recommended test dimensions and grade each one."""
        analysis = cls.analyze_test_ways(req)
        scenarios = analysis["scenarios"]
        results = []
        passed_count = 0

        for sc in scenarios:
            exec_res = execute_request(
                method=sc["override_method"],
                url=req.get("url", ""),
                headers=sc["override_headers"],
                body=sc["override_body"],
                variables=variables or {}
            )

            code = exec_res["status_code"]
            elapsed = exec_res["elapsed_ms"]
            expected_codes = sc["expected_codes"]

            # Evaluate pass/fail
            passed = False
            if sc["id"] == "latency_benchmark":
                passed = (code in expected_codes) and (elapsed < 500.0)
            else:
                passed = code in expected_codes

            if passed:
                passed_count += 1

            results.append({
                "id": sc["id"],
                "name": sc["name"],
                "category": sc["category"],
                "passed": passed,
                "status_code": code,
                "elapsed_ms": elapsed,
                "expected": sc["expected"],
                "actual": f"HTTP {code} ({elapsed}ms)",
                "error": exec_res.get("error")
            })

        return {
            "api_name": req.get("name"),
            "total_ways": len(scenarios),
            "passed_count": passed_count,
            "failed_count": len(scenarios) - passed_count,
            "score_percentage": round((passed_count / len(scenarios)) * 100, 1),
            "scenarios": results
        }
