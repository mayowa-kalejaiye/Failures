import re
from typing import List, Dict, Any
from .loader import load_principles

# Component type -> relevant failure templates
COMPONENT_RULES = {
    "payment": [
        ("idempotency", "CRITICAL", "Duplicate charge on retry/timeout", "Network timeout creates ambiguous outcome; client retries → second charge.", ["idempotency key", "persisted operation state", "reconciliation worker"]),
        ("atomicity", "CRITICAL", "Charge succeeds but DB record fails", "External effect can't be rolled back.", ["persist pending before external call", "transaction for local writes"]),
        ("timeout", "HIGH", "Provider timeout handled as failure", "Timeout is ambiguous, not failure.", ["timeout + treat as pending", "reconciliation"]),
        ("concurrency", "HIGH", "Concurrent payment for same order", "Two workers process same payment", ["unique constraint on order_id", "SELECT FOR UPDATE"]),
        ("availability", "MEDIUM", "Provider down", "Payment provider unavailable", ["circuit breaker", "degraded response"]),
    ],
    "queue": [
        ("recovery", "HIGH", "Message redelivery causes duplicate processing", "Crash before ack → redelivery", ["idempotent consumer", "dedup table", "ack after success"]),
        ("ordering", "MEDIUM", "Messages out of order", "Queue doesn't guarantee order", ["sequence numbers", "idempotent out-of-order handling"]),
        ("resource_exhaustion", "MEDIUM", "Unbounded queue", "Producer faster than consumer", ["bounded queue", "backpressure", "DLQ"]),
        ("observability", "MEDIUM", "Poison message stalls consumer", "Repeated failure", ["DLQ + metrics", "max retries"]),
    ],
    "database": [
        ("atomicity", "CRITICAL", "Partial commit", "Crash between writes", ["transaction"]),
        ("concurrency", "HIGH", "Lost update", "Read-modify-write race", ["SELECT FOR UPDATE / optimistic locking"]),
        ("resource_exhaustion", "HIGH", "Pool exhaustion", "Too many concurrent holders", ["bounded pool", "timeouts", "rate limit"]),
        ("availability", "MEDIUM", "DB unavailable", "Connection drops", ["retry with backoff", "circuit breaker"]),
    ],
    "api": [
        ("resource_exhaustion", "MEDIUM", "No rate limiting", "Burst overwhelms backend", ["token bucket"]),
        ("timeout", "HIGH", "Slow downstream hangs request", "No timeout", ["explicit timeout", "circuit breaker"]),
        ("idempotency", "HIGH", "POST not idempotent", "Retry duplicates", ["idempotency key for mutating POST"]),
        ("observability", "LOW", "No request ID", "Can't trace failure", ["request ID in logs"]),
    ],
    "auth": [
        ("concurrency", "MEDIUM", "Race on token refresh", "Two refreshes issue two tokens", ["atomic compare-and-swap", "singleflight"]),
        ("resource_exhaustion", "MEDIUM", "Brute force login", "No rate limit", ["rate limit + lockout"]),
        ("consistency", "MEDIUM", "Stale session after revocation", "Replica/cache lag", ["revocation list / short TTL"]),
    ],
    "cache": [
        ("consistency", "MEDIUM", "Stale cache after write", "Cache not invalidated", ["write-through / invalidation"]),
        ("availability", "LOW", "Cache down", "Cache used as truth", ["fallback to DB", "treat cache as optional"]),
    ],
    "storage": [
        ("atomicity", "HIGH", "File saved but metadata not", "Partial success", ["atomic commit / transactional outbox"]),
        ("idempotency", "MEDIUM", "Duplicate upload", "Retry uploads twice", ["content hash dedup", "idempotency key"]),
        ("resource_exhaustion", "MEDIUM", "Large file exhausts memory", "No streaming", ["stream + chunked upload"]),
    ],
    "worker": [
        ("recovery", "HIGH", "Crash before ack", "Redelivery duplicate", ["idempotent + dedup"]),
        ("resource_exhaustion", "MEDIUM", "No concurrency limit", "OOM", ["bounded concurrency"]),
    ],
    "default": [
        ("atomicity", "HIGH", "Partial success leaves inconsistent state", "Operation has multiple steps with crash between", ["transaction"]),
        ("idempotency", "HIGH", "Retry duplicates side effect", "Network boundary → ambiguous", ["idempotency key"]),
        ("timeout", "HIGH", "No timeout handling", "Dependency hangs", ["timeout + ambiguous handling"]),
        ("concurrency", "MEDIUM", "Concurrent mutation race", "Lost update", ["locking"]),
        ("observability", "LOW", "Cannot reconstruct failure", "No trace ID", ["operation ID logging"]),
    ]
}

