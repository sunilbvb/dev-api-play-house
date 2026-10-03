# 📡 REST API Reference

The backend exposes the following REST endpoints:

## 1. Environments

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/environments` | List all saved environments |
| `POST` | `/api/environments` | Create a new environment |
| `PUT` | `/api/environments/{id}` | Update environment name or variables |
| `DELETE` | `/api/environments/{id}` | Delete an environment |
| `POST` | `/api/environments/active` | Set active environment by ID (`{"id": 1}`) |

## 2. Collections & Requests

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/collections` | List all collections with request counts |
| `POST` | `/api/collections` | Create a new collection |
| `DELETE` | `/api/collections/{id}` | Delete a collection and all its requests |
| `GET` | `/api/requests?collection_id={id}` | List requests in a collection |
| `POST` | `/api/requests` | Create a new API request definition |
| `PUT` | `/api/requests/{id}` | Update an existing API request definition |
| `DELETE` | `/api/requests/{id}` | Delete an API request definition |

## 3. Execution & Workflow

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/execute` | Execute a single request against active environment variables |
| `POST` | `/api/workflows/analyze` | Run DAG solver to build dependency graph and sequence |
| `POST` | `/api/workflows/run` | Execute complete collection quest pipeline in DAG order |

## 4. Import & Export

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/import` | Ingest cURL, Postman JSON, OpenAPI / Swagger (v2, v3, v3.1), .http file, or Markdown |
| `POST` | `/api/export` | Convert requests to cURL, .http, fetch, python, or Postman |
| `GET` | `/api/history` | View the last 50 executed requests |
| `GET` | `/api/health` | Health check endpoint |

## 5. Game House Auto-Architect & Vitals

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/house/auto-build` | Automatically partition raw API list or workspace into themed Game House with rooms, quests, and Raid Boss |
| `GET` | `/api/house/{id}/vitals` | Retrieve live Game House HP, average agility, XP rewards, and Boss status |

## 6. Offline Mock Game Server

| Method | Endpoint | Description |
|---|---|---|
| `GET / POST` | `/mock/*` | Dynamic zero-backend offline simulator returning realistic game payloads (auth tokens, player profiles, raid loot, leaderboards) |

## 7. Gamification, Trophies & Chaos

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/trophies` | List all developer achievements and unlock statuses |
| `POST` | `/api/fuzzer/generate-side-quests` | Generate 3 boundary & security fuzzing side quests (`{"request_id": 1}`) |
| `POST` | `/api/workflows/run` | Execute pipeline with optional `{"chaos_mode": true, "chaos_level": "medium"}` |

## 8. Co-op Arena & Time-Travel Replay

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/coop/events?since_id={id}` | Poll live co-op activity feed from team members |
| `POST` | `/api/coop/events` | Broadcast party message or ping (`{"message": "Ready!", "actor": "Dev"}`) |
| `GET` | `/api/replay/frames` | Retrieve recorded session checkpoints for timeline scrubber |
| `POST` | `/api/replay/export` | Download full `.json` replay session tape |

## 9. Tester Assistance, Advisor & In-App Docs

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/docs/generate` | Auto-generate GitHub Markdown spec with parameter tables, inferred JSON schemas, and QA checklist |
| `POST` | `/api/advisor/analyze-test-ways` | Calculate exact count and definitions of test dimensions for an API |
| `POST` | `/api/advisor/run-test-ways` | Execute matrix and grade API resilience score |
| `GET` | `/api/docs/content?name={readme\|architecture\|faq\|api}` | Serve live markdown documentation directly into in-app Docs Hub |

