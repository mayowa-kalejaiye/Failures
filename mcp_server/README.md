# Failures MCP Server (runnable)

This is the runnable implementation. See `../mcp/README.md` for full docs.

```bash
.venv/Scripts/python.exe mcp_server/server.py  # stdio
.venv/Scripts/python.exe mcp/server.py         # via shim (same)
```

`mcp/` is the spec-facing folder; `mcp_server/` avoids the `pip mcp` name clash at runtime.
