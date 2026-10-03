# ❓ Frequently Asked Questions (FAQ)

### 1. Does Dev API Play House require Node.js or npm?
No. The backend uses Python 3's built-in standard library (`urllib`, `http.server`, `sqlite3`). The frontend is pure Vanilla ES6 JavaScript. No `npm install`, no `pip install`.

### 2. How does the Game Workflow / DAG sequencing work?
The system inspects each API's endpoint name, URL pattern, and token requirements:
- URLs with `/auth`, `/login`, or `/token` are placed in **Tier 0 (Prerequisites)**.
- User or Character profiles are placed in **Tier 1 (Player Setup)**.
- Game actions (raids, matchmaking, items) are placed in **Tier 2 (Mechanics)**.
- Scores and leaderboards are placed in **Tier 3 (Summary)**.
If an endpoint declares an extraction rule (e.g., extracting `jwt_token` from response body) and another endpoint uses `{{jwt_token}}` in its header, the DAG engine automatically ensures the producer executes before the consumer.

### 3. Which formats can be imported?
- **OpenAPI & Swagger**: OpenAPI 3.0, 3.1, or Swagger 2.0 JSON specifications.
- **cURL commands**: Single or multi-line commands with `-H`, `-X`, `-d`, `--data-raw`, etc.
- **Postman Collections (v2 / v2.1)**: Full JSON export.
- **Postman Environments**: Key-value JSON environment exports.
- **RFC 7230 `.http` / `.rest`**: Text files with `###` block separators.
- **Markdown documentation**: Automatically extracts code blocks matching `curl` or `http`.

### 4. How do I switch environments?
Use the **ENV** dropdown selector in the top bar. You can click the ⚙️ icon to view all variables, add new environments (e.g. `Staging`, `Production`), or edit existing keys in JSON format.

### 5. How does the tool auto-generate API documentation?
The tool inspects the HTTP method, URL path tokens, query string parameters, headers, and request body JSON schema. Clicking **"⚡ Auto-Fill Documentation from API"** automatically produces a full Markdown document containing parameter specifications, request/response schema tables, expected HTTP status codes, and QA checklists.

### 6. What is the Test Matrix Advisor and how does it determine test ways?
The Strategy Advisor inspects the API contract and calculates the exact count of critical test scenarios (typically 6–8 dimensions):
1. *Happy Path Baseline* (200 OK)
2. *Missing Auth Credentials* (Security 401 gate)
3. *HTTP Method Safety* (e.g., DELETE on GET)
4. *Empty Payload Fuzz* (400 validation)
5. *Malformed JSON Syntax* (Parser integrity)
6. *Type Inversion & Null Injection* (Type safety)
7. *SQL Injection & XSS Sanitization* (Security)
8. *Performance SLA Benchmark* (< 500ms agility)
Testers can execute all scenarios with 1 click to verify backend robustness.

### 7. Can I read server setup instructions and repository docs without leaving the browser?
Yes. Click the **📖 Docs & Setup** tab in the top navigation bar. It opens the integrated Developer Knowledge Hub with:
- **Server Setup & CLI Guide**: Instructions for running the web studio, port customization, and headless CI runner flags (`--cli`, `--min-hp`, `--col`, `--chaos`, `--out`).
- **Architecture & DAG**: Visual explanation of Game Rooms (Gates, Armory, Coliseum, Vault), variable chaining, House HP, and Raid Boss dynamics.
- **QA & Test Strategy**: Multi-way test dimension explanations and chaos monkey settings.
- **REST API Reference**: Full endpoint tables and curl examples.
- **Live Markdown Docs**: Interactive reader that fetches and displays `README.md`, `ARCHITECTURE.md`, `FAQ.md`, and `docs/API.md` directly from the repository with one-click markdown copying.

