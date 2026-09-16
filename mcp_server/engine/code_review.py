import re
from typing import List, Dict, Any

# Heuristics are deterministic and honest about confidence.
# Output is STATIC FAILURE CHECK — not "BUG PROVEN" — unless syntactically certain.

def _has(text: str, pattern: str) -> bool:
    return bool(re.search(pattern, text, re.IGNORECASE | re.DOTALL))

def _snippet(code: str, pattern: str, max_len: int = 180) -> str:
    m = re.search(pattern, code, re.IGNORECASE | re.DOTALL)
    if not m:
        return ""
    s = m.group(0).strip().replace("\n", " ")
    return s[:max_len]

def _lines_of(code: str, pattern: str) -> str:
    for i, line in enumerate(code.splitlines(), 1):
        if re.search(pattern, line, re.IGNORECASE):
            return f"line {i}: {line.strip()[:160]}"
    return ""

def review_code(code: str, language: str = "python") -> List[Dict[str, Any]]:
    findings: List[Dict[str, Any]] = []

    has_external = _has(code, r"stripe|paystack|charge|payment.*provider|external_api|requests\.(post|get)|httpx|fetch\(|axios")
    has_idempotency = _has(code, r"idempotency[_-]?key|idempotent")
    if has_external and not has_idempotency:
        evidence_line = _lines_of(code, r"stripe|paystack|charge|requests\.|httpx|fetch\(|axios")
        findings.append({
            "id": "external_call_without_idempotency",
            "severity": "CRITICAL",
            "confidence": 0.91,
            "mode": "STATIC FAILURE CHECK",
            "dimension": "idempotency",
            "title": "External side-effect without idempotency key",
            "why": "Network boundary creates ambiguous outcome; timeout doesn't mean failure. Retry may duplicate the side effect (e.g., double charge).",
            "evidence": {
                "excerpt": evidence_line or "External call detected without idempotency_key handling",
                "note": "No idempotency_key in call path; retry after ambiguous timeout may duplicate",
                "snippet": _snippet(code, r".{0,40}(stripe|paystack|charge).{0,60}", 200),
            },
            "risk": "Retry after ambiguous timeout may duplicate charge",
            "required": ["persist idempotency key BEFORE external call", "unique constraint on key", "return cached response on duplicate"],
            "optional": ["reconciliation worker"],
            "tests": ["retry_after_provider_success", "duplicate_idempotency_key"],
        })

    db_writes = len(re.findall(r"execute\(|update |insert into|db\.execute|session\.commit|cursor\.execute|db\.query\(|db\.add\(|session\.add\(|\.commit\(\)", code, re.IGNORECASE))
    # avoid false positive from comment "no transaction" — require code-like transaction token
    # includes SQLAlchemy (session.begin/db.commit) so ORM code isn't silently skipped
    has_tx_code = _has(code, r"db\.transaction|\.transaction\(|\bBEGIN\b|\bCOMMIT\b|\.commit\(|atomic|session\.begin|with_for_update")
    has_tx_word = _has(code, r"\btransaction\b")
    has_tx = has_tx_code
    if has_tx_word and not has_tx_code:
        # only word transaction appears, likely in comment/docstring — not a real transaction
        lines_with_tx = [l for l in code.splitlines() if "transaction" in l.lower()]
        code_like = any("db.transaction" in l or "BEGIN" in l or "COMMIT" in l for l in lines_with_tx)
        has_tx = code_like
    has_charge_before_db = bool(re.search(r"(charge|paystack).*?\n.*?(update|insert|execute)", code.lower(), re.DOTALL))

    if db_writes >= 2 and not has_tx:
        findings.append({
            "id": "db_writes_not_transactional",
            "severity": "HIGH" if db_writes == 2 else "CRITICAL",
            "confidence": 0.96 if db_writes >= 2 else 0.80,
            "mode": "STATIC FAILURE CHECK",
            "dimension": "atomicity",
            "title": "Multiple DB writes without transaction",
            "why": "Crash between writes leaves partial state (e.g., debit without audit record).",
            "evidence": {"excerpt": f"{db_writes} DB writes detected without BEGIN/COMMIT", "note": "No transaction boundary found", "lines": _lines_of(code, r"execute\(|insert into|update ")},
            "risk": "Partial commit leaves invalid state",
            "required": ["wrap in DB transaction", "or use transactional outbox"],
            "optional": ["compensating action for distributed case"],
            "tests": ["crash_between_writes"],
        })

    if has_charge_before_db and not has_tx:
        findings.append({
            "id": "charge_then_db_update",
            "severity": "CRITICAL",
            "confidence": 0.88,
            "mode": "STATIC FAILURE CHECK",
            "dimension": "atomicity",
            "title": "External charge before durable local state",
            "why": "External effect cannot be rolled back; DB failure after charge leaves money taken but not recorded.",
            "evidence": {"excerpt": _lines_of(code, r"charge|paystack"), "note": "charge/external call appears before DB write without surrounding transaction/pending record", "snippet": _snippet(code, r"charge.{0,80}", 200)},
            "risk": "Money charged but not recorded; orphaned payment",
            "required": ["insert pending payment record BEFORE external call", "update to completed after success", "reconciliation for pending"],
            "optional": [],
            "tests": ["db_failure_after_provider_success"],
        })

    has_http = _has(code, r"requests\.|httpx\.|fetch\(|axios\.|urllib|paystack|stripe")
    has_timeout = _has(code, r"timeout\s*=")
    if has_http and not has_timeout:
        findings.append({
            "id": "no_timeout",
            "severity": "HIGH",
            "confidence": 0.85,
            "mode": "STATIC FAILURE CHECK",
            "dimension": "timeout",
            "title": "External call without timeout",
            "why": "Hung dependency exhausts workers; caller cannot distinguish success vs failure.",
            "evidence": {"excerpt": _lines_of(code, r"requests\.|httpx\.|fetch|stripe|paystack") or "HTTP/external call without timeout=", "note": "No timeout= parameter detected"},
            "risk": "Worker exhaustion; ambiguous outcome",
            "required": ["explicit timeout (e.g., timeout=5)", "treat TimeoutError as ambiguous, not failure"],
            "optional": ["circuit breaker"],
            "tests": ["dependency_timeout"],
        })

    has_select = _has(code, r"select.*where")
    has_update = _has(code, r"update.*set")
    has_lock = _has(code, r"for update|optimistic|version|cas|compare_and_swap|atomic")
    if has_select and has_update and not has_lock:
        findings.append({
            "id": "race_condition_read_modify_write",
            "severity": "HIGH",
            "confidence": 0.82,
            "mode": "STATIC FAILURE CHECK",
            "dimension": "concurrency",
            "title": "Read-modify-write without locking",
            "why": "Two concurrent requests can read stale state and overwrite each other (lost update).",
            "evidence": {"excerpt": _lines_of(code, r"select.*where") or "SELECT then UPDATE", "note": "No FOR UPDATE or version check detected"},
            "risk": "Lost update / double spend",
            "required": ["SELECT ... FOR UPDATE or optimistic locking with version column"],
            "optional": [],
            "tests": ["concurrent_update"],
        })

    has_queue = _has(code, r"\bqueue\b|kafka|sqs|celery|\bworker\b|\bconsumer\b")
    has_ack = _has(code, r"\back\b|acknowledge")
    if has_queue and not (has_ack and has_idempotency):
        findings.append({
            "id": "queue_no_ack_handling",
            "severity": "HIGH",
            "confidence": 0.78,
            "mode": "STATIC FAILURE CHECK",
            "dimension": "recovery",
            "title": "Queue processing may duplicate on redelivery",
            "why": "Crash before ack causes redelivery; without idempotent consumer, effect duplicates.",
            "evidence": {"excerpt": _lines_of(code, r"queue|worker|consumer") or "queue/worker detected", "note": "No explicit ack+idempotent handling found"},
            "risk": "At-least-once delivery becomes duplicate effect",
            "required": ["ack AFTER successful processing", "idempotent consumer with dedup table"],
            "optional": ["dead-letter queue"],
            "tests": ["crash_before_ack", "queue_duplicate_delivery"],
        })

    has_retry = _has(code, r"retry|backoff|tenacity|retrying")
    if has_retry and not has_idempotency:
        findings.append({
            "id": "unsafe_retry",
            "severity": "HIGH",
            "confidence": 0.87,
            "mode": "STATIC FAILURE CHECK",
            "dimension": "retry_safety",
            "title": "Retry without idempotency",
            "why": "Blind retry on non-idempotent operation doubles side effects.",
            "evidence": {"excerpt": _lines_of(code, r"retry|backoff"), "note": "retry logic without idempotency key"},
            "risk": "Retry amplifies duplicate side effects",
            "required": ["make operation idempotent first", "exponential backoff + jitter", "retry only on retryable errors (503/timeout, not 400)"],
            "optional": [],
            "tests": ["retry_after_provider_success"],
        })

    has_mutating = _has(code, r"@app\.post|@app\.put|router\.post|POST /")
    has_rate_code = _has(code, r"TokenBucket|rate_limit\s*\(|@limiter|throttle|limiter\.")
    # docstring "no rate limit" should not count as implementation
    if _has(code, r"no rate limit") and not has_rate_code:
        has_rate = False
    else:
        has_rate = has_rate_code
    if has_mutating and not has_rate:
        findings.append({
            "id": "no_rate_limit",
            "severity": "MEDIUM",
            "confidence": 0.72,
            "mode": "STATIC FAILURE CHECK",
            "dimension": "resource_exhaustion",
            "title": "Mutating endpoint without rate limiting",
            "why": "Unbounded writes can exhaust connection pool or DB.",
            "evidence": {"excerpt": _lines_of(code, r"@app\.post|@app\.put") or "POST/PUT handler", "note": "No rate limiter detected"},
            "risk": "Burst overwhelms backend",
            "required": ["token bucket rate limiter on mutating endpoints"],
            "optional": ["bounded queue + backpressure"],
            "tests": ["burst_rate_limit"],
        })

    has_req_id = _has(code, r"request.?id|operation.?id|correlation.?id|x-request-id")
    has_log = _has(code, r"log|logger")
    if not has_req_id and has_log:
        findings.append({
            "id": "missing_observability",
            "severity": "LOW",
            "confidence": 0.68,
            "mode": "STATIC FAILURE CHECK",
            "dimension": "observability",
            "title": "No operation/request ID for traceability",
            "why": "Cannot reconstruct what happened after a failure without correlating logs.",
            "evidence": {"excerpt": _lines_of(code, r"log"), "note": "logging without operation ID"},
            "risk": "Untraceable failure",
            "required": ["include operation/request ID in structured logs"],
            "optional": ["metrics for success/failure/timeout/retry"],
            "tests": ["reconstruct_from_logs"],
        })

    order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    findings.sort(key=lambda f: order.get(f["severity"], 99))
    return findings

