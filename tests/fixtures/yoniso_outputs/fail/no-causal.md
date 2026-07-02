Yoniso Assessment: MEDIUM
Signals: edge-case at order.py:12
Severity: MEDIUM — non-primary path wrong behavior
Min Why Layers: 2
Root Cause Chain:
  L1: `calc_total()` at order.py:12 returns 0 for empty cart
  L2: the function lacks a guard clause, change it to add a check
Fix Decision: Add a guard to `calc_total()` at order.py:12
Verification: run order test
