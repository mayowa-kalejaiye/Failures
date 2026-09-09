# Pattern: Circuit Breaker

States: CLOSED -> (failures > threshold) -> OPEN -> (timeout) -> HALF_OPEN

Prevents cascade. Fail fast when dependency is unhealthy.
