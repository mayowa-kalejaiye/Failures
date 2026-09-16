"""Failures MCP — deterministic failure-oriented engineering checks."""
import json, pathlib, sys
# ensure engine is importable when run as script
sys.path.insert(0, str(pathlib.Path(__file__).parent))

from mcp.server.mcpserver import MCPServer
from mcp.types import TextContent

from engine.loader import load_principles, load_dimensions
from engine.analyzer import review_architecture, analyze_component, generate_failure_cases, generate_failure_tests, review_plan, check_invariant
from engine.code_review import review_code, check_idempotency, check_retry_safety, check_transaction_safety
from engine.semantic import semantic_review

mcp = MCPServer(
    name="failures",
    title="Failures — Engineering constraints for AI-built software",
    version="0.1.0",
    instructions="Make the coding agent reason about what happens when things fail. Every tool is deterministic and opinionated.",
)

def _json(obj):
    return json.dumps(obj, indent=2)

@mcp.tool(name="get_principles", description="List Failures engineering principles and dimensions. Optionally filter by id.")
def get_principles(filter: str = "") -> str:
    principles = load_principles()
    if filter:
        f = filter.lower()
        principles = [p for p in principles if f in p["id"] or f in p["name"].lower()]
    dims = load_dimensions()
    return _json({"principles": principles, "dimensions": dims})

@mcp.tool(name="review_architecture", description="Review a system architecture for failure modes. Provide system description, components (list of {name,description,dependencies} or strings), optional flows and dependencies. Returns severity-ranked findings with required controls and tests.")
def review_architecture_tool(system: str, components: list = None, flows: list = None, dependencies: list = None) -> str:
    if not system or not system.strip():
        return _json({"error": "system description is required"})
    # normalize components: allow strings or dicts (fixes brittle contract)
    raw = components or []
    normalized = []
    for c in raw:
        if isinstance(c, str):
            normalized.append({"name": c, "description": c})
        elif isinstance(c, dict):
            normalized.append(c)
        else:
            normalized.append({"name": str(c), "description": str(c)})
    components = normalized
    result = review_architecture(system, components, flows, dependencies)
    lines = [f"FAILURE REVIEW — {result['system']}", ""]
    if not result["findings"]:
        lines.append("No critical findings (system description may be too vague). Ask: What crosses a network boundary? What has side effects?")
    else:
        for f in result["findings"]:
            conf = f.get("confidence")
            conf_str = f" Confidence: {conf:.2f}" if isinstance(conf, (int,float)) else ""
            mode = f" [{f.get('mode','')}]" if f.get("mode") else ""
            lines.append(f"[{f['severity']}] {f['title']} ({f['dimension']}) — component: {f['component']}{conf_str}{mode}")
            lines.append(f"  Failure: {f['failure']}")
            lines.append(f"  Why: {f['why']}")
            if f.get("evidence"):
                lines.append(f"  Evidence: {f.get('evidence')}")
            if f.get("invariant"):
                lines.append(f"  Invariant: {f['invariant']}")
            if f.get("required"):
                lines.append(f"  Required: {', '.join(f['required'])}")
            if f.get("tests"):
                lines.append(f"  Tests: {', '.join(f['tests'])}")
            lines.append("")
    lines.append("QUESTIONS THE AGENT SHOULD ANSWER:")
    for q in result["questions"]:
        lines.append(f"  • {q}")
    lines.append("")
    lines.append("--- JSON ---")
    lines.append(_json(result))
    return "\n".join(lines)

@mcp.tool(name="analyze_component", description="Analyze a single component (database, queue, api, payment, auth, cache, worker, storage) for failure modes.")
def analyze_component_tool(component_type: str, description: str, dependencies: list = None) -> str:
    if not component_type or not description:
        return _json({"error": "component_type and description required"})
    result = analyze_component(component_type, description, dependencies or [])
    lines = [f"COMPONENT REVIEW — {result['component']} (detected: {result['detected_type']})", f"Description: {result['description']}", ""]
    for f in result["findings"]:
        lines.append(f"[{f['severity']}] {f['title']} ({f['dimension']})")
        lines.append(f"  Why: {f['why']}")
        lines.append(f"  Required: {', '.join(f['required'])}")
        lines.append("")
    lines.append("--- JSON ---")
    lines.append(_json(result))
    return "\n".join(lines)

