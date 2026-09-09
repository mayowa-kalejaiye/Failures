# Pattern: Optimistic Locking

```sql
UPDATE accounts SET balance = :new, version = version+1 WHERE id=:id AND version=:old_version
-- if rowcount 0 => conflict, retry or abort
```
