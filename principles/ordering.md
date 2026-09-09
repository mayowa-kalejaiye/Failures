# Ordering

> What if events arrive out of order?

## Question
Does correctness depend on event order?

## Failure Mode
- Out-of-order messages cause stale state to overwrite fresh state
- Race between create and delete

## Controls
- Version vectors / sequence numbers
- Last-write-wins with logical clocks only when safe
- Causal ordering, idempotent consumers
- Buffer + reorder by sequence

## Tests
- deliver events in reverse order
- delayed message arrives late