def _detect_component_type(name: str, description: str) -> str:
    text = f"{name} {description}".lower()
    for key in ["payment", "queue", "database", "auth", "cache", "storage", "worker"]:
        if key in text:
            return key
    if "api" in text or "endpoint" in text or "service" in text:
        return "api"
    return "default"

def analyze_component(component_type: str, description: str, dependencies: List[str] = None) -> Dict[str, Any]:
    dependencies = dependencies or []
    key = _detect_component_type(component_type, description)
    rules = COMPONENT_RULES.get(key, COMPONENT_RULES["default"])
    findings = []
    for dim, sev, title, why, required in rules:
        findings.append({
            "dimension": dim,
            "severity": sev,
            "title": title,
            "why": why,
            "required": required,
        })
    # add dependency-specific
    for dep in dependencies:
        d = dep.lower()
        if "postgres" in d or "db" in d or "database" in d:
            findings.append({"dimension": "atomicity", "severity": "HIGH", "title": f"Dependency {dep} — partial commit risk", "why": "Multiple writes to DB without transaction", "required": ["transaction"]})
        if "stripe" in d or "payment" in d:
            findings.append({"dimension": "idempotency", "severity": "CRITICAL", "title": f"Dependency {dep} — ambiguous outcome", "why": "External payment timeout", "required": ["idempotency key", "reconciliation"]})
        if "queue" in d or "kafka" in d or "sqs" in d:
            findings.append({"dimension": "recovery", "severity": "HIGH", "title": f"Dependency {dep} — redelivery", "why": "Queue redelivery", "required": ["idempotent consumer"]})
    return {
        "component": component_type,
        "detected_type": key,
        "description": description,
        "dependencies": dependencies,
        "findings": findings,
    }