def check_idempotency(code: str, operation: str = "") -> Dict[str, Any]:
    has_key = bool(re.search(r"idempotency", code, re.IGNORECASE))
    has_unique = bool(re.search(r"unique|on conflict|upsert|dedup", code, re.IGNORECASE))
    has_cached_resp = bool(re.search(r"cached|return.*existing|already.*completed", code, re.IGNORECASE))
    safe = has_key and has_unique
    conf = 0.93 if safe else (0.88 if has_key else 0.84)
    return {
        "operation": operation or "analyzed operation",
        "idempotent": safe,
        "confidence": conf,
        "mode": "STATIC FAILURE CHECK",
        "decision": "REQUIRES idempotency" if not safe else "PASS",
        "reason": "No idempotency key with persisted dedup detected" if not safe else "Idempotency key with dedup found",
        "evidence": {"has_idempotency_key": has_key, "has_unique_constraint": has_unique, "caches_response": has_cached_resp},
        "checks": {"has_idempotency_key": has_key, "has_unique_constraint_or_dedup": has_unique, "caches_response": has_cached_resp},
        "required_if_missing": ["client-supplied idempotency key", "DB unique constraint on (key)", "insert pending before side effect", "return cached response on duplicate key"],
        "tests": ["send same request twice with same key -> one effect", "same key different payload -> 422", "retry after timeout -> cached response"],
    }

