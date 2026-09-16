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

## npx (Node wrapper, requires Python + `failures-mcp` installed)
```bash
npx failures-mcp
```

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
