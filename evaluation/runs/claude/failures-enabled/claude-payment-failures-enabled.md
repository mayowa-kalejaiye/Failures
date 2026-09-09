Read-only snapshot below. Nothing was modified, no coding cycle was run, and I did **not** re-run the tests — the result shown is the one already produced earlier in this session. `git` confirms the project is **not** under version control.

---

## 1. Final project tree

`__pycache__/` and `.pyc` files omitted (build artifacts). Everything else is exactly as it stands on disk.

```
failures-eval-payment-failures/
├── .env.example
├── requirements.txt
├── requirements-dev.txt
├── pytest.ini
├── config.py
├── db.py
├── schemas.py
├── main.py
├── adapter/
│   ├── __init__.py
│   └── paystack.py
├── api/
│   ├── __init__.py
│   ├── deps.py
│   ├── payments.py
│   └── webhooks.py
├── jobs/
│   ├── __init__.py
│   └── reconcile.py
├── models/
│   ├── __init__.py
│   ├── _ids.py
│   ├── course.py
│   ├── enrollment.py
│   ├── payment.py
│   └── webhook_event.py
├── services/
│   ├── __init__.py
│   ├── enrollment.py
│   ├── errors.py
│   └── payments.py
├── webhook/
│   ├── __init__.py
│   └── handler.py
└── tests/
    ├── conftest.py
    ├── test_adapter_paystack.py
    ├── test_complete_payment.py
    ├── test_initialize_payment.py
    ├── test_invariants.py
    ├── test_reconcile.py
    └── test_webhook.py
```

(Also present: `.claude/settings.local.json` — Claude Code tooling config, not application code.)

## 2. git status

```
fatal: not a git repository (or any of the parent directories): .git
```

The project is **not** a git repository, so there is no VCS state to freeze or diff against. See §6 for the session change-record that `git status` would otherwise have surfaced.

## 3. Test result (already produced this session — not re-run)

Command used earlier: `python -m pytest -q --no-header -p no:cacheprovider`

```
....................................                                     [100%]
======================== warnings summary ========================
tests/test_invariants.py::test_end_to_end_happy_path_via_api
  ...PendingDeprecationWarning: Please use `import python_multipart` instead.
36 passed, 1 warning in 4.10s
```

**36 passed, 1 warning.** The single warning is a benign `PendingDeprecationWarning` from Starlette's multipart import — unrelated to this code.

## 4. Files relevant to payment / Paystack / enrollment / database / webhooks / tests

| Area | Files |
|---|---|
| **Payment processing** | `services/payments.py` (initialize + complete), `api/payments.py` (routes), `models/payment.py`, `schemas.py`, `services/errors.py`, `jobs/reconcile.py` (reconciliation of pending payments) |
| **Paystack integration** | `adapter/paystack.py`, `adapter/__init__.py`, `config.py` (secret/base-url/timeout/retry settings), `api/deps.py` (provides the client) |
| **Enrollment** | `services/enrollment.py`, `models/enrollment.py` |
| **Database / models** | `db.py` (engine + session), `models/__init__.py`, `models/payment.py`, `models/enrollment.py`, `models/course.py`, `models/webhook_event.py`, `models/_ids.py` |
| **Webhooks** | `webhook/handler.py`, `webhook/__init__.py`, `api/webhooks.py` |
| **Tests** | `tests/conftest.py`, `tests/test_adapter_paystack.py`, `tests/test_initialize_payment.py`, `tests/test_complete_payment.py`, `tests/test_webhook.py`, `tests/test_reconcile.py`, `tests/test_invariants.py` |
| **App wiring** | `main.py`, `api/__init__.py`, `jobs/__init__.py` |

## 5. Exact project directory

```
C:\Users\kalej\Documents\failures-eval-payment-failures
```

## 6. Change record for this Failures-enabled run (from session log, since git is absent)

Reported from this session's record — not from VCS, and not re-derived from disk (that listing was the tool call you stopped).

- **Created (test suite):** `tests/conftest.py`, `tests/test_adapter_paystack.py`, `tests/test_initialize_payment.py`, `tests/test_complete_payment.py`, `tests/test_webhook.py`, `tests/test_reconcile.py`, `tests/test_invariants.py`
- **Modified (2 source files):**
  - `pytest.ini` — added `asyncio_default_fixture_loop_scope = function`
  - `webhook/handler.py` — bug fix: `_get_event` → `_event_status` (the `MissingGreenlet` fix)
- **Unchanged:** the rest of the implementation (`config.py`, `db.py`, `schemas.py`, `main.py`, `models/*`, `adapter/*`, `services/*`, `api/*`, `jobs/*`, `webhook/__init__.py`, `requirements*.txt`, `.env.example`) — created earlier in the same build, untouched since.
- **Outside the project dir:** two notes were written to `…\.claude\…\memory\` during this session. They are my own session memory, not part of the implementation, and do not affect the frozen code.

The implementation is frozen as-is. I won't touch anything further.