def review_architecture(system: str, components: List[Dict[str, Any]], flows: List[str] = None, dependencies: List[str] = None) -> Dict[str, Any]:
    flows = flows or []
    dependencies = dependencies or []
    all_findings = []
    # heuristic based on text
    text = f"{system} {' '.join(flows)} {' '.join(dependencies)}".lower()
    # payment flow?
    if "payment" in text or "stripe" in text or "charge" in text:
        all_findings.append({
            "severity": "CRITICAL",
            "dimension": "idempotency",
            "confidence": 0.92,
            "mode": "STATIC FAILURE CHECK",
            "component": "payment",
            "title": "Duplicate payment on retry",
            "failure": "Payment provider succeeds but response times out; client retries → second charge.",
            "why": "Network boundary creates ambiguous outcome.",
            "invariant": "One logical payment must produce at most one charge.",
            "evidence": "payment/stripe/charge in system or flows",
            "required": ["idempotency key", "persisted operation state", "safe retry", "reconciliation"],
            "tests": ["provider succeeds then timeout", "same request retried", "duplicate idempotency key", "DB failure after provider success"],
        })
    if "database" in text or "postgres" in text or "db" in text:
        all_findings.append({
            "severity": "HIGH",
            "dimension": "atomicity",
            "component": "database",
            "confidence": 0.90,
            "mode": "STATIC FAILURE CHECK",
            "title": "Partial DB state on crash",
            "failure": "Crash between multiple writes leaves inconsistent state.",
            "why": "Writes not transactionally coupled.",
            "evidence": "database/postgres in system",
            "invariant": "All-or-nothing commit.",
            "required": ["BEGIN/COMMIT wrapping writes", "transactional outbox if publishing events"],
            "tests": ["crash between writes", "DB timeout after first write"],
        })
    if "queue" in text or "worker" in text or "consumer" in text:
        all_findings.append({
            "severity": "HIGH",
            "dimension": "recovery",
            "component": "queue/worker",
            "confidence": 0.89,
            "mode": "STATIC FAILURE CHECK",
            "title": "Duplicate processing on redelivery",
            "failure": "Worker crashes after processing but before ack; message redelivered.",
            "why": "At-least-once delivery.",
            "evidence": "queue/worker in system",
            "invariant": "Processing must be idempotent.",
            "required": ["idempotent consumer", "dedup table", "ack after success", "DLQ"],
            "tests": ["crash before ack", "message delivered twice", "poison message"],
        })
    if "cache" in text:
        all_findings.append({
            "severity": "MEDIUM",
            "dimension": "consistency",
            "component": "cache",
            "confidence": 0.75,
            "mode": "STATIC FAILURE CHECK",
            "title": "Stale cache serves wrong data",
            "failure": "Write updates DB but cache not invalidated.",
            "why": "Replica lag.",
            "evidence": "cache in system",
            "invariant": "Readers see committed state.",
            "required": ["cache invalidation or write-through", "version checks"],
            "tests": ["read after write returns stale"],
        })
    if "auth" in text or "login" in text:
        all_findings.append({
            "severity": "HIGH",
            "dimension": "resource_exhaustion",
            "component": "auth",
            "confidence": 0.80,
            "mode": "STATIC FAILURE CHECK",
            "title": "Brute force / no rate limit",
            "failure": "Unbounded login attempts.",
            "why": "Mutating endpoint without rate limit.",
            "evidence": "auth/login in system",
            "invariant": "Auth endpoints rate-limited and lockout.",
            "required": ["token bucket per IP/user", "lockout after N failures"],
            "tests": ["burst login attempts"],
        })
    # generic timeout/cascade
    if any(k in text for k in ["external", "api", "http", "service"]):
        all_findings.append({
            "severity": "HIGH",
            "dimension": "timeout",
            "component": "external dependency",
            "confidence": 0.84,
            "mode": "STATIC FAILURE CHECK",
            "title": "Timeout ambiguous; cascade risk",
            "failure": "Downstream hangs; workers exhausted; cascade to 500s.",
            "why": "No timeout / no circuit breaker.",
            "evidence": "external/api/http in system",
            "invariant": "Timeout bounded, ambiguous outcome handled.",
            "required": ["explicit timeout", "circuit breaker", "bulkhead"],
            "tests": ["downstream hangs 5s", "downstream returns 503"],
        })

    # per-component deep dive
    for c in components:
        name = c.get("name") or c.get("type") or "unknown"
        desc = c.get("description") or c.get("purpose") or ""
        deps = c.get("dependencies") or []
        comp = analyze_component(name, desc, deps)
        for f in comp["findings"]:
            # avoid duplicates
            if not any(x["title"] == f["title"] for x in all_findings):
                all_findings.append({
                    "severity": f["severity"],
                    "dimension": f["dimension"],
                    "component": name,
                    "title": f["title"],
                    "failure": f["why"],
                    "why": f["why"],
                    "invariant": f"Check {f['dimension']}",
                    "required": f["required"],
                    "tests": [],
                })

    # sort
    order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    all_findings.sort(key=lambda x: order.get(x["severity"], 99))

    questions = [
        "What happens if the server crashes after charging but before persisting?",
        "Can this operation be retried safely? What happens if it happens twice?",
        "Can two requests modify the same record concurrently?",
        "What happens when the external dependency times out — did it succeed?",
        "How does the system recover to a valid state after partial failure?",
        "How will you know what happened? (observability)",
    ]

    return {
        "system": system,
        "components": components,
        "flows": flows,
        "findings": all_findings,
        "questions": questions,
    }

