#!/usr/bin/env node
// npx failures-mcp — spawns the Python MCP via stdio
// Works with pipx/uvx installed `failures-mcp` or fallback to python -m
import { spawn } from 'node:child_process';
import { existsSync } from 'node:fs';

const args = process.argv.slice(2);
const pythonCandidates = ['python', 'python3', 'py'];
// Try pipx/uvx binary first, then python -m
const trySpawn = (cmd, a) => {
  const child = spawn(cmd, a, { stdio: 'inherit' });
  child.on('error', () => {});
  child.on('exit', code => process.exit(code ?? 1));
};

// If failures-mcp binary exists (pipx/uvx), use it directly
// else fall back to python -m mcp_server.server
import { execSync } from 'node:child_process';
try {
  execSync('where failures-mcp', { stdio: 'ignore' });
  trySpawn('failures-mcp', args);
} catch {
  // fallback: python -m
  for (const py of pythonCandidates) {
    try {
      execSync(`${py} -c "import mcp_server.server"`, { stdio: 'ignore' });
      trySpawn(py, ['-m', 'mcp_server.server', ...args]);
      break;
    } catch {}
  }
}