@mcp.tool(name="generate_failure_cases", description="Generate concrete failure scenarios for a system. Prioritizes ambiguous and partial failures. Optional focus: atomicity, idempotency, timeout, concurrency, etc.")
def generate_failure_cases_tool(system: str, components: list = None, focus: str = "") -> str:
    if not system:
        return _json({"error": "system description required"})
    cases = generate_failure_cases(system, components, focus)
    lines = [f"FAILURE CASES — {system}" + (f" (focus: {focus})" if focus else ""), ""]
    for c in cases:
        lines.append(f"[{c['severity']}] {c['case']} ({c['dimension']})")
        lines.append(f"  How: {c['how']}")
        lines.append(f"  Effect: {c['effect']}")
        lines.append(f"  Mitigation: {c['mitigation']}")
        lines.append("")
    lines.append("--- JSON ---")
    lines.append(_json(cases))
    return "\n".join(lines)

@mcp.tool(name="review_code", description="Review source code for failure-related risks (idempotency, transactions, timeouts, race conditions, retry safety, resource exhaustion). Provide code and language.")
def review_code_tool(code: str, language: str = "python") -> str:
    if not code or not code.strip():
        return _json({"error": "code is required"})
    findings = review_code(code, language)
    lines = ["STATIC FAILURE CHECK — Code Review", ""]
    if not findings:
        lines.append("No deterministic issues detected. Still ask: what if this is retried? what if it crashes between steps?")
        lines.append("")
    else:
        for f in findings:
            ev = f.get("evidence", {})
            ev_str = ev.get("excerpt", "") if isinstance(ev, dict) else str(ev)
            lines.append(f"[{f['severity']}] {f['title']} ({f['dimension']}) Confidence: {f.get('confidence',0):.2f} [{f.get('mode','')}]")
            lines.append(f"  Why: {f['why']}")
            lines.append(f"  Evidence: {ev_str}")
            if isinstance(ev, dict) and ev.get("note"):
                lines.append(f"  Note: {ev.get('note')}")
            if f.get("risk"):
                lines.append(f"  Risk: {f.get('risk')}")
            lines.append(f"  Required: {', '.join(f['required'])}")
            if f.get("optional"):
                lines.append(f"  Optional: {', '.join(f['optional'])}")
            if f.get("tests"):
                lines.append(f"  Tests: {', '.join(f.get('tests'))}")
            lines.append("")
        lines.append("SUGGESTED TESTS:")
        dims = {x["dimension"] for x in findings}
        if "idempotency" in dims or "timeout" in dims:
            lines.append("  • retry after provider success")
            lines.append("  • duplicate idempotency key")
        if "atomicity" in dims:
            lines.append("  • crash between writes")
            lines.append("  • DB failure after external success")
        if "concurrency" in dims:
            lines.append("  • concurrent requests on same record")
        if "recovery" in dims:
            lines.append("  • worker crash before ack → redelivery")
        lines.append("")
    lines.append("--- JSON ---")
    lines.append(_json(findings))
    return "\n".join(lines)

@mcp.tool(name="generate_failure_tests", description="Generate failure-oriented tests for a system/component.")
def generate_failure_tests_tool(system: str, component: str = "", language: str = "python") -> str:
    if not system:
        return _json({"error": "system description required"})
    tests = generate_failure_tests(system, component, language)
    lines = [f"FAILURE TESTS — {system}" + (f" / {component}" if component else ""), ""]
    for t in tests:
        lines.append(f"• {t['name']} ({t['covers']})")
        lines.append(f"  Scenario: {t['scenario']}")
        lines.append(f"  Hint: {t.get('snippet_hint','')}")
        lines.append("")
    lines.append("--- JSON ---")
    lines.append(_json(tests))
    return "\n".join(lines)

