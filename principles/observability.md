# Observability

> How do we know what actually happened?

## Question
Can you answer "did payment 123 succeed?" from logs/metrics?

## Controls
- Structured logs with operation ID
- Metrics: success, failure, timeout, retry count
- Distributed tracing
- Audit log / transaction ledger

## Tests
- trigger failure, can you reconstruct timeline from logs?
