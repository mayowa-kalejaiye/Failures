# Pattern: Transactional Outbox

Atomic DB commit + event publish.

```
BEGIN
  INSERT INTO orders ...
  INSERT INTO outbox (event_type, payload) ...
COMMIT
-> relay publishes outbox to queue
```

Prevents: DB commit succeeds but event never published (partial failure).