@mcp.tool(name="check_idempotency", description="Check whether an operation/code is safe to execute more than once.")
def check_idempotency_tool(code: str, operation: str = "") -> str:
    if not code:
        return _json({"error": "code required"})
    result = check_idempotency(code, operation)
    lines = [f"IDEMPOTENCY CHECK — {result['operation']}", f"Decision: {result['decision']}", f"Reason: {result['reason']}", ""]
    lines.append(f"Checks: {_json(result['checks'])}")
    if not result["idempotent"]:
        lines.append("")
        lines.append("REQUIRED:")
        for r in result["required_if_missing"]:
            lines.append(f"  • {r}")
        lines.append("")
        lines.append("Tests: " + ", ".join(result["tests"]))
    lines.append("")
    lines.append("--- JSON ---")
    lines.append(_json(result))
    return "\n".join(lines)

@mcp.tool(name="check_retry_safety", description="Determine whether retrying an operation can produce duplicate side effects or inconsistent state.")
def check_retry_safety_tool(code: str, operation: str = "") -> str:
    if not code:
        return _json({"error": "code required"})
    result = check_retry_safety(code, operation)
    lines = [f"RETRY SAFETY — {result['operation']}", f"Decision: {result['decision']}", f"Reason: {result['reason']}", ""]
    lines.append(f"Checks: {_json(result['checks'])}")
    if not result["retry_safe"]:
        lines.append("")
        lines.append("REQUIRED:")
        for r in result["required"]:
            lines.append(f"  • {r}")
    lines.append("")
    lines.append("--- JSON ---")
    lines.append(_json(result))
    return "\n".join(lines)

@mcp.tool(name="check_transaction_safety", description="Analyze database/state transitions for partial commits, crashes, rollback behavior, lost updates.")
def check_transaction_safety_tool(code: str, operation: str = "") -> str:
    if not code:
        return _json({"error": "code required"})
    result = check_transaction_safety(code, operation)
    lines = [f"TRANSACTION SAFETY — {result['operation']}", f"Decision: {result['decision']}", f"Reason: {result['reason']}", ""]
    lines.append(f"Checks: {_json(result['checks'])}")
    if not result["transaction_safe"]:
        lines.append("")
        lines.append("REQUIRED:")
        for r in result["required"]:
            lines.append(f"  • {r}")
        lines.append("")
        lines.append("Tests: " + ", ".join(result["tests"]))
    lines.append("")
    lines.append("--- JSON ---")
    lines.append(_json(result))
    return "\n".join(lines)

@mcp.tool(name="review_plan", description="Review an implementation plan (ordered steps) for failure ordering, idempotency, and transaction gaps. Use before coding to catch flawed ordering.")
def review_plan_tool(feature: str, plan: list = None, context: str = "") -> str:
    if not feature or not plan:
        return _json({"error": "feature and plan (list of steps) required"})
    result = review_plan(feature, plan, context)
    if "error" in result:
        return _json(result)
    lines = [f"PLAN REVIEW — {result['feature']}", ""]
    if not result["findings"]:
        lines.append("No ordering issues detected. Still ask: does any step have ambiguous outcome?")
    else:
        for f in result["findings"]:
            lines.append(f"[{f['severity']}] {f['title']} ({f['dimension']}) Confidence: {f.get('confidence', 0):.2f} [{f.get('mode','')}]")
            lines.append(f"  Failure: {f['failure']}")
            lines.append(f"  Why: {f['why']}")
            lines.append(f"  Evidence: {f.get('evidence','')}")
            lines.append(f"  Invariant: {f.get('invariant','')}")
            lines.append(f"  Required: {', '.join(f.get('required',[]))}")
            if f.get("tests"):
                lines.append(f"  Tests: {', '.join(f.get('tests',[]))}")
            lines.append("")
    lines.append("QUESTIONS:")
    for q in result["questions"]:
        lines.append(f"  • {q}")
    lines.append("")
    lines.append("--- JSON ---")
    lines.append(_json(result))
    return "\n".join(lines)