def check_retry_safety(code: str, operation: str = "") -> Dict[str, Any]:
    has_retry = bool(re.search(r"retry|backoff", code, re.IGNORECASE))
    has_idemp = bool(re.search(r"idempotency", code, re.IGNORECASE))
    has_backoff = bool(re.search(r"backoff|jitter|exponential", code, re.IGNORECASE))
    has_circuit = bool(re.search(r"circuit.?breaker", code, re.IGNORECASE))
    safe = (not has_retry) or (has_retry and has_idemp and has_backoff)
    conf = 0.90 if (has_retry and not has_idemp) else 0.75
    return {
        "operation": operation or "analyzed operation",
        "retry_safe": safe,
        "confidence": conf,
        "mode": "STATIC FAILURE CHECK",
        "decision": "UNSAFE to retry" if not safe else ("NO retry logic (consider if transient failures need it)" if not has_retry else "PASS"),
        "reason": "Retry without idempotency risks duplicate side effects" if has_retry and not has_idemp else ("Missing backoff/jitter risks retry storm" if has_retry and not has_backoff else "No retry present or retry is guarded"),
        "evidence": {"has_retry": has_retry, "has_idempotency": has_idemp, "has_backoff_jitter": has_backoff, "has_circuit_breaker": has_circuit},
        "checks": {"has_retry": has_retry, "has_idempotency": has_idemp, "has_backoff_jitter": has_backoff, "has_circuit_breaker": has_circuit},
        "required": ["only retry idempotent operations", "exponential backoff + jitter", "retry budget / circuit breaker", "distinguish retryable vs non-retryable errors"],
        "tests": ["retry after 503 succeeds", "retry after timeout does not duplicate", "retry storm under failure does not cascade"],
    }

