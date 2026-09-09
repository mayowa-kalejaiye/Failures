# Recovery

> How does the system return to a valid state?

## Question
After failure, can the system self-heal?

## Controls
- Reconciliation workers
- Dead-letter queues
- Compensating transactions
- Manual remediation runbooks

## Tests
- crash then restart, does state converge?
- poison message handling
