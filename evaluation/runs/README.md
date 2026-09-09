# Blind runs — reproducible protocol

Freeze the scorecard before running agents. Do not change harness after seeing results.

## Layout (predictable output location)

```
evaluation/runs/
├── claude/
│   ├── baseline/
│   │   ├── payment.py
│   │   ├── payment.manifest.json  (generated via create_manifest.py)
│   │   └── ...
│   └── failures-enabled/
│       ├── payment.py
│       └── payment.manifest.json
├── cursor/
│   ├── baseline/
│   └── failures-enabled/
└── codex/
    ├── baseline/
    └── failures-enabled/
```

Legacy `evaluation/baseline/` and `evaluation/failures-enabled/` also scanned (for backwards compat).

## How to run a blind evaluation

1. For each agent + scenario (identical prompt, same repo commit):

```bash
# 1a. Baseline (no Failures)
# Give Claude/Cursor/Codex the scenario prompt verbatim from evaluation/scenarios/payment.md
# Save output
cp /tmp/agent_output.py evaluation/runs/claude/baseline/payment.py
python evaluation/create_manifest.py --agent claude --scenario payment --mode baseline --model claude-sonnet-4

# 1b. Failures-enabled (same prompt, same commit, MCP connected)
# Instruct agent to call review_plan before coding and review_code/check_invariant before finalizing, but do not add failure hints to prompt
cp /tmp/agent_output2.py evaluation/runs/claude/failures-enabled/payment.py
python evaluation/create_manifest.py --agent claude --scenario payment --mode failures-enabled --model claude-sonnet-4
```

2. Validate prompt consistency:

```bash
python evaluation/run_evaluation.py --mode manual --agent claude
# checks prompt_hash equality across manifest files
```

3. Full comparison:

```bash
python evaluation/run_evaluation.py --mode manual
python evaluation/run_evaluation.py --mode manual --agent claude
```

## Manifest fields

```
{
  "agent": "claude",
  "scenario": "payment",
  "mode": "baseline",
  "model": "claude-sonnet-4",
  "timestamp": "2026-05-14T12:34:56Z",
  "prompt_hash": "a1b2c3d4e5f6",
  "prompt_source": "evaluation/scenarios/payment.md",
  "failures_mcp_enabled": false,
  "commit": "abc123...",
  "output_path": "evaluation/runs/claude/baseline/payment.py"
}
```

- `prompt_hash` is SHA256 of `scenarios/<scenario>.md` — baseline and failures-enabled must match.
- `failures_mcp_enabled` must be true for failures-enabled, false for baseline.
- `commit` is `git rev-parse HEAD`.

## Do not

- Modify `scenarios/*.md` between baseline and failures-enabled runs.
- Fabricate numbers or pre-fill `results.json`.
- Change `run_evaluation.py` after first real-agent run (freeze protocol).

## Expected table

After all three agents, you should have:

```
Agent    Baseline   +Failures   Improvement
Claude   4/9        8/9         +44%
Cursor   5/9        8/9         +33%
Codex    4/9        9/9         +56%
```

But this table is empty until real runs.
