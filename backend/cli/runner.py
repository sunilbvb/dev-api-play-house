import sys
import json
import argparse
from typing import Dict, Any

from ..storage.db import get_connection, init_db
from ..engine.dependency_graph import analyze_workflow_dag
from ..engine.executor import execute_request
from ..engine.extractor import extract_variables

BANNER = r"""
  ____             _    ____ ___   ____  _             _   _                       
 |  _ \  _____   _/ \  |  _ \_ _| |  _ \| | __ _ _   _| | | | ___  _   _ ___  ___  
 | | | |/ _ \ \ / / _ \ | |_) | |  | |_) | |/ _` | | | | |_| |/ _ \| | | / __|/ _ \ 
 | |_| |  __/\ V / ___ \|  __/| |  |  __/| | (_| | |_| |  _  | (_) | |_| \__ \  __/ 
 |____/ \___| \_/_/   \_\_|  |___| |_|   |_|\__,_|\__, |_| |_|\___/ \__,_|___/\___| 
                                                  |___/                            
           🎮 HEADLESS CI/CD QUEST RUNNER - GAME HOUSE INTEGRITY 🎮
"""

def run_cli():
    parser = argparse.ArgumentParser(description="Dev API Play House - Headless Quest Runner for CI/CD")
    parser.add_argument("--collection", "-c", type=int, default=None, help="Collection ID to test (default: first collection)")
    parser.add_argument("--min-hp", type=int, default=70, help="Minimum House HP required to pass (0-100, default: 70)")
    parser.add_argument("--max-latency", type=float, default=2000.0, help="Maximum average latency in ms before alert")
    args = parser.parse_args()

    print(BANNER)
    init_db()
    conn = get_connection()
    cursor = conn.cursor()

    col_id = args.collection
    if not col_id:
        cursor.execute("SELECT id, name FROM collections LIMIT 1")
        col_row = cursor.fetchone()
        if not col_row:
            print("❌ Error: No collections found in database.")
            sys.exit(1)
        col_id = col_row["id"]
        col_name = col_row["name"]
    else:
        cursor.execute("SELECT name FROM collections WHERE id = ?", (col_id,))
        col_row = cursor.fetchone()
        if not col_row:
            print(f"❌ Error: Collection #{col_id} not found.")
            sys.exit(1)
        col_name = col_row["name"]

    print(f"🏰 Target Game House: [{col_id}] \"{col_name}\"")
    print(f"🎯 Integrity Threshold: Min HP >= {args.min_hp}%\n")

    # Fetch requests
    cursor.execute("SELECT * FROM requests WHERE collection_id = ? ORDER BY order_idx ASC, id ASC", (col_id,))
    rows = [dict(r) for r in cursor.fetchall()]
    for r in rows:
        r["headers"] = json.loads(r.get("headers_json", "{}") or "{}")
        r["extracts"] = json.loads(r.get("extracts_json", "[]") or "[]")

    if not rows:
        print("⚠️ Warning: No APIs configured in this collection.")
        sys.exit(0)

    # Solve DAG
    analysis = analyze_workflow_dag(rows)
    ordered = analysis.get("ordered_requests", rows)

    # Fetch active variables
    cursor.execute("SELECT variables_json FROM environments WHERE is_active = 1 LIMIT 1")
    env_row = cursor.fetchone()
    variables = json.loads(env_row["variables_json"]) if env_row else {}

    total_steps = len(ordered)
    success_count = 0
    total_latency = 0.0

    print(f"⚡ Starting Quest Pipeline ({total_steps} sequential stages)...\n")

    for idx, req_item in enumerate(ordered, 1):
        res = execute_request(
            method=req_item.get("method", "GET"),
            url=req_item.get("url", ""),
            headers=req_item.get("headers", {}),
            body=req_item.get("body", ""),
            variables=variables
        )
        elapsed = res["elapsed_ms"]
        total_latency += elapsed
        code = res["status_code"]
        is_ok = 200 <= code < 300

        # Extract vars
        new_vars = extract_variables(
            extract_rules=req_item.get("extracts", []),
            status_code=code,
            headers=res["headers"],
            response_body=res["body"]
        )
        variables.update(new_vars)

        status_icon = "✅" if is_ok else "❌"
        if is_ok:
            success_count += 1

        print(f"[{idx}/{total_steps}] {status_icon} {req_item.get('method'):<6} {req_item.get('name')[:35]:<35} -> HTTP {code} ({elapsed}ms)")
        if new_vars:
            print(f"      📦 Chained: {list(new_vars.keys())}")
        if not is_ok and res.get("error"):
            print(f"      ⚠️ Error: {res.get('error')}")

    avg_latency = round(total_latency / total_steps, 2)
    failure_count = total_steps - success_count
    final_hp = max(0, 100 - (failure_count * 20))

    print("\n" + "="*70)
    print(f"🏆 QUEST SUMMARY REPORT:")
    print(f"   * Stages Cleared: {success_count}/{total_steps}")
    print(f"   * House Health:   {final_hp}% (Required: {args.min_hp}%)")
    print(f"   * Agility (Avg):  {avg_latency} ms")
    print("="*70)

    if final_hp >= args.min_hp:
        print("\n🎉 VICTORY! Game House Passed Integrity Checks. CI/CD Success!\n")
        sys.exit(0)
    else:
        print(f"\n💀 DEFEAT! House Health ({final_hp}%) below threshold ({args.min_hp}%). Failing build.\n")
        sys.exit(1)

if __name__ == "__main__":
    run_cli()
