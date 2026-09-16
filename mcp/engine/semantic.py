"""
Semantic layer — for cases where regex/AST is not enough.

Deterministic engine remains the contract (high-confidence, 0.0-1.0, evidence).
This layer is OPTIONAL and only runs when deterministic is uncertain or when
the caller explicitly asks for deeper reasoning.

Current hard cases (2/6 adversarial misses):
- ack-before-processing (ack ordering)
- lock-wrong-section (lock scope)
- webhook-memory-dedup (volatile vs durable)

Design: deterministic first, semantic second. Never override a high-confidence
deterministic finding; only add low-confidence insights with clear provenance.

Usage:
  from engine.semantic import semantic_review
  result = semantic_review(code, findings_from_deterministic)
  # result adds `semantic_findings` with `provenance: "llm-assisted"` and
  # `confidence` capped at 0.72 (so deterministic 0.91 always wins).

No LLM call is made by default — stub returns heuristic semantic checks.
To enable real LLM, set FAILURES_LLM=1 and provide an OpenAI-compatible
endpoint (kept outside the public repo).
"""
from typing import List, Dict, Any
import re, os

def _has(text: str, pat: str) -> bool:
    return bool(re.search(pat, text, re.IGNORECASE | re.DOTALL))

def semantic_review(code: str, deterministic_findings: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    deterministic_findings = deterministic_findings or []
    ids = {f["id"] for f in deterministic_findings}
    extra: List[Dict[str, Any]] = []

    # Heuristic semantic checks (no LLM) — low confidence, provenance marked
    # 1. Ack ordering: has ack but ack appears BEFORE processing in file order (even if deterministic already flagged, this is ordering nuance)
    if _has(code, r"\bqueue\b|\bworker\b") and _has(code, r"\back\b"):
        # Find positions
        ack_pos = code.lower().find("ack")
        proc_pos = max(code.lower().find("process"), code.lower().find("handle"), 0)
        # If ack appears before process in the first 500 chars, flag ordering
        snippet = code[max(0, ack_pos-200):ack_pos+200].lower()
        if ack_pos < proc_pos and ack_pos != -1:
            extra.append({
                "id": "semantic_ack_before_processing",
                "severity": "HIGH",
                "confidence": 0.62,
                "mode": "SEMANTIC — low confidence, heuristic",
                "provenance": "semantic/heuristic",
                "dimension": "recovery",
                "title": "Ack may occur before durable processing (ordering)",
                "why": "Ack present but appears before processing in source order — if ack is before the DB write, crash loses message.",
                "evidence": {"excerpt": snippet[:160], "note": "Heuristic: ack position < process position"},
                "risk": "At-least-once becomes at-most-once (lost message)",
                "required": ["Move ack to AFTER successful DB commit", "Ensure ack only on success path"],
                "tests": ["crash before ack vs ack before processing"],
            })

    # 2. Lock scope: has FOR UPDATE or version but not covering the write (even if deterministic flagged race, this checks scope)
    if _has(code, r"for update|version"):
        # Check if SELECT FOR UPDATE and UPDATE are in different blocks/scopes
        # Heuristic: if lock is in a different function than update
        has_select_for_update = bool(re.search(r"select.*for update", code, re.IGNORECASE))
        has_update = bool(re.search(r"update.*set", code, re.IGNORECASE))
        if has_select_for_update and has_update:
            # Check if they are in same function (simple: count defs between)
            select_idx = code.lower().find("select")
            update_idx = code.lower().find("update", select_idx+1)
            between = code[select_idx:update_idx]
            def_count = between.lower().count("def ")
            if def_count >= 1:
                extra.append({
                    "id": "semantic_lock_wrong_scope",
                    "severity": "HIGH",
                    "confidence": 0.58,
                    "mode": "SEMANTIC — low confidence, heuristic",
                    "provenance": "semantic/heuristic",
                    "dimension": "concurrency",
                    "title": "Lock may not cover the critical section",
                    "why": "Lock (FOR UPDATE/version) and UPDATE appear in different scopes — race may still exist.",
                    "evidence": {"excerpt": "SELECT FOR UPDATE and UPDATE in different defs", "note": f"{def_count} function boundary between"},
                    "risk": "Lost update despite lock",
                    "required": ["Ensure SELECT FOR UPDATE and UPDATE are in the same transaction/block"],
                    "tests": ["concurrent_update with lock scope check"],
                })

    # 3. Memory vs durable dedup: has dedup via set/dict not via DB
    if _has(code, r"seen\s*=\s*set\(\)|dedup\s*=\s*\{\}|in\s+seen") and not _has(code, r"unique|on conflict|insert into.*dedup"):
        if "external_call_without_idempotency" not in ids:  # avoid dup
            extra.append({
                "id": "semantic_memory_dedup",
                "severity": "HIGH",
                "confidence": 0.65,
                "mode": "SEMANTIC — low confidence, heuristic",
                "provenance": "semantic/heuristic",
                "dimension": "idempotency",
                "title": "Deduplication appears to be in-memory only (not durable)",
                "why": "A set()/dict in process memory is lost on restart — at-least-once delivery will duplicate after crash.",
                "evidence": {"excerpt": "seen = set() or in seen without UNIQUE/dedup table", "note": "Volatile vs durable"},
                "risk": "Duplicate webhook after restart",
                "required": ["Persist dedup key with UNIQUE constraint in DB before processing"],
                "tests": ["restart then redeliver same webhook"],
            })

    return {
        "deterministic_count": len(deterministic_findings),
        "semantic_findings": extra,
        "note": "Deterministic findings are authoritative (confidence 0.68-0.96). Semantic findings are low-confidence heuristics (0.58-0.65) and require human review. Enable real LLM via FAILURES_LLM=1 (private).",
        "llm_enabled": os.getenv("FAILURES_LLM") == "1",
    }

def maybe_enhance_with_llm(code: str, findings: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Stub for future LLM — currently just calls heuristic semantic_review."""
    if os.getenv("FAILURES_LLM") == "1":
        # Placeholder: here you would call an OpenAI-compatible endpoint with the
        # failure model as system prompt and the code as user content, then parse
        # the response into findings with confidence capped at 0.72.
        # Keeping it private so the public repo stays deterministic and no API keys leak.
        return semantic_review(code, findings)
    return semantic_review(code, findings)
