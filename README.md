# 🎮 Dev API Play House

> Open-source, zero-dependency API playground, multi-format importer, and game workflow DAG engine.

---

## 🚀 Key Features

1. **Multi-Format Ingestion Engine**:
   - **OpenAPI & Swagger**: Drag-and-drop or paste OpenAPI 3.0, 3.1, or Swagger 2.0 specs.
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

4. **⚔️ Boss Enrage Mode (API Chaos Engine)**:
   - Simulates network lag spikes, rate-limit triggers (429), and internal server crashes (500) to verify client resilience.

5. **🕹️ Offline Mock Game Server**:
   - Dynamic simulation endpoints under `/mock/*` for developing games without active backend dependencies.

6. **🤖 Headless CI/CD Quest Runner**:
   - Run API suites directly inside GitHub Actions or CI pipelines with `python3 app.py --cli --min-hp 80`.

7. **👥 Co-op Multiplayer Live Ticker**:
   - Live event stream showing party executions, token loots, and teammate pings.

8. **🎯 Boundary & Security Side Quests**:
   - 1-click fuzzing generator producing *Ghost Attack* (empty body), *Armor Pierce* (injection fuzz), and *Speed Sprint* stress tests.

9. **📼 Time-Travel Replay & Tape Exporter**:
   - Scrub through execution frame checkpoints and export session tapes for instant bug reproduction.

10. **🏆 Developer Trophies & Badges**:
   - Gamified developer experience with unlockable badges (*Speed Demon*, *Iron Gatekeeper*, *Dragon Slayer*, *Chaos Survivor*).

11. **📡 Real-Time WebSocket & SSE Live Studio**:
   - Native client for testing bidirectional game socket frames (`ws://`, `wss://`) and server-sent event streams with live traffic monitor and 1-click ping.

---

## ⚡ Quick Start

### 1. Interactive Web Studio
```bash
# Run server (Python 3.8+ built-in, zero pip installs)
python3 app.py
```
Open your browser at: 👉 **`http://localhost:8000`**

### 2. Headless CI/CD Mode
```bash
# Run headless quest integrity check in CI pipeline
python3 app.py --cli --collection 1 --min-hp 70
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
