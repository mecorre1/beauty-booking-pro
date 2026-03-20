# Beauty Booking Pro

Monorepo for the beauty booking app. Product requirements: [docs/SPEC.md](docs/SPEC.md). Autonomous implementation order (admin-first): [docs/plans/autonomous-build-roadmap.md](docs/plans/autonomous-build-roadmap.md).

## Backend (FastAPI)

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```

API base: [http://127.0.0.1:8000](http://127.0.0.1:8000) — OpenAPI docs at `/docs`.

**Bootstrap admin:** on API startup, if the `users` table is empty, the backend creates the default dev account below. Override with `BOOTSTRAP_ADMIN_EMAIL` and `BOOTSTRAP_ADMIN_PASSWORD` in `.env`, or set both empty and use `POST /api/admin/auth/register` once with `{ "email", "password" }` (min. 8 characters); further registrations return 403. To get the default account again, delete `data/app.db` (or your DB file) so the table is empty on next start.

**Demo data (local):** from `backend/` with the venv active, run `python -m app.seed_dev_slots` to wipe `slots` and insert sample rows for this and next ISO week.

## Frontend (Vue 3 + Vite)

```bash
cd frontend
npm install
copy .env.example .env.local
npm run dev
```

App: [http://127.0.0.1:5173](http://127.0.0.1:5173). Client routes use `/`; back office uses `/admin` and `/admin/login`.

**Brand colors** are defined as CSS variables in [`frontend/src/style.css`](frontend/src/style.css) (`--color-blush`, `--color-cream`, `--color-sand`, `--color-peach`, plus semantic tokens such as `--background`, `--foreground`, `--card`, `--border`). Prefer those variables in new UI instead of hard-coded hex.

**Blank page / `504 (Outdated Optimize Dep)` on `vue.js`:** stop the dev server, run `npm run dev:fresh` (or `npm run dev:force`), then hard-refresh the browser (Ctrl+Shift+R). That clears or rebuilds Vite’s `node_modules/.vite` dependency cache, which can get out of sync after upgrades or if multiple dev servers ran on the same port.

### Back office login (local dev)

Start the backend first, then open the app and sign in:

| Field | Value |
| --- | --- |
| **URL** | [http://127.0.0.1:5173/admin/login](http://127.0.0.1:5173/admin/login) |
| **Email** | `admin@admin.com` |
| **Password** | `admin` |

These match the bootstrap user created when the API starts with an empty `users` table (see **Backend** above).

CORS allows the Vite dev origin for local development.

## Postman (Cursor)

To connect the Postman MCP plugin (API key + workspace): [docs/postman-mcp-setup.md](docs/postman-mcp-setup.md). After the backend is running, you can sync or import from `http://127.0.0.1:8000/openapi.json` (see `/docs` for interactive OpenAPI).

## Atlassian (Cursor)

**Not done yet** — authenticate the Atlassian MCP server (`plugin-atlassian-atlassian` / Jira & Confluence) in Cursor when you are ready; until then, skip Atlassian-dependent workflows.
