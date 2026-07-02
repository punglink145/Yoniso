Yoniso Assessment: MEDIUM
Signals: missing validation at form.py:5
Severity: MEDIUM — incomplete guard
Min Why Layers: 2
Root Cause Chain:
  L1: `validate()` at form.py:5 accepts negative numbers because the lower bound is unset
  L2: the validator omits a floor check, so add a `min=0` constraint to fix the gap
Fix Decision: After analysis we determined that a guard would help prevent negative inputs in the future.
Verification: run form test
