# 🎮 Dev API Play House

> Open-source, zero-dependency API playground, multi-format importer, and game workflow DAG engine.

---

## 🚀 Key Features

1. **Multi-Format Ingestion Engine**:
   - **cURL Commands**: Paste any single or multi-line cURL.
   - **Postman Collections (v2 / v2.1)**: Full JSON parser with nested folder resolution and environment files.
   - **RFC 7230 `.http` / `.rest` Files**: Ingest files separated by `###` delimiters.
   - **Markdown Documentation**: Automatically scans documentation files for embedded cURL and HTTP codeblocks.

2. **Game API & Autonomous DAG Workflow Engine**:
   - Identifies API prerequisites and lifecycle sequences (e.g. Auth/Login -> Character Setup -> Matchmaking/Gameplay -> Scoring).
   - Auto-extracts tokens, IDs, and cookies from responses into environment variables.
   - 1-click **Quest Pipeline Runner** that executes complete sequence graphs with live status, timings, and variable logs.

3. **Autonomous Game House Generator**:
   - Feed raw API lists (URLs, endpoints, cURL strings) or scan entire local workspace directories.
   - Automatically partitions APIs into 4 Game Rooms (The Citadel Gates, The Armory, The Coliseum, The Vault).
   - Spawns a **Raid Boss**, assigns XP rewards, tracks live **House HP**, and evaluates victory conditions.

3. **Multi-Environment State & Secret Vault**:
   - Seamless switching between `Development`, `Staging`, and `Production`.
   - Variable interpolation engine with support for `{{variable_name}}` and dynamic generators (`{{$guid}}`, `{{$timestamp}}`, `{{$randomInt}}`).

4. **Multi-Format Studio & Exporter**:
   - Toggle instantly between **Builder**, **cURL**, **RFC .http**, **JavaScript fetch**, and **Python urllib** views.
   - 1-click copy buttons for request payloads, response payloads, headers, and code snippets.
   - Export single APIs or batch collections to Postman v2.1 JSON or `.http` files.

5. **Zero External Dependencies**:
   - Pure Python standard library backend (built on `http.server`, `urllib`, `sqlite3`). No `pip install` required!
   - Pure Vanilla ES6 JavaScript frontend.

---

## ⚡ Quick Start

```bash
# Clone the repository
git clone https://github.com/your-username/dev-api-play-house.git
cd dev-api-play-house

# Run the server (Python 3.8+ built-in)
python3 app.py
```

Open your browser to:
👉 **`http://localhost:8000`**

To customize the port or host:
```bash
PORT=8080 HOST=127.0.0.1 python3 app.py
```

---

## 📁 Repository Structure

```
dev-api-play-house/
├── app.py                      # Application entrypoint runner
├── backend/
│   ├── server.py               # HTTP server & JSON REST API router
│   ├── storage/
│   │   └── db.py               # SQLite3 database engine & schema
│   ├── parsers/
│   │   ├── curl_parser.py      # Shell cURL parser
│   │   ├── postman_parser.py   # Postman collection/environment JSON parser
│   │   ├── http_file_parser.py # RFC 7230 .http parser
│   │   └── markdown_parser.py  # Markdown codeblock extractor
│   ├── engine/
│   │   ├── executor.py         # urllib HTTP client
│   │   ├── interpolator.py     # Variable template engine
│   │   ├── extractor.py        # Response JSON/header/regex token extractor
│   │   └── dependency_graph.py # Game API DAG solver & workflow sequencer
│   └── exporters/
│       └── codegen.py          # cURL, .http, fetch, Python, Postman codegen
├── frontend/
│   ├── index.html              # Main single-page application interface
│   ├── css/
│   │   └── styles.css          # Cyber-arcade responsive dark theme
│   └── js/
│       ├── app.js              # Application bootstrapper
│       └── modules/
│           ├── api_client.js   # Backend REST client wrapper
│           ├── env/            # Environment manager & modal
│           ├── explorer/       # Collections & request sidebar
│           ├── studio/         # Request editor, code tabs & response inspector
│           ├── workflow/       # Game quest visualizer & DAG pipeline runner
│           ├── importer/       # Multi-format import modal
│           └── exporter/       # Multi-format export modal
├── docs/
│   └── API.md                  # REST API endpoint reference
├── ARCHITECTURE.md             # Technical design & sequence models
└── FAQ.md                      # Common questions and troubleshooting
```
