Yoniso Assessment: MEDIUM
Signals: edge-case wrong behavior — empty-string SKU at inventory.py:21 returns 200 with a null row instead of 400; non-primary path only
Severity: MEDIUM — incomplete input validation on a non-primary path
Min Why Layers: 2
Root Cause Chain:
  L1: `lookup_sku()` at inventory.py:21 returns a row for the empty string because the guard only checks for `None`, allowing `""` to hit the database and yield a null result
  L2: The function has no empty-string validation because the schema permits nullable SKU and no caller-side guard exists — add an explicit `if not sku: raise ValueError` guard
Fix Decision: Add an empty-string guard to `lookup_sku()` at inventory.py:21 returning HTTP 400, and add `test_lookup_empty_sku`
Verification: Run `pytest inventory_test.py::test_lookup_empty_sku`; POST an empty SKU and assert 400
Feedback / Pattern Update: predicted MEDIUM, actual MEDIUM.
