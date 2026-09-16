# Install Failures MCP

Live on PyPI: https://pypi.org/project/failures-mcp/

## pipx (recommended)
```bash
pipx install failures-mcp
failures-mcp
```

## uvx (no install)
```bash
uvx failures-mcp
uvx --from failures-mcp failures-mcp
```

## pip
```bash
pip install failures-mcp
failures-mcp
```

## npx (not published yet)
`failures-mcp` is not on the npm registry, so `npx failures-mcp` will 404. A `bin/failures-mcp.js` wrapper exists in this repo for after publishing — until then, use pipx/pip/uvx above.

## Claude Code / Cursor config
```json
{
  "mcpServers": {
    "failures": {
      "command": "failures-mcp",
      "args": []
    }
  }
}
```
Or explicit (from a checkout):
```json
{
  "mcpServers": {
    "failures": {
      "command": "python",
      "args": ["-m", "mcp_server.server"]
    }
  }
}
```

See `mcp/README.md` for the 13 tools.
