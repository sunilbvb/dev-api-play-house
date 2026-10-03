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
| `POST` | `/api/import` | Ingest cURL, Postman JSON, .http file, or Markdown |
| `POST` | `/api/export` | Convert requests to cURL, .http, fetch, python, or Postman |
| `GET` | `/api/history` | View the last 50 executed requests |
| `GET` | `/api/health` | Health check endpoint |

## 5. Game House Auto-Architect & Vitals

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/house/auto-build` | Automatically partition raw API list or workspace into themed Game House with rooms, quests, and Raid Boss |
| `GET` | `/api/house/{id}/vitals` | Retrieve live Game House HP, average agility, XP rewards, and Boss status |