def check_transaction_safety(code: str, operation: str = "") -> Dict[str, Any]:
    writes = len(re.findall(r"execute\(|insert into|update |delete from", code, re.IGNORECASE))
    has_tx = bool(re.search(r"db\.transaction|\.transaction\(|\bBEGIN\b|\bCOMMIT\b|\.commit\(|atomic", code, re.IGNORECASE))
    has_rollback = bool(re.search(r"rollback", code, re.IGNORECASE))
    safe = writes <= 1 or has_tx
    conf = 0.96 if (writes >= 2 and not has_tx) else 0.80
    return {
        "operation": operation or "analyzed operation",
        "transaction_safe": safe,
        "confidence": conf,
        "mode": "STATIC FAILURE CHECK",
        "decision": "PASS" if safe else "REQUIRES transaction",
        "reason": f"{writes} writes {'inside' if has_tx else 'without'} transaction",
        "evidence": {"write_count": writes, "has_transaction": has_tx, "has_rollback": has_rollback},
        "checks": {"write_count": writes, "has_transaction": has_tx, "has_rollback": has_rollback},
        "required": ["BEGIN/COMMIT wrapping all writes", "rollback on error", "consider transactional outbox if publishing events"],
        "tests": ["crash between writes leaves no partial state", "DB failure after first write rolls back"],
    }