def generate_failure_cases(system: str, components: List[str] = None, focus: str = "") -> List[Dict[str, Any]]:
    components = components or []
    base = [
        {"case": "Provider succeeds but response times out", "dimension": "timeout", "severity": "CRITICAL", "how": "Call external service; it processes, but network times out before response.", "effect": "Caller retries → duplicate side effect.", "mitigation": "idempotency key + reconciliation"},
        {"case": "Duplicate request / webhook redelivery", "dimension": "idempotency", "severity": "CRITICAL", "how": "Client retries after timeout, or webhook delivered twice.", "effect": "Two records / two charges.", "mitigation": "dedup table with unique constraint"},
        {"case": "Crash between two DB writes", "dimension": "atomicity", "severity": "CRITICAL", "how": "First write commits, process crashes before second.", "effect": "Partial/inconsistent state.", "mitigation": "transaction"},
        {"case": "Concurrent update lost", "dimension": "concurrency", "severity": "HIGH", "how": "Two requests read same balance and both subtract.", "effect": "Lost update.", "mitigation": "SELECT FOR UPDATE or optimistic locking"},
        {"case": "Downstream timeout cascades", "dimension": "availability", "severity": "HIGH", "how": "Slow dependency holds workers.", "effect": "Thread pool exhaustion → 500s.", "mitigation": "timeout + circuit breaker + bulkhead"},
        {"case": "Queue redelivery after crash-before-ack", "dimension": "recovery", "severity": "HIGH", "how": "Worker processes then crashes before ack.", "effect": "Message processed twice.", "mitigation": "idempotent consumer"},
        {"case": "Out-of-order events", "dimension": "ordering", "severity": "MEDIUM", "how": "Events arrive reversed due to retry/delay.", "effect": "Stale overwrites fresh.", "mitigation": "sequence numbers; last-write-wins only if safe"},
        {"case": "Pool exhaustion under burst", "dimension": "resource_exhaustion", "severity": "MEDIUM", "how": "Burst of requests holds all connections.", "effect": "Timeout waiting for connection.", "mitigation": "bounded pool + rate limiting"},
        {"case": "Cache stale after write", "dimension": "consistency", "severity": "MEDIUM", "how": "DB updated, cache not invalidated.", "effect": "Readers see stale.", "mitigation": "invalidation/write-through"},
        {"case": "Retry storm", "dimension": "retry_safety", "severity": "MEDIUM", "how": "All clients retry simultaneously on 503.", "effect": "Thundering herd.", "mitigation": "jitter + retry budget + circuit breaker"},
    ]
    if focus:
        f = focus.lower()
        base = [c for c in base if f in c["dimension"] or f in c["case"].lower()] or base
    return base

