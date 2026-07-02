Yoniso Assessment: HIGH
Signals: observed race condition — lost update on the checkout primary path at checkout.py:88 under concurrent POST /checkout; cart total silently drops the last item
Severity: HIGH — observed race on a primary business path, non-deterministic failure
Min Why Layers: 3
Root Cause Chain:
  L1: `apply_discount()` at checkout.py:88 reads then writes `cart.total` non-atomically, because two concurrent requests both read the stale total and the later write wins, leading to a lost update
  L2: The write path has no row lock or transaction because `checkout()` was written for single-user mode and never wrapped in `SELECT ... FOR UPDATE`, allowing the interleaving — wrap the read-modify-write in a transaction
  L3: CI never exercised concurrent checkout because the suite is single-threaded, so the race was invisible — add a `test_concurrent_checkout` test category using a parallel harness
Fix Decision: Wrap the `cart.total` read-modify-write in `checkout.py:88` inside a `SELECT ... FOR UPDATE` transaction and add `test_concurrent_checkout`
Verification: Run the new parallel test asserting no lost update under 10 concurrent POST /checkout; check the row lock holds via `pg_locks`
Feedback / Pattern Update: predicted HIGH, actual HIGH. Log race-pattern for the inventory write paths next.
