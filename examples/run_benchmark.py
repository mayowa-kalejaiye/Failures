"""Golden benchmark — proves MCP has teeth: naive fails loud, improved quiets."""
import sys, pathlib, json
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "mcp_server"))

from engine.code_review import review_code
from engine.analyzer import review_plan, check_invariant

ROOT = pathlib.Path(__file__).parent

def score(code: str):
    findings = review_code(code)
    crit = sum(1 for f in findings if f["severity"] == "CRITICAL")
    high = sum(1 for f in findings if f["severity"] == "HIGH")
    ids = {f["id"] for f in findings}
    return {"findings": findings, "critical": crit, "high": high, "ids": ids, "total": len(findings)}

def check_example(name: str) -> bool:
    base = ROOT / name
    naive = (base / "naive.py").read_text(encoding="utf-8")
    improved = (base / "improved.py").read_text(encoding="utf-8")
    expected = json.loads((base / "expected.json").read_text(encoding="utf-8"))

    n = score(naive)
    i = score(improved)

    ok = True
    print(f"\n=== {name} ===")
    print(f"  naive: {n['critical']} CRITICAL, {n['high']} HIGH, total {n['total']} ids={sorted(n['ids'])}")
    print(f"  improved: {i['critical']} CRITICAL, {i['high']} HIGH, total {i['total']} ids={sorted(i['ids'])}")

    exp_n = expected.get("naive", {})
    for fid in exp_n.get("expected_findings", []):
        if fid not in n["ids"]:
            print(f"  FAIL: naive expected {fid} not found")
            ok = False

    exp_i = expected.get("improved", {})
    for fid in exp_i.get("expected_findings_absent", exp_i.get("expected_absent", [])):
        if fid in i["ids"]:
            print(f"  FAIL: improved should not have {fid}")
            ok = False
    if "max_critical" in exp_i and i["critical"] > exp_i["max_critical"]:
        print(f"  FAIL: improved critical {i['critical']} > {exp_i['max_critical']}")
        ok = False
    if i["total"] >= n["total"] and n["total"] > 0:
        print(f"  WARN: improved total {i['total']} not fewer than naive {n['total']}")

    if ok:
        print("  PASS")
    return ok

def test_plan():
    print("\n=== review_plan (payment) ===")
    plan = ["Create payment", "Call Paystack", "Save transaction", "Enroll student", "Send email"]
    res = review_plan("Course payment and enrollment", plan)
    titles = {f["title"] for f in res["findings"]}
    print(f"  findings: {titles}")
    ok = "External side-effect before durable local state" in titles and "Enrollment not gated on verified payment" in titles
    print("  PASS" if ok else "  FAIL: expected plan findings missing")
    return ok

def test_invariant():
    print("\n=== check_invariant ===")
    res = check_invariant(
        invariants=["A student must never be enrolled without a successful payment", "A payment must never be charged twice"],
        architecture="Payment API with FastAPI, Postgres, Paystack",
        plan=["Call Paystack", "Save transaction", "Enroll student"],
    )
    viol = [r for r in res["results"] if r.get("violatable")]
    print(f"  violatable: {[r['invariant'][:30] for r in viol]}")
    ok = len(viol) >= 1
    print("  PASS" if ok else "  FAIL")
    return ok

if __name__ == "__main__":
    examples = ["payment", "queue", "auth", "file-upload", "inventory"]
    results = [check_example(e) for e in examples]
    results += [test_plan(), test_invariant()]
    print("\n" + ("ALL PASS" if all(results) else "SOME FAIL"))
    sys.exit(0 if all(results) else 1)
