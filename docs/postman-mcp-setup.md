# Postman MCP setup (Cursor)

This matches the **Postman for Cursor** first-run flow (`/postman:setup`): API key, connection check, and **choosing your existing workspace** (see project plan: import/sync OpenAPI from the running API).

## 1. Create a Postman API key

1. Open [Postman API keys](https://postman.postman.co/settings/me/api-keys).
2. Generate a key and copy it (prefix is usually `PMAK-`).

## 2. Expose the key to Cursor (pick one)

### Option A — User environment variable (recommended on Windows)

PowerShell (current session only):

```powershell
$env:POSTMAN_API_KEY = "PMAK-your-key-here"
```

Persist for your Windows user (restart Cursor afterward):

```powershell
[System.Environment]::SetEnvironmentVariable('POSTMAN_API_KEY', 'PMAK-your-key-here', 'User')
```

### Option B — Plugin / Cursor settings

If the Postman extension stores the key in Cursor settings instead of the shell, use the UI flow when you run `/postman:setup` and paste the key where prompted.

## 3. Run `/postman:setup` in Cursor

1. Open the Command Palette or chat and run **`/postman:setup`**.
2. Complete API key verification (the flow may call Postman to confirm the key).
3. When asked for a workspace, **select the workspace you already use** for this project so imports and sync land there.

## 4. Smoke test

After setup, the MCP should be able to list workspaces and collections. You can try **`/postman:sync`** with the backend running and OpenAPI at `http://127.0.0.1:8000/openapi.json` (see [README](../README.md)).

## Troubleshooting

| Symptom | What to try |
|--------|-------------|
| 401 / invalid key | Regenerate the key in Postman and update `POSTMAN_API_KEY` (or plugin settings), then restart Cursor. |
| MCP tools missing | Call authentication for the Postman MCP server from Cursor if prompted, or re-run `/postman:setup`. |
| Empty workspace | Use `/postman:sync` or manual Import → Link to `openapi.json` once the API is up. |