def review_plan(feature: str, plan: List[str], context: str = "") -> Dict[str, Any]:
    """Analyze an implementation plan (ordered steps) for failure ordering issues."""
    if not feature or not plan:
        return {"error": "feature and plan required"}
    text = " ".join(plan).lower()
    ctx = (feature + " " + context).lower()
    combined = text + " " + ctx
    findings = []

    # helper: find index of step containing keyword
    def idx_of(keywords):
        for i, step in enumerate(plan):
            low = step.lower()
            if any(k in low for k in keywords):
                return i
        return None

    # Rule 1: external call before durable state
    idx_pending = idx_of(["pending", "create payment record", "persist", "idempotency key", "save pending"])
    idx_external = idx_of(["paystack", "stripe", "charge", "external", "provider", "call pay"])
    if idx_external is not None:
        if idx_pending is None or idx_pending > idx_external:
            findings.append({
                "severity": "CRITICAL",
                "confidence": 0.90,
                "mode": "STATIC FAILURE CHECK",
                "dimension": "atomicity",
                "title": "External side-effect before durable local state",
                "failure": f"Step {idx_external+1} calls external provider before establishing durable pending state",
                "why": "If provider succeeds and server crashes, orphaned payment with no record to reconcile",
                "evidence": f"plan[{idx_external}]: {plan[idx_external]}",
                "invariant": "Pending record must exist before external call",
                "required": ["1. Create pending payment record", "2. Generate idempotency key", "3. Persist provider reference", "4. Then call provider", "5. Make subsequent steps conditional on verified payment"],
                "tests": ["crash after provider success before save", "webhook arrives before API response"],
            })
        # also check idempotency key before external
        idx_idem = idx_of(["idempotency"])
        if idx_idem is None or idx_idem > idx_external:
            findings.append({
                "severity": "CRITICAL",
                "confidence": 0.91,
                "mode": "STATIC FAILURE CHECK",
                "dimension": "idempotency",
                "title": "No idempotency establishment before retryable external call",
                "failure": "External call is retryable but no idempotency key established beforehand",
                "why": "Ambiguous outcome: timeout does not mean failure; retry will duplicate",
                "evidence": f"plan[{idx_external}]: {plan[idx_external]} without prior idempotency step",
                "invariant": "One logical payment produces at most one charge",
                "required": ["Generate idempotency key", "Persist with unique constraint before external call", "Return cached response on duplicate"],
                "tests": ["provider succeeds then timeout, client retries", "duplicate webhook delivery"],
            })

    # Rule 2: enrollment / side effect not conditional on verified payment
    idx_enroll = idx_of(["enroll", "fulfill", "provision"])
    idx_verify = idx_of(["verify", "webhook", "confirm", "check payment status", "reconcile"])
    if idx_enroll is not None:
        if idx_verify is None:
            findings.append({
                "severity": "CRITICAL",
                "confidence": 0.88,
                "mode": "STATIC FAILURE CHECK",
                "dimension": "atomicity",
                "title": "Enrollment not gated on verified payment",
                "failure": f"Step {idx_enroll+1} ({plan[idx_enroll]}) appears unconditional",
                "why": "Plan enrolls before payment is verified; crash or duplicate webhook breaks invariant",
                "evidence": f"plan[{idx_enroll}]: {plan[idx_enroll]} without preceding verify step",
                "invariant": "Student must never be enrolled without successful payment",
                "required": ["Enroll only after payment verified (webhook or status check)", "Make enrollment idempotent", "Handle webhook deduplication"],
                "tests": ["webhook arrives twice", "crash between payment success and enrollment"],
            })
        elif idx_verify is not None and idx_enroll < idx_verify:
            findings.append({
                "severity": "HIGH",
                "confidence": 0.86,
                "mode": "STATIC FAILURE CHECK",
                "dimension": "ordering",
                "title": "Enrollment ordered before verification",
                "failure": "Enrollment step precedes verification step",
                "why": "Out-of-order execution or crash violates payment->enrollment invariant",
                "evidence": f"enroll at {idx_enroll}, verify at {idx_verify}",
                "invariant": "Enrollment requires verified payment",
                "required": ["Reorder: verify payment before enroll", "Make enroll idempotent with dedup key"],
                "tests": ["concurrent webhook and API retry"],
            })

    # Rule 3: webhook handling without dedup
    idx_webhook = idx_of(["webhook"])
    if idx_webhook is not None:
        has_dedup = any("dedup" in s.lower() or "idempoten" in s.lower() for s in plan)
        if not has_dedup:
            findings.append({
                "severity": "HIGH",
                "confidence": 0.83,
                "mode": "STATIC FAILURE CHECK",
                "dimension": "idempotency",
                "title": "Webhook handling without deduplication",
                "failure": "Webhook step without dedup/idempotency",
                "why": "Provider may deliver webhook twice (at-least-once)",
                "evidence": f"plan[{idx_webhook}]: {plan[idx_webhook]}",
                "invariant": "Webhook processed exactly once per logical event",
                "required": ["Persist webhook event_id with unique constraint", "Return 200 for duplicates"],
                "tests": ["webhook delivered twice", "webhook replay after timeout"],
            })

    # Rule 4: missing transaction boundary for local writes
    local_writes = sum(1 for s in plan if any(k in s.lower() for k in ["save", "create", "update", "insert", "write", "persist"]))
    has_tx_step = any("transaction" in s.lower() or "atomic" in s.lower() for s in plan)
    if local_writes >= 2 and not has_tx_step:
        findings.append({
            "severity": "HIGH",
            "confidence": 0.78,
            "mode": "STATIC FAILURE CHECK",
            "dimension": "atomicity",
            "title": "Multiple local writes without transaction",
            "failure": f"{local_writes} writes in plan without transaction/ outbox step",
            "why": "Crash between writes leaves partial state",
            "evidence": f"{local_writes} write-like steps without transaction",
            "invariant": "All-or-nothing local state",
            "required": ["Wrap writes in transaction or transactional outbox"],
            "tests": ["crash between writes"],
        })

    # Rule 5: retry without safety
    has_retry = any("retry" in s.lower() for s in plan)
    has_idem_any = any("idempoten" in s.lower() for s in plan)
    if has_retry and not has_idem_any:
        findings.append({
            "severity": "HIGH",
            "confidence": 0.81,
            "mode": "STATIC FAILURE CHECK",
            "dimension": "retry_safety",
            "title": "Retry step without idempotency",
            "failure": "Plan retries without ensuring idempotency",
            "why": "Blind retry doubles side effects",
            "evidence": "retry in plan without idempotency",
            "invariant": "Retries safe only for idempotent operations",
            "required": ["Ensure idempotency before retry", "Exponential backoff + jitter"],
            "tests": ["retry after timeout duplicates?"],
        })

    questions = [
        "What happens if Paystack succeeds and your server crashes before the next step?",
        "What happens if the webhook arrives twice?",
        "What happens if the student retries payment after timeout?",
        "What happens if two requests enroll the same student concurrently?",
        "How does the system recover pending payments?",
    ]

    return {
        "feature": feature,
        "plan": plan,
        "context": context,
        "findings": sorted(findings, key=lambda x: {"CRITICAL":0,"HIGH":1,"MEDIUM":2,"LOW":3}[x["severity"]]),
        "questions": questions,
    }


