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
    parse_markdown,
    parse_openapi
)
from .engine import (
    execute_request,
    extract_variables,
    analyze_workflow_dag,
    parse_raw_api_list,
    scan_workspace_for_apis,
    auto_generate_game_house,
    THEMES
)
from .chaos import ChaosEngine
from .sandbox import MockGameServer
from .coop import CoopHub
from .fuzzer import SideQuestGenerator
from .replay import ReplayRecorder
from .trophies import TrophyEngine
from .docs_generator import ApiDocGenerator
from .advisor import TestAdvisor
from .exporters import (
    to_curl,
    to_http_raw,
    to_javascript_fetch,
    to_python_urllib,
    to_postman_collection
)
from .search import ContextualSearchEngine

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

        if path.startswith("/mock/"):
            mock_res = MockGameServer.generate_response("GET", path)
            self.send_response(mock_res["status_code"])
            for hk, hv in mock_res["headers"].items():
                self.send_header(hk, hv)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(mock_res["body"].encode("utf-8"))
            return

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

            elif path.startswith("/api/house/") and path.endswith("/vitals"):
                col_id = path.split("/")[3]
                cursor.execute("SELECT * FROM requests WHERE collection_id = ?", (col_id,))
                reqs = [dict(r) for r in cursor.fetchall()]

                cursor.execute("SELECT status_code, elapsed_ms FROM history WHERE request_id IN (SELECT id FROM requests WHERE collection_id = ?) ORDER BY id DESC LIMIT 20", (col_id,))
                history_rows = cursor.fetchall()

                total_runs = len(history_rows)
                successes = sum(1 for h in history_rows if 200 <= (h["status_code"] or 0) < 300)
                failures = total_runs - successes
                avg_latency = round(sum((h["elapsed_ms"] or 0) for h in history_rows) / total_runs, 1) if total_runs > 0 else 0
                hp = max(10, 100 - (failures * 15)) if total_runs > 0 else 100
                xp_earned = successes * 120

                self._send_json({
                    "collection_id": col_id,
                    "total_requests": len(reqs),
                    "total_runs": total_runs,
                    "success_rate": round((successes / total_runs) * 100, 1) if total_runs > 0 else 100.0,
                    "avg_latency_ms": avg_latency,
                    "house_hp": hp,
                    "xp_earned": xp_earned,
                    "boss_defeated": hp > 50 and successes >= len(reqs) and len(reqs) > 0
                })

            elif path == "/api/trophies":
                self._send_json(TrophyEngine.get_all_trophies())

            elif path == "/api/coop/events":
                since_id = int(query.get("since_id", [0])[0])
                self._send_json(CoopHub.get_events(since_id))

            elif path == "/api/replay/frames":
                self._send_json(ReplayRecorder.get_frames())

            elif path == "/api/search":
                search_query = query.get("q", [""])[0]
                cursor.execute("SELECT * FROM requests ORDER BY id ASC")
                req_rows = [dict(r) for r in cursor.fetchall()]
                cursor.execute("SELECT * FROM collections ORDER BY id ASC")
                col_rows = [dict(c) for c in cursor.fetchall()]

                results = ContextualSearchEngine.search(req_rows, col_rows, search_query)
                self._send_json({
                    "query": search_query,
                    "total_matches": len(results),
                    "results": results
                })

            elif path == "/api/docs/content":
                doc_name = query.get("name", ["readme"])[0].lower()
                root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                file_map = {
                    "readme": os.path.join(root_dir, "README.md"),
                    "architecture": os.path.join(root_dir, "ARCHITECTURE.md"),
                    "faq": os.path.join(root_dir, "FAQ.md"),
                    "api": os.path.join(root_dir, "docs", "API.md"),
                    "contributing": os.path.join(root_dir, "CONTRIBUTING.md"),
                    "code_of_conduct": os.path.join(root_dir, "CODE_OF_CONDUCT.md"),
                    "security": os.path.join(root_dir, "SECURITY.md")
                }
                target = file_map.get(doc_name)
                if target and os.path.exists(target):
                    with open(target, "r", encoding="utf-8") as f:
                        content = f.read()
                    self._send_json({"name": doc_name, "content": content, "path": target})
                else:
                    self._send_json({"error": f"Documentation file '{doc_name}' not found"}, status=404)

            else:
                self._send_json({"error": "Endpoint not found"}, status=404)
        finally:
            conn.close()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        body = self._read_body_json()

        if path.startswith("/mock/"):
            body_raw = json.dumps(body) if body else ""
            mock_res = MockGameServer.generate_response("POST", path, body_raw)
            self.send_response(mock_res["status_code"])
            for hk, hv in mock_res["headers"].items():
                self.send_header(hk, hv)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(mock_res["body"].encode("utf-8"))
            return

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

                elif import_type == "openapi":
                    try:
                        spec_obj = json.loads(content)
                        parsed_spec = parse_openapi(spec_obj)
                        imported_requests = parsed_spec.get("requests", [])
                        collection_name = parsed_spec.get("name") or collection_name
                    except Exception as e:
                        return self._send_json({"error": f"Failed to parse OpenAPI JSON: {str(e)}"}, status=400)

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

                chaos_mode = body.get("chaos_mode", False)
                chaos_level = body.get("chaos_level", "medium")
                actor = body.get("actor", "Player 1")

                ReplayRecorder.clear()
                step_results = []
                for idx, req_item in enumerate(ordered, 1):
                    # Check for chaos injection
                    chaotic_resp = None
                    if chaos_mode:
                        chaotic_resp = ChaosEngine.apply_chaos(req_item, chaos_level=chaos_level)

                    if chaotic_resp:
                        res = chaotic_resp
                    else:
                        res = execute_request(
                            method=req_item.get("method", "GET"),
                            url=req_item.get("url", ""),
                            headers=req_item.get("headers", {}),
                            body=req_item.get("body", ""),
                            variables=variables
                        )

                    # Extract variables if successful
                    new_vars = {}
                    if 200 <= (res.get("status_code") or 0) < 300:
                        new_vars = extract_variables(
                            extract_rules=req_item.get("extracts", []),
                            status_code=res["status_code"],
                            headers=res["headers"],
                            response_body=res["body"]
                        )
                        variables.update(new_vars)
                    
                    step_data = {
                        "step": idx,
                        "request_id": req_item.get("id"),
                        "name": req_item.get("name"),
                        "method": req_item.get("method"),
                        "url": res["sent"]["url"] if "sent" in res and "url" in res["sent"] else req_item.get("url"),
                        "status_code": res["status_code"],
                        "elapsed_ms": res["elapsed_ms"],
                        "extracted": new_vars,
                        "error": res.get("error")
                    }
                    step_results.append(step_data)

                    # Time-travel recording
                    ReplayRecorder.record_frame(idx, req_item, res, dict(variables))

                # Evaluate newly unlocked trophies
                run_payload = {
                    "steps": step_results,
                    "final_variables": variables,
                    "chaos_mode": chaos_mode
                }
                newly_unlocked = TrophyEngine.evaluate(run_payload)

                # Broadcast to Co-op Hub
                CoopHub.publish(
                    "quest_complete",
                    actor,
                    f"Completed quest pipeline with {len(step_results)} stages (Chaos: {chaos_mode})",
                    {"total_steps": len(step_results), "unlocked_count": len(newly_unlocked)}
                )

                self._send_json({
                    "workflow_status": "completed",
                    "total_steps": len(step_results),
                    "final_variables": variables,
                    "steps": step_results,
                    "chaos_mode": chaos_mode,
                    "new_trophies": newly_unlocked
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

            elif path == "/api/house/auto-build":
                raw_text = body.get("raw_text", "")
                workspace_path = body.get("workspace_path", "")
                house_name = body.get("house_name", "Arcade Game House")
                theme_key = body.get("theme_key", "arcade")

                collected_apis = []
                if raw_text:
                    collected_apis.extend(parse_raw_api_list(raw_text))
                if workspace_path:
                    collected_apis.extend(scan_workspace_for_apis(workspace_path))

                if not collected_apis:
                    return self._send_json({"error": "No valid APIs could be parsed from input or workspace"}, status=400)

                # Generate game house
                house = auto_generate_game_house(collected_apis, house_name=house_name, theme_key=theme_key)

                # Persist as a new collection
                cursor.execute("INSERT INTO collections (name, description) VALUES (?, ?)", 
                               (house["house_name"], f"Theme: {house['theme']} | Quests: {house['stats']['total_quests']}"))
                col_id = cursor.lastrowid

                # Insert requests in ordered quest sequence
                order_idx = 1
                for r in house["ordered_sequence"]:
                    cursor.execute("""
                    INSERT INTO requests (collection_id, name, method, url, headers_json, body, body_type, order_idx, extracts_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        col_id,
                        r.get("quest_title") or r.get("name", "Quest API"),
                        r.get("method", "GET"),
                        r.get("url", ""),
                        json.dumps(r.get("headers", {})),
                        r.get("body", ""),
                        r.get("body_type", "json"),
                        order_idx,
                        json.dumps(r.get("extracts", []))
                    ))
                    order_idx += 1

                conn.commit()
                house["collection_id"] = col_id
                self._send_json(house, status=201)

            elif path == "/api/coop/events":
                msg = body.get("message", "Ping")
                actor = body.get("actor", "Player")
                ev = CoopHub.publish("chat", actor, msg)
                self._send_json(ev, status=201)

            elif path == "/api/replay/export":
                self._send_json({"tape": ReplayRecorder.export_session()})

            elif path == "/api/fuzzer/generate-side-quests":
                req_id = body.get("request_id")
                cursor.execute("SELECT * FROM requests WHERE id = ?", (req_id,))
                row = cursor.fetchone()
                if not row:
                    return self._send_json({"error": "Request not found"}, status=404)
                req_data = dict(row)
                req_data["headers"] = json.loads(req_data.get("headers_json", "{}") or "{}")
                quests = SideQuestGenerator.generate_quests(req_data)

                for q in quests:
                    cursor.execute("""
                    INSERT INTO requests (collection_id, name, method, url, headers_json, body, body_type, order_idx, extracts_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        req_data["collection_id"],
                        q["name"],
                        q.get("method", "GET"),
                        q.get("url", ""),
                        json.dumps(q.get("headers", {})),
                        q.get("body", ""),
                        q.get("body_type", "json"),
                        q.get("order_idx", 900),
                        "[]"
                    ))
                conn.commit()
                self._send_json({"status": "generated", "side_quests": [q["name"] for q in quests]}, status=201)

            elif path == "/api/docs/generate":
                req_id = body.get("request_id")
                req_data = body.get("request")
                if req_id and not req_data:
                    cursor.execute("SELECT * FROM requests WHERE id = ?", (req_id,))
                    row = cursor.fetchone()
                    if row:
                        req_data = dict(row)
                        req_data["headers"] = json.loads(req_data.get("headers_json", "{}") or "{}")
                        req_data["extracts"] = json.loads(req_data.get("extracts_json", "[]") or "[]")

                if not req_data:
                    return self._send_json({"error": "No API request provided"}, status=400)

                doc_md = ApiDocGenerator.generate_markdown_docs(req_data)

                # Persist to database if req_id provided
                if req_id:
                    cursor.execute("UPDATE requests SET documentation = ? WHERE id = ?", (doc_md, req_id))
                    conn.commit()

                self._send_json({"status": "generated", "documentation": doc_md})

            elif path == "/api/advisor/analyze-test-ways":
                req_id = body.get("request_id")
                req_data = body.get("request")
                if req_id and not req_data:
                    cursor.execute("SELECT * FROM requests WHERE id = ?", (req_id,))
                    row = cursor.fetchone()
                    if row:
                        req_data = dict(row)
                        req_data["headers"] = json.loads(req_data.get("headers_json", "{}") or "{}")

                if not req_data:
                    return self._send_json({"error": "No API request provided"}, status=400)

                analysis = TestAdvisor.analyze_test_ways(req_data)
                self._send_json(analysis)

            elif path == "/api/advisor/run-test-ways":
                req_id = body.get("request_id")
                req_data = body.get("request")
                if req_id and not req_data:
                    cursor.execute("SELECT * FROM requests WHERE id = ?", (req_id,))
                    row = cursor.fetchone()
                    if row:
                        req_data = dict(row)
                        req_data["headers"] = json.loads(req_data.get("headers_json", "{}") or "{}")

                if not req_data:
                    return self._send_json({"error": "No API request provided"}, status=400)

                # Fetch active environment variables
                cursor.execute("SELECT variables_json FROM environments WHERE is_active = 1 LIMIT 1")
                env_row = cursor.fetchone()
                variables = json.loads(env_row["variables_json"]) if env_row else {}

                results = TestAdvisor.run_all_test_ways(req_data, variables)
                self._send_json(results)

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

                doc = body.get("documentation")

                if doc is not None:
                    cursor.execute("""
                    UPDATE requests
                    SET name = ?, method = ?, url = ?, headers_json = ?, body = ?, body_type = ?, extracts_json = ?, documentation = ?
                    WHERE id = ?
                    """, (name, method, url, headers, req_body, body_type, extracts, doc, req_id))
                else:
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
