# 🤝 Contributing to Dev API Play House

Thank you for your interest in contributing to **Dev API Play House**! This document provides the guidelines, branching rules, and coding standards required for all contributors.

---

## 🌿 Git Branching Strategy & Rules

To ensure a stable codebase and smooth collaboration, we follow a feature-branch workflow:

### 1. Branch Roles
* **`main`**: The production-ready branch. Protected branch.
  - Never push directly to `main`.
  - All changes must arrive via tested Pull Requests (PRs).
  - Every commit on `main` must pass all CI integrity gates.
* **Feature & Fix Branches**:
  - Always branch off the latest `main`: `git checkout main && git pull origin main && git checkout -b <branch-name>`
  - Keep branches focused on a single responsibility.

### 2. Branch Naming Conventions
Use descriptive, lower-case branch names prefixed with the change type:

| Prefix | Purpose | Example |
|---|---|---|
| `feat/` | New feature or engine capability | `feat/graphql-explorer` |
| `fix/` | Bug fix or issue resolution | `fix/curl-multiline-quotes` |
| `docs/` | Documentation additions or updates | `docs/add-contributing-guide` |
| `refactor/` | Code restructuring without feature changes | `refactor/modular-importers` |
| `test/` | Adding or improving test cases | `test/add-openapi-matrix` |
| `chore/` | Maintenance, CI workflow, or tooling | `chore/update-ci-pipeline` |

---

## 💬 Commit Message Standards (Conventional Commits)

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>: <short description in imperative mood>

[optional body explaining rationale and context]
```

### Supported Types:
* `feat:` A new feature or capability.
* `fix:` A bug fix.
* `docs:` Documentation updates only.
* `style:` Code formatting, white-space, semicolon fixes (no functional change).
* `refactor:` Code refactoring with zero external behavior change.
* `perf:` A code change that improves performance.
* `test:` Adding missing tests or correcting existing tests.
* `chore:` Build scripts, GitHub actions, or package updates.

**Examples**:
* `feat: add GraphQL live subscription support`
* `fix: handle escape characters in raw http headers`
* `docs: update API.md with new replay tape endpoint`

---

## 🏗️ Architectural & Coding Standards

All contributions must adhere to our zero-dependency core principles:

### 1. Backend (Python 3.8+)
- **100% Python Standard Library**: Rely exclusively on built-in modules (`http.server`, `urllib.request`, `sqlite3`, `json`, `re`, `ssl`, `hashlib`, etc.). **Do NOT add third-party pip packages**.
- **Clean Root Directory**: Domain logic must reside in dedicated sub-packages with an `__init__.py` (e.g. `backend/parsers/`, `backend/engine/`, `backend/chaos/`, `backend/advisor/`).
- **Backward Compatibility**: If moving or refactoring modules, provide zero-breakage backward compatibility shims.

### 2. Frontend (Vanilla ES6 JavaScript)
- **No Build Step Required**: Use native ES6 Modules (`import`/`export`). No Webpack, Vite, or Babel required.
- **Modular Directory Organization**: Group modules by domain under `frontend/js/modules/<domain>/`.
- **Theme Consistency**: Use established CSS variables (`--bg-card`, `--accent-cyan`, `--accent-pink`, `--font-mono`) from `frontend/css/styles.css`.

### 3. Living Documentation Synchronization
Whenever a feature, endpoint, or configuration is added or modified:
1. Update `README.md`
2. Update `ARCHITECTURE.md`
3. Update `FAQ.md`
4. Update `docs/API.md`
5. Update `frontend/index.html` (Docs & Knowledge Hub)

---

## 🚀 Step-by-Step Contribution Workflow

1. **Fork the Repository**:
   Click the **Fork** button on [GitHub](https://github.com/sunilbvb/dev-api-play-house).

2. **Clone Your Fork**:
   ```bash
   git clone git@github.com:<your-username>/dev-api-play-house.git
   cd dev-api-play-house
   ```

3. **Create a Feature Branch**:
   ```bash
   git checkout -b feat/my-new-feature
   ```

4. **Develop & Verify Locally**:
   Run the test verification suite to ensure 0 third-party packages and 100% CI pass:
   ```bash
   # Run headless quest runner
   python3 app.py --cli --min-hp 70

   # Run local web server and verify in browser
   python3 app.py
   ```

5. **Commit Your Changes**:
   ```bash
   git add .
   git commit -m "feat: implement my new feature"
   ```

6. **Push to Your Fork**:
   ```bash
   git push -u origin feat/my-new-feature
   ```

7. **Submit a Pull Request**:
   - Open a PR against `main` on `sunilbvb/dev-api-play-house`.
   - Fill out the PR template checklist.
   - Wait for automated GitHub Actions CI to pass.

Thank you for helping make **Dev API Play House** the best open-source API engine! 🎮