def check_invariant(invariants: List[str], architecture: str = "", plan: List[str] = None, code: str = "", context: str = "") -> Dict[str, Any]:
    """Check if declared invariants can be violated under failures."""
    plan = plan or []
    results = []
    text = " ".join([architecture, context, code] + plan).lower()
    inv_text = " ".join(invariants).lower()

    def _violatable(invariant: str, scenario: str, why: str, dimension: str, severity: str, confidence: float, required: List[str], tests: List[str]):
        return {
            "invariant": invariant,
            "violatable": True,
            "confidence": confidence,
            "mode": "STATIC FAILURE CHECK",
            "dimension": dimension,
            "scenario": scenario,
            "why": why,
            "required": required,
            "tests": tests,
        }

    for inv in invariants:
        low = inv.lower()
        # invariant: never enrolled without successful payment
        if any(k in low for k in ["enroll", "student"]) and any(k in low for k in ["payment", "pay"]):
            # check if plan/code lacks verified gate
            has_verify = any(k in text for k in ["verify", "webhook", "confirm", "check status", "reconcile"])
            has_pending_first = "pending" in text and ("paystack" in text or "stripe" in text or "charge" in text)
            # heuristic: if no verify or payment before enroll, violatable
            if not has_verify or not has_pending_first:
                results.append(_violatable(
                    inv,
                    "Payment succeeds -> server crashes -> enrollment transaction never commits, or enrollment happens before verification",
                    "No durable pending state before external call and enrollment not gated on verified payment",
                    "atomicity",
                    "CRITICAL",
                    0.88,
                    ["Create pending payment before provider call", "Gate enrollment on verified payment status", "Make enrollment idempotent", "Reconciliation worker for pending payments"],
                    ["crash after provider success", "webhook arrives twice", "concurrent enrollment requests"]
                ))
            else:
                results.append({"invariant": inv, "violatable": False, "confidence": 0.72, "mode": "STATIC FAILURE CHECK", "reason": "Plan appears to gate enrollment on verified payment with pending state; still verify idempotency and dedup"})
        elif any(k in low for k in ["double charge", "charged twice", "at most once", "never charged twice"]):
            has_idem = "idempotency" in text or "idempotent" in text
            if not has_idem:
                results.append(_violatable(
                    inv,
                    "Provider succeeds but response times out; client retries -> second charge",
                    "No idempotency key; ambiguous outcome treated as failure",
                    "idempotency",
                    "CRITICAL",
                    0.91,
                    ["Idempotency key with unique constraint before provider call", "Persist operation state", "Return cached response on duplicate key"],
                    ["retry after provider success", "duplicate idempotency key"]
                ))
            else:
                results.append({"invariant": inv, "violatable": False, "confidence": 0.75, "mode": "STATIC FAILURE CHECK", "reason": "Idempotency mechanism present; verify unique constraint and cached response"})
        else:
            # generic invariant: search for relevant dimension keywords
            sev = "HIGH"
            dim = "atomicity"
            if "concurrent" in low or "twice" in low:
                dim = "concurrency"
            if "timeout" in low:
                dim = "timeout"
            results.append({
                "invariant": inv,
                "violatable": True,
                "confidence": 0.70,
                "mode": "STATIC FAILURE CHECK",
                "dimension": dim,
                "scenario": f"Check if failure can break: {inv} — manual review needed",
                "why": "No specific rule for this invariant; requires human + plan/architecture review",
                "required": ["Define failure scenarios for this invariant", "Add tests that attempt violation"],
                "tests": ["generate_failure_cases with focus on " + dim],
                "note": "Generic fallback — add domain rule for precise check",
            })

    return {
        "invariants": invariants,
        "context": {"architecture": architecture, "plan": plan, "code_excerpt": code[:300] if code else ""},
        "results": results,
    }


