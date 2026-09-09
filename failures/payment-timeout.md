# Failure: Payment Timeout (Ambiguous Outcome)

Scenario: payment provider charges card, response lost due to timeout.
Retry causes duplicate charge.
Severity: CRITICAL
Principle: timeout + idempotency
Mitigation: idempotency key, reconciliation worker.
