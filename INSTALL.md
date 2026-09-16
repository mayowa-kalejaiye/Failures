# Install Failures MCP

## pipx (recommended)
```bash
pipx install failures
pipx install failures-mcp  # alt name
failures-mcp --help
```

## uvx (no install)
```bash
uvx failures-mcp
uvx --from failures failures-mcp
```

## pip
```bash
pip install failures
failures-mcp
```

## npx (Node wrapper)
```bash
npx failures-mcp
# requires Python with `failures` installed; wrapper spawns `python -m mcp_server.server`
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
Or explicit:
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

See `mcp/README.md` for 12 tools.
