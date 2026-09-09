# Scenario: webhook (Paystack webhook ingestion)

## Prompt

> Build a webhook endpoint that receives Paystack payment events and updates payment status. Paystack may resend events.

No mention of deduplication, idempotency, or ordering.

## Invariants

- `I1`: A webhook event must be processed exactly once per logical event (at-least-once delivery -> exactly-once effect)
- `I2`: Out-of-order webhooks must not corrupt payment state (e.g., failure webhook arriving after success)

## Expected Failures-enabled

- Persist `event_id` with UNIQUE constraint before processing
- Idempotent state machine: pending -> completed, ignore completed
- Sequence/version check for ordering
