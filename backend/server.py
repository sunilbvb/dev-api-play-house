import http.server
import socketserver
import os
import json
import urllib.parse
from typing import Dict, Any

from .storage.db import get_connection, init_db
from .parsers import (
    parse_curl,
    parse_postman_collection,
    parse_postman_environment,
    parse_http_file,
    parse_markdown
)
from .engine import (
    execute_request,
    extract_variables,
    analyze_workflow_dag
)
from .exporters import (
    to_curl,
    to_http_raw,
    to_javascript_fetch,
    to_python_urllib,
    to_postman_collection
)

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")

class PlayhouseRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=FRONTEND_DIR, **kwargs)

    def _send_json(self, data: Any, status: int = 200):
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()
        self.wfile.write(body)

    def _read_body_json(self) -> Dict[str, Any]:
        content_len = int(self.headers.get("Content-Length", 0))
        if content_len == 0:
            return {}
        raw = self.rfile.read(content_len).decode("utf-8")
        try:
            return json.loads(raw)
        except Exception:
            return {}

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        if not path.startswith("/api/"):
            # Serve frontend static assets
            return super().do_GET()

        conn = get_connection()
        cursor = conn.cursor()

        try:
            if path == "/api/health":
                self._send_json({"status": "ok", "app": "Dev API Play House", "version": "1.0.0"})

            elif path == "/api/environments":
                cursor.execute("SELECT id, name, variables_json, is_active, created_at FROM environments ORDER BY id ASC")
                rows = [dict(r) for r in cursor.fetchall()]
                for r in rows:
                    try:
                        r["variables"] = json.loads(r["variables_json"])
                    except Exception:
                        r["variables"] = {}
                self._send_json(rows)

            elif path == "/api/collections":
                cursor.execute("""
                SELECT c.id, c.name, c.description, c.created_at, COUNT(r.id) as request_count
                FROM collections c
                LEFT JOIN requests r ON c.id = r.collection_id
                GROUP BY c.id
                ORDER BY c.id ASC
                """)
                self._send_json([dict(r) for r in cursor.fetchall()])

            elif path == "/api/requests":
                col_id = query.get("collection_id", [None])[0]
                if col_id:
                    cursor.execute("SELECT * FROM requests WHERE collection_id = ? ORDER BY order_idx ASC, id ASC", (col_id,))
                else:
                    cursor.execute("SELECT * FROM requests ORDER BY collection_id ASC, order_idx ASC, id ASC")
                rows = [dict(r) for r in cursor.fetchall()]
                for r in rows:
                    for jfield in ("headers_json", "extracts_json", "assertions_json", "auth_json"):
                        try:
                            r[jfield.replace("_json", "")] = json.loads(r.get(jfield, "{}") or "{}")
                        except Exception:
                            r[jfield.replace("_json", "")] = {}
                self._send_json(rows)

            elif path == "/api/history":
                cursor.execute("SELECT * FROM history ORDER BY id DESC LIMIT 50")
                self._send_json([dict(r) for r in cursor.fetchall()])

            else:
                self._send_json({"error": "Endpoint not found"}, status=404)
        finally:
            conn.close()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        body = self._read_body_json()

        conn = get_connection()
        cursor = conn.cursor()

        try:
            if path == "/api/environments":
                name = body.get("name", "New Environment")
                vars_dict = body.get("variables", {})
                cursor.execute("INSERT INTO environments (name, variables_json, is_active) VALUES (?, ?, 0)",
                               (name, json.dumps(vars_dict, indent=2)))
                conn.commit()
                self._send_json({"id": cursor.lastrowid, "name": name, "variables": vars_dict}, status=201)

            elif path == "/api/environments/active":
                env_id = body.get("id")
                cursor.execute("UPDATE environments SET is_active = 0")
                if env_id:
                    cursor.execute("UPDATE environments SET is_active = 1 WHERE id = ?", (env_id,))
                conn.commit()
                self._send_json({"status": "success", "active_id": env_id})

            elif path == "/api/collections":
                name = body.get("name", "New Collection")
                desc = body.get("description", "")
                cursor.execute("INSERT INTO collections (name, description) VALUES (?, ?)", (name, desc))
                conn.commit()
                self._send_json({"id": cursor.lastrowid, "name": name, "description": desc}, status=201)

            elif path == "/api/requests":
                col_id = body.get("collection_id")
                name = body.get("name", "New Request")
                method = body.get("method", "GET").upper()
                url = body.get("url", "")
                headers = json.dumps(body.get("headers", {}))
                req_body = body.get("body", "")
                body_type = body.get("body_type", "json")
                extracts = json.dumps(body.get("extracts", []))
                
                cursor.execute("""
                INSERT INTO requests (collection_id, name, method, url, headers_json, body, body_type, extracts_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (col_id, name, method, url, headers, req_body, body_type, extracts))
                conn.commit()
                self._send_json({"id": cursor.lastrowid, "name": name, "method": method, "url": url}, status=201)

            elif path == "/api/import":
                import_type = body.get("type", "curl") # curl | postman | http | markdown
                content = body.get("content", "")
                collection_name = body.get("collection_name", "Imported APIs")
                
                # Create or get collection
                cursor.execute("SELECT id FROM collections WHERE name = ?", (collection_name,))
                existing_col = cursor.fetchone()
                if existing_col:
                    col_id = existing_col["id"]
                else:
                    cursor.execute("INSERT INTO collections (name, description) VALUES (?, ?)",
                                   (collection_name, f"Imported via {import_type.upper()} format"))
                    col_id = cursor.lastrowid

                imported_requests = []
                if import_type == "curl":
                    req_data = parse_curl(content)
                    imported_requests.append(req_data)

                elif import_type == "postman":
                    try:
                        p_data = json.loads(content)
                        if "values" in p_data and "name" in p_data and "item" not in p_data:
                            # It's an environment
                            env_data = parse_postman_environment(p_data)
                            cursor.execute("INSERT INTO environments (name, variables_json) VALUES (?, ?)",
                                           (env_data["name"], json.dumps(env_data["variables"], indent=2)))
                            conn.commit()
                            return self._send_json({"status": "imported_environment", "name": env_data["name"]})
                        else:
                            parsed_col = parse_postman_collection(p_data)
                            imported_requests = parsed_col.get("requests", [])
                    except Exception as e:
                        return self._send_json({"error": f"Failed to parse Postman JSON: {str(e)}"}, status=400)

                elif import_type == "http":
                    imported_requests = parse_http_file(content)

                elif import_type == "markdown":
                    imported_requests = parse_markdown(content)

                # Persist imported requests
                saved_count = 0
                for r in imported_requests:
                    cursor.execute("""
                    INSERT INTO requests (collection_id, name, method, url, headers_json, body, body_type, extracts_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        col_id,
                        r.get("name", "Imported Request"),
                        r.get("method", "GET").upper(),
                        r.get("url", ""),
                        json.dumps(r.get("headers", {})),
                        r.get("body", ""),
                        r.get("body_type", "json"),
                        json.dumps(r.get("extracts", []))
                    ))
                    saved_count += 1

                conn.commit()
                self._send_json({
                    "status": "success",
                    "collection_id": col_id,
                    "imported_count": saved_count,
                    "collection_name": collection_name
                })

            elif path == "/api/execute":
                # Execute single request
                # Can accept either direct request payload or request_id
                req_id = body.get("request_id")
                req_obj = None
                
                if req_id:
                    cursor.execute("SELECT * FROM requests WHERE id = ?", (req_id,))
                    row = cursor.fetchone()
                    if row:
                        req_obj = dict(row)
                        req_obj["headers"] = json.loads(req_obj.get("headers_json", "{}") or "{}")
                        req_obj["extracts"] = json.loads(req_obj.get("extracts_json", "[]") or "[]")

                if not req_obj:
                    req_obj = {
                        "name": body.get("name", "Custom Request"),
                        "method": body.get("method", "GET"),
                        "url": body.get("url", ""),
                        "headers": body.get("headers", {}),
                        "body": body.get("body", ""),
                        "extracts": body.get("extracts", [])
                    }

                # Get active environment variables
                cursor.execute("SELECT variables_json FROM environments WHERE is_active = 1 LIMIT 1")
                active_env_row = cursor.fetchone()
                variables = {}
                if active_env_row:
                    try:
                        variables = json.loads(active_env_row["variables_json"])
                    except Exception:
                        pass
                
                # Merge runtime override variables
                variables.update(body.get("runtime_variables", {}))

                # Execute
                result = execute_request(
                    method=req_obj.get("method", "GET"),
                    url=req_obj.get("url", ""),
                    headers=req_obj.get("headers", {}),
                    body=req_obj.get("body", ""),
                    variables=variables
                )

                # Run extraction rules
                extracted = extract_variables(
                    extract_rules=req_obj.get("extracts", []),
                    status_code=result["status_code"],
                    headers=result["headers"],
                    response_body=result["body"]
                )
                result["extracted_variables"] = extracted

                # Save history
                cursor.execute("""
                INSERT INTO history (request_id, name, method, url, status_code, elapsed_ms, response_headers_json, response_body)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    req_id,
                    req_obj.get("name"),
                    result["sent"]["method"],
                    result["sent"]["url"],
                    result["status_code"],
                    result["elapsed_ms"],
                    json.dumps(result["headers"]),
                    result["body"]
                ))
                conn.commit()

                self._send_json(result)

            elif path == "/api/workflows/analyze":
                col_id = body.get("collection_id")
                req_list = body.get("requests")
                
                if not req_list and col_id:
                    cursor.execute("SELECT * FROM requests WHERE collection_id = ? ORDER BY order_idx ASC, id ASC", (col_id,))
                    rows = [dict(r) for r in cursor.fetchall()]
                    for r in rows:
                        r["headers"] = json.loads(r.get("headers_json", "{}") or "{}")
                        r["extracts"] = json.loads(r.get("extracts_json", "[]") or "[]")
                    req_list = rows

                analysis = analyze_workflow_dag(req_list or [])
                self._send_json(analysis)

            elif path == "/api/workflows/run":
                # Execute full DAG workflow sequentially with variable passing
                col_id = body.get("collection_id")
                cursor.execute("SELECT * FROM requests WHERE collection_id = ? ORDER BY order_idx ASC, id ASC", (col_id,))
                rows = [dict(r) for r in cursor.fetchall()]
                for r in rows:
                    r["headers"] = json.loads(r.get("headers_json", "{}") or "{}")
                    r["extracts"] = json.loads(r.get("extracts_json", "[]") or "[]")

                # Analyze DAG sequence
                analysis = analyze_workflow_dag(rows)
                ordered = analysis.get("ordered_requests", rows)

                # Get base active variables
                cursor.execute("SELECT variables_json FROM environments WHERE is_active = 1 LIMIT 1")
                active_env_row = cursor.fetchone()
                variables = {}
                if active_env_row:
                    try:
                        variables = json.loads(active_env_row["variables_json"])
                    except Exception:
                        pass
                variables.update(body.get("runtime_variables", {}))

                step_results = []
                for idx, req_item in enumerate(ordered, 1):
                    res = execute_request(
                        method=req_item.get("method", "GET"),
                        url=req_item.get("url", ""),
                        headers=req_item.get("headers", {}),
                        body=req_item.get("body", ""),
                        variables=variables
                    )
                    # Extract variables
                    new_vars = extract_variables(
                        extract_rules=req_item.get("extracts", []),
                        status_code=res["status_code"],
                        headers=res["headers"],
                        response_body=res["body"]
                    )
                    variables.update(new_vars)
                    
                    step_results.append({
                        "step": idx,
                        "request_id": req_item.get("id"),
                        "name": req_item.get("name"),
                        "method": req_item.get("method"),
                        "url": res["sent"]["url"],
                        "status_code": res["status_code"],
                        "elapsed_ms": res["elapsed_ms"],
                        "extracted": new_vars,
                        "error": res.get("error")
                    })

                self._send_json({
                    "workflow_status": "completed",
                    "total_steps": len(step_results),
                    "final_variables": variables,
                    "steps": step_results
                })

            elif path == "/api/export":
                format_type = body.get("format", "curl") # curl | http | fetch | python | postman
                req_obj = body.get("request")
                requests_list = body.get("requests", [req_obj] if req_obj else [])

                if format_type == "curl":
                    output = "\n\n".join(to_curl(r) for r in requests_list if r)
                elif format_type == "http":
                    output = "\n\n".join(to_http_raw(r) for r in requests_list if r)
                elif format_type == "fetch":
                    output = "\n\n".join(to_javascript_fetch(r) for r in requests_list if r)
                elif format_type == "python":
                    output = "\n\n".join(to_python_urllib(r) for r in requests_list if r)
                elif format_type == "postman":
                    name = body.get("collection_name", "Dev API Play House Export")
                    output = json.dumps(to_postman_collection(name, requests_list), indent=2)
                else:
                    output = to_curl(requests_list[0] if requests_list else {})

                self._send_json({"format": format_type, "content": output})

            else:
                self._send_json({"error": "Endpoint not found"}, status=404)
        finally:
            conn.close()

    def do_PUT(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        body = self._read_body_json()

        conn = get_connection()
        cursor = conn.cursor()

        try:
            if path.startswith("/api/environments/"):
                env_id = path.split("/")[-1]
                name = body.get("name")
                vars_dict = body.get("variables")
                if name is not None and vars_dict is not None:
                    cursor.execute("UPDATE environments SET name = ?, variables_json = ? WHERE id = ?",
                                   (name, json.dumps(vars_dict, indent=2), env_id))
                elif name is not None:
                    cursor.execute("UPDATE environments SET name = ? WHERE id = ?", (name, env_id))
                elif vars_dict is not None:
                    cursor.execute("UPDATE environments SET variables_json = ? WHERE id = ?",
                                   (json.dumps(vars_dict, indent=2), env_id))
                conn.commit()
                self._send_json({"status": "updated", "id": env_id})

            elif path.startswith("/api/requests/"):
                req_id = path.split("/")[-1]
                name = body.get("name")
                method = body.get("method")
                url = body.get("url")
                headers = json.dumps(body.get("headers", {}))
                req_body = body.get("body", "")
                body_type = body.get("body_type", "json")
                extracts = json.dumps(body.get("extracts", []))

                cursor.execute("""
                UPDATE requests
                SET name = ?, method = ?, url = ?, headers_json = ?, body = ?, body_type = ?, extracts_json = ?
                WHERE id = ?
                """, (name, method, url, headers, req_body, body_type, extracts, req_id))
                conn.commit()
                self._send_json({"status": "updated", "id": req_id})

            else:
                self._send_json({"error": "Endpoint not found"}, status=404)
        finally:
            conn.close()

    def do_DELETE(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        conn = get_connection()
        cursor = conn.cursor()

        try:
            if path.startswith("/api/collections/"):
                col_id = path.split("/")[-1]
                cursor.execute("DELETE FROM collections WHERE id = ?", (col_id,))
                conn.commit()
                self._send_json({"status": "deleted", "id": col_id})

            elif path.startswith("/api/requests/"):
                req_id = path.split("/")[-1]
                cursor.execute("DELETE FROM requests WHERE id = ?", (req_id,))
                conn.commit()
                self._send_json({"status": "deleted", "id": req_id})

            elif path.startswith("/api/environments/"):
                env_id = path.split("/")[-1]
                cursor.execute("DELETE FROM environments WHERE id = ?", (env_id,))
                conn.commit()
                self._send_json({"status": "deleted", "id": env_id})

            else:
                self._send_json({"error": "Endpoint not found"}, status=404)
        finally:
            conn.close()

def run_server(port: int = 8000, host: str = "0.0.0.0"):
    init_db()
    with socketserver.TCPServer((host, port), PlayhouseRequestHandler) as httpd:
        print(f"🎮 Dev API Play House running at http://localhost:{port}")
        print(f"📂 Frontend assets served from: {FRONTEND_DIR}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server...")
            httpd.server_close()

if __name__ == "__main__":
    run_server()
