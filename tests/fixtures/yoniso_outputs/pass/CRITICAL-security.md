Yoniso Assessment: CRITICAL
Signals: auth bypass via forged JWT `alg=none` accepted at auth.py:42; no signature verification on the None-alg branch
Severity: CRITICAL — auth bypass breaks the privilege boundary; security_bug=true (auth middleware + JWT parsing)
Min Why Layers: 4
Root Cause Chain:
  L1: `verify_jwt()` at auth.py:42 returns True when the header `alg` is `none`, because the None-alg branch skips the signature check
  L2: `verify_jwt()` lacks an algorithm allowlist because it was added in v2.1 without a downgrade threat model, allowing forgery across all 8 call sites — fix by adding `allowed_algs` to `verify_jwt()`
  L3: PR #1042 merged without a security gate because CI has no auth-path test category, so the downgrade slipped past review — add a `test_reject_none_alg` test category to CI
  L4: The service trusts client-supplied header fields because no request-level validator abstraction exists, which caused the bypass class system-wide — add a `RequestValidator` abstraction to gate untrusted input
Fix Decision: Add `allowed_algs = ["HS256"]` allowlist to `verify_jwt()` at auth.py:42, add `test_reject_none_alg` to auth_test.py, and add a CI gate `no-unverified-auth`
Verification: Run `pytest auth_test.py::test_reject_none_alg`; forge an `alg=none` token against /login and assert HTTP 401
Feedback / Pattern Update: predicted CRITICAL, actual CRITICAL. Add "JWT alg-downgrade" to the known-pattern KB and grep all `verify_*` call sites.
