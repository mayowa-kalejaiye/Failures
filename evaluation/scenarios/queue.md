# Scenario: queue

## Prompt

> Build a background job system for sending course completion certificates. When a student completes a course, enqueue a job that generates a PDF certificate via an external service and emails it. Use a queue and worker pool.

No mention of ack, deduplication, at-least-once, DLQ.

## Invariants

- `I1`: A certificate is sent at most once per completion (duplicate delivery must not duplicate effect)
- `I2`: A poison message must not stall the queue

## Expected (Failures-enabled)

- Worker acks AFTER durable processing
- Idempotent consumer via dedup table (msg_id unique)
- Dead-letter queue after N failures
- Outbox or transactional enqueue

## Checklist: duplicate delivery, crash before ack, poison message, out-of-order, pool exhaustion
