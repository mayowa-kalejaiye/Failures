"""
Helper to create reproducible run manifests for blind evaluation.

Usage:
  python evaluation/create_manifest.py --agent claude --scenario payment --mode baseline --model claude-sonnet-4
  python evaluation/create_manifest.py --agent cursor --scenario payment --mode failures-enabled --model gpt-4

Creates evaluation/runs/<agent>/<mode>/<scenario>.manifest.json
"""
import argparse, hashlib, json, pathlib, subprocess, datetime, sys
ROOT = pathlib.Path(__file__).parent.parent

def prompt_hash(scenario: str) -> str:
    p = ROOT / "evaluation" / "scenarios" / f"{scenario}.md"
    return hashlib.sha256(p.read_bytes()).hexdigest()[:12] if p.exists() else ""

def git_commit() -> str:
    try:
        out = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=str(ROOT), stderr=subprocess.DEVNULL)
        return out.decode().strip()[:12]
    except Exception:
        return "unknown"

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent", required=True, choices=["claude","cursor","codex"])
    parser.add_argument("--scenario", required=True, choices=["payment","queue","authentication","file-upload","inventory","webhook"])
    parser.add_argument("--mode", required=True, choices=["baseline","failures-enabled"])
    parser.add_argument("--model", default="")
    args = parser.parse_args()

    failures_enabled = args.mode == "failures-enabled"
    manifest = {
        "agent": args.agent,
        "scenario": args.scenario,
        "mode": args.mode,
        "model": args.model,
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "prompt_hash": prompt_hash(args.scenario),
        "prompt_source": f"evaluation/scenarios/{args.scenario}.md",
        "failures_mcp_enabled": failures_enabled,
        "commit": git_commit(),
        "output_path": f"evaluation/runs/{args.agent}/{args.mode}/{args.scenario}.py",
    }
    out_path = ROOT / "evaluation" / "runs" / args.agent / args.mode / f"{args.scenario}.manifest.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Wrote {out_path}")
    print(json.dumps(manifest, indent=2))