@mcp.tool(name="check_invariant", description="Check if declared invariants can be violated under failures. Provide invariants and architecture/plan/code context. Returns counter-scenarios.")
def check_invariant_tool(invariants: list, architecture: str = "", plan: list = None, code: str = "", context: str = "") -> str:
    if not invariants:
        return _json({"error": "invariants (list of strings) required"})
    result = check_invariant(invariants, architecture, plan, code, context)
    lines = ["INVARIANT CHECK", ""]
    for r in result["results"]:
        status = "VIOLATABLE" if r.get("violatable") else "LIKELY HOLDS"
        lines.append(f"[{status}] {r['invariant']} (confidence {r.get('confidence',0):.2f}, {r.get('dimension','')})")
        if r.get("violatable"):
            lines.append(f"  Scenario: {r.get('scenario','')}")
            lines.append(f"  Why: {r.get('why','')}")
            lines.append(f"  Required: {', '.join(r.get('required',[]))}")
            if r.get("tests"):
                lines.append(f"  Tests: {', '.join(r.get('tests',[]))}")
        else:
            lines.append(f"  Reason: {r.get('reason','')}")
        lines.append("")
    lines.append("--- JSON ---")
    lines.append(_json(result))
    return "\n".join(lines)

@mcp.tool(name="review_code_semantic", description="Semantic review — deterministic checks plus low-confidence heuristic for hard cases (ack ordering, lock scope, memory dedup). Deterministic findings are authoritative (0.68-0.96); semantic are 0.58-0.65 and require human review. No LLM by default.")
def review_code_semantic_tool(code: str, language: str = "python") -> str:
    if not code or not code.strip():
        return _json({"error": "code is required"})
    det = review_code(code, language)
    sem = semantic_review(code, det)
    lines = ["STATIC + SEMANTIC REVIEW", ""]
    lines.append(f"Deterministic: {len(det)} findings (authoritative)")
    lines.append(f"Semantic: {len(sem['semantic_findings'])} additional low-confidence (heuristic, requires human review)")
    lines.append("")
    for f in det:
        ev = f.get("evidence", {})
        ev_str = ev.get("excerpt", "") if isinstance(ev, dict) else str(ev)
        lines.append(f"[{f['severity']}] {f['title']} ({f['dimension']}) Confidence: {f.get('confidence',0):.2f} [{f.get('mode','')}]")
        lines.append(f"  Evidence: {ev_str}")
        lines.append("")
    if sem["semantic_findings"]:
        lines.append("--- SEMANTIC (low confidence, heuristic) ---")
        for f in sem["semantic_findings"]:
            lines.append(f"[{f['severity']}] {f['title']} ({f['dimension']}) Confidence: {f.get('confidence',0):.2f} [{f.get('mode','')}] provenance={f.get('provenance')}")
            lines.append(f"  Why: {f['why']}")
            lines.append(f"  Evidence: {f.get('evidence',{}).get('excerpt','')}")
            lines.append("")
        lines.append(sem["note"])
        lines.append("")
    lines.append("--- JSON ---")
    lines.append(_json({"deterministic": det, "semantic": sem["semantic_findings"], "meta": {"deterministic_count": sem["deterministic_count"], "llm_enabled": sem["llm_enabled"]}}))
    return "\n".join(lines)

@mcp.tool(name="list_failures", description="List known failure scenarios from the knowledge base.")
def list_failures_tool(filter: str = "") -> str:
    import pathlib as _pl, json as _js
    p = _pl.Path(__file__).parent / "knowledge" / "rules.json"
    rules = _js.loads(p.read_text(encoding="utf-8"))
    if filter:
        f = filter.lower()
        rules = [r for r in rules if f in r["dimension"] or f in r["title"].lower()]
    fail_dir = _pl.Path(__file__).parent.parent / "failures"
    extra = [x.stem for x in fail_dir.glob("*.md")] if fail_dir.exists() else []
    return _json({"rules": rules, "failure_docs": extra})

@mcp.resource("failures://principles/{principle_id}")
def get_principle_resource(principle_id: str) -> str:
    principles = load_principles()
    for p in principles:
        if p["id"] == principle_id:
            return json.dumps(p, indent=2)
    return json.dumps({"error": f"principle {principle_id} not found", "available": [p["id"] for p in principles]}, indent=2)

def main():
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()