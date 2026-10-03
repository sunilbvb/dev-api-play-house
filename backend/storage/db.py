import sqlite3
import json
import os
from typing import Dict, Any, List, Optional

DB_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "playhouse.db")

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS environments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        variables_json TEXT NOT NULL DEFAULT '{}',
        is_active INTEGER NOT NULL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS collections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        description TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        collection_id INTEGER,
        name TEXT NOT NULL,
        method TEXT NOT NULL DEFAULT 'GET',
        url TEXT NOT NULL,
        headers_json TEXT NOT NULL DEFAULT '{}',
        body TEXT DEFAULT '',
        body_type TEXT DEFAULT 'json',
        auth_json TEXT DEFAULT '{}',
        order_idx INTEGER DEFAULT 0,
        extracts_json TEXT DEFAULT '[]',
        assertions_json TEXT DEFAULT '[]',
        documentation TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (collection_id) REFERENCES collections(id) ON DELETE CASCADE
    );
    """)

    # Safe migration for existing databases
    try:
        cursor.execute("ALTER TABLE requests ADD COLUMN documentation TEXT DEFAULT ''")
    except Exception:
        pass

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        request_id INTEGER,
        name TEXT,
        method TEXT,
        url TEXT,
        status_code INTEGER,
        elapsed_ms REAL,
        response_headers_json TEXT,
        response_body TEXT,
        executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (request_id) REFERENCES requests(id) ON DELETE SET NULL
    );
    """)

    # Seed default environment and demo game API collection if empty
    cursor.execute("SELECT COUNT(*) as count FROM environments")
    if cursor.fetchone()["count"] == 0:
        default_vars = json.dumps({
            "base_url": "https://httpbin.org",
            "game_server": "https://api.gameplayhouse.local",
            "player_id": "player_99",
            "api_key": "arcade_secret_token_123"
        }, indent=2)
        cursor.execute("INSERT INTO environments (name, variables_json, is_active) VALUES (?, ?, 1)", ("Development", default_vars))
        prod_vars = json.dumps({
            "base_url": "https://httpbin.org",
            "game_server": "https://api.gameplayhouse.prod",
            "player_id": "pro_gamer_1",
            "api_key": "live_secret_token_456"
        }, indent=2)
        cursor.execute("INSERT INTO environments (name, variables_json, is_active) VALUES (?, ?, 0)", ("Production", prod_vars))

    cursor.execute("SELECT COUNT(*) as count FROM collections")
    if cursor.fetchone()["count"] == 0:
        cursor.execute("INSERT INTO collections (name, description) VALUES (?, ?)", 
                       ("Arcade Game API Quest", "Sample game workflow APIs: Auth, Player Profile, Dungeon Raid, Leaderboard"))
        col_id = cursor.lastrowid
        
        demo_requests = [
            (col_id, "1. Player Login (Auth)", "POST", "{{base_url}}/post",
             json.dumps({"Content-Type": "application/json"}),
             json.dumps({"username": "shadow_ninja", "password": "super_secret_password"}),
             "json", 1,
             json.dumps([{"target": "jwt_token", "source": "body_json", "path": "json.username"}])),
            
            (col_id, "2. Get Player Character", "GET", "{{base_url}}/get?player={{player_id}}",
             json.dumps({"Authorization": "Bearer {{jwt_token}}", "X-Game-Key": "{{api_key}}"}),
             "", "none", 2,
             json.dumps([{"target": "character_level", "source": "body_json", "path": "args.player"}])),
            
            (col_id, "3. Enter Dungeon Raid", "POST", "{{base_url}}/post",
             json.dumps({"Content-Type": "application/json", "Authorization": "Bearer {{jwt_token}}"}),
             json.dumps({"action": "dungeon_enter", "dungeon_id": "crimson_keep", "party_size": 4}),
             "json", 3,
             json.dumps([{"target": "raid_loot_xp", "source": "body_json", "path": "json.party_size"}])),
            
            (col_id, "4. Submit High Score", "POST", "{{base_url}}/post",
             json.dumps({"Content-Type": "application/json", "Authorization": "Bearer {{jwt_token}}"}),
             json.dumps({"player": "{{player_id}}", "score": 99420, "badges": ["dragon_slayer"]}),
             "json", 4, "[]")
        ]
        
        for req in demo_requests:
            cursor.execute("""
            INSERT INTO requests (collection_id, name, method, url, headers_json, body, body_type, order_idx, extracts_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, req)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")
