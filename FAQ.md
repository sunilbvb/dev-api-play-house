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
- **cURL commands**: Single or multi-line commands with `-H`, `-X`, `-d`, `--data-raw`, etc.
- **Postman Collections (v2 / v2.1)**: Full JSON export.
- **Postman Environments**: Key-value JSON environment exports.
- **RFC 7230 `.http` / `.rest`**: Text files with `###` block separators.
- **Markdown documentation**: Automatically extracts code blocks matching `curl` or `http`.

### 4. How do I switch environments?
Use the **ENV** dropdown selector in the top bar. You can click the ⚙️ icon to view all variables, add new environments (e.g. `Staging`, `Production`), or edit existing keys in JSON format.