def generate_failure_tests(system: str, component: str = "", language: str = "python") -> List[Dict[str, Any]]:
    tests = [
        {"name": "retry_after_provider_success", "covers": "timeout+idempotency", "scenario": "Provider succeeds, response times out, client retries with same idempotency key → one charge, cached response."},
        {"name": "duplicate_idempotency_key", "covers": "idempotency", "scenario": "Send same key twice with same payload → second returns cached, no new side effect."},
        {"name": "same_key_different_payload", "covers": "idempotency", "scenario": "Same key with different amount → 422 error."},
        {"name": "db_failure_after_provider_success", "covers": "atomicity", "scenario": "DB down after external charge → pending state reconciled later, no lost charge."},
        {"name": "crash_between_writes", "covers": "atomicity", "scenario": "Kill process between two writes → no partial state visible (rolled back)."},
        {"name": "concurrent_update", "covers": "concurrency", "scenario": "Two parallel requests modify same record → one succeeds, other gets 409 or serializes correctly."},
        {"name": "dependency_timeout", "covers": "timeout", "scenario": "Downstream hangs > timeout → returns 504 quickly, does not hold worker."},
        {"name": "dependency_unavailable", "covers": "availability", "scenario": "Downstream 503 → circuit opens, subsequent calls fail fast."},
        {"name": "queue_duplicate_delivery", "covers": "recovery", "scenario": "Same message delivered twice → processed once."},
        {"name": "crash_before_ack", "covers": "recovery", "scenario": "Worker crashes before ack → message redelivered and handled idempotently."},
        {"name": "out_of_order_events", "covers": "ordering", "scenario": "Events delivered out of order → final state correct."},
        {"name": "burst_rate_limit", "covers": "resource_exhaustion", "scenario": "Burst 100 req/s → rate limited, pool not exhausted."},
    ]
    # filter a bit by component hint
    if component:
        c = component.lower()
        if "payment" in c:
            tests = [t for t in tests if t["covers"] in ["timeout+idempotency", "idempotency", "atomicity"]]
        elif "queue" in c:
            tests = [t for t in tests if "recovery" in t["covers"] or "ordering" in t["covers"]]
        elif "auth" in c:
            tests = [t for t in tests if t["covers"] in ["concurrency", "resource_exhaustion", "atomicity"]] + tests[:2]
    # produce code snippets hint
    for t in tests:
        if language == "python":
            t["snippet_hint"] = f"# pytest: simulate {t['name']} with mocks/monkeypatch"
        elif language == "javascript":
            t["snippet_hint"] = f"// jest: mock {t['name']}"
    return tests
