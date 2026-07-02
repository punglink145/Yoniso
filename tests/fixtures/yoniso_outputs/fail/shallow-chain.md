Yoniso Assessment: HIGH
Signals: wrong output on primary path at api.py:30
Severity: HIGH — primary path returns wrong result
Min Why Layers: 3
Root Cause Chain:
  L1: `get_user()` at api.py:30 returns the wrong row because the query filters on the wrong column
Fix Decision: Fix the column in the query at api.py:30
Verification: run the user test
