# Worked Examples — Yoniso v3.1.0

Four examples demonstrating correct Yoniso application at each severity level.

---

## Example 1: LOW — Typo in Log Message

**Scenario:** Error log says "Conection failed" instead of "Connection failed".

### Yoniso Application

```
Yoniso: LOW — typo in error message at logger.py:45
Why: "Connection" misspelled as "Conection" in log string
Fix: Correct spelling at logger.py:45
Done. No further Yoniso analysis needed.
```

**Analysis:** One-layer is sufficient. No security, data-loss, or behavioral
impact. The "do not over-analyze LOW" rule applies.

---

## Example 2: MEDIUM — Missing Input Validation

**Scenario:** User can submit negative quantity via the `/api/order` endpoint.
The backend stores it and later division-by-quantity causes an error in
reporting.

### Yoniso Application

```
Yoniso Assessment: MEDIUM
Signals: non-primary path wrong behavior — valid orders work, but negative
         quantity causes downstream reporting error
Severity: MEDIUM — edge case, missing validation
Min Why Layers: 2

Root Cause Chain:
  L1: POST /api/order accepts quantity=-5 at order_handler.py:78
      because validate_order_input() only checks quantity != 0, not quantity > 0
  L2: validate_order_input() permits negative values because the validation
      schema at schemas/order.py:23 defines quantity as int without min=1
      constraint — no integration test covers negative inputs

Fix Decision: Add `min=1` constraint to quantity field in schemas/order.py:23 +
              add test_negative_quantity_rejected() to test_order_api.py

Verification: POST /api/order with quantity=-5 → expect 422; run pytest test_order_api.py

Feedback / Pattern Update:
  Predicted: MEDIUM → Actual: MEDIUM ✓
  Pattern: NEW — missing_min_validation on numeric fields
  Add check: grep all Pydantic/schema int fields for missing min/max constraints
```

---

## Example 3: HIGH — API Contract Break (Missing Field)

**Scenario:** v2.1 removed the `legacy_id` field from the `/api/users` response.
Three internal consumers still read it. No version bump. Production errors in
billing service.

### Yoniso Application

```
Yoniso Assessment: HIGH
Signals: API contract break — field removed without versioning, production
         regression in billing service
Severity: HIGH — wrong output on primary path for downstream consumers
Min Why Layers: 3 (E1 HIGH → 3 + E8 cross_subsystem → 3, highest = 3)

Root Cause Chain:
  L1: /api/users response no longer includes `legacy_id` field because
      UserSerializer at serializers/user.py:112 dropped it in commit a1b2c3d
  L2: The field removal was possible because no integration test covers
      downstream consumer contracts — only unit tests for the API itself
      exist at test_user_api.py; the billing service integration test at
      test_billing_integration.py was marked @skip 3 months ago
  L3: The review process allowed this because the API change was in a PR
      titled "cleanup: remove deprecated fields" — the word "cleanup"
      signaled low-risk to reviewers, and the @skip on the integration
      test wasn't flagged by CI as stale (no stale-skip lint rule)

Fix Decision: Revert field removal. Add `deprecated: true` annotation to
              `legacy_id` instead. Schedule removal with 2-version notice.
              Unskip and re-enable test_billing_integration.py.
              Add CI rule: blocked PRs cannot merge with @skip > 30 days.

Verification: Run full integration suite including billing.
              Confirm all 3 consumers can read `legacy_id`.

Feedback / Pattern Update:
  Predicted: HIGH → Actual: HIGH ✓
  Pattern: KNOWN — silent_API_break (hit count updated)
  Add guard: PR title containing "cleanup" + schema change → flag for
             API-review label in CI
```

---

## Example 4: CRITICAL — Auth Bypass via Timing Attack

**Scenario:** `verify_token()` at `auth.py:67` uses string `==` comparison
instead of `hmac.compare_digest()`, enabling timing-based token forgery.

### Yoniso Application

```
Yoniso Assessment: CRITICAL
Signals: auth bypass vector — non-constant-time token comparison,
         security boundary broken, remote exploitation possible
Severity: CRITICAL — auth bypass + security signal (auth middleware code)
Min Why Layers: 4 (E2 CRITICAL → 4)

Root Cause Chain:
  L1: verify_token() at auth.py:67 uses `==` for token comparison,
      which short-circuits on first non-matching byte, leaking token
      validity through response timing
  L2: Non-constant-time comparison is possible because auth.py imports
      standard string operations but does not import hmac — no code
      review checklist covered timing-attack surface for auth primitives
  L3: Review process allowed this because the security review step in
      CI only runs SAST (bandit) which doesn't flag `==` on strings as
      a timing vector — the check is too coarse. No human security
      review required for PRs touching auth.py.
  L4: The system permits this class because there is no crypto-primitive
      abstraction layer — each developer writes raw comparison logic in
      auth handlers instead of calling a vetted `secure_compare()`
      utility. No architecture decision recorded for auth patterns.

Fix Decision:
  Immediate: Replace `==` with `hmac.compare_digest()` at auth.py:67.
  Containment: Audit all `==` usage in auth/ directory for token/key
               comparisons (found 3 more at auth.py:89, session.py:34,
               crypto.py:112 — fix all).
  Prevention: Create `secure_compare()` utility at lib/crypto.py.
              Add CI rule: `hmac.compare_digest` required for all
              `==` operations on byte/string tokens in auth/ path.
  Rollback: No rollback needed — timing fix is backward-compatible.

Verification:
  - Unit test: test_verify_token_constant_time() — assert timing variance < 1ms
  - Integration test: token verification with valid/invalid tokens
  - Manual: security review of all `==` in auth/ directory
  - Blast radius: confirm no tokens issued during vulnerability window
    are suspected compromised; rotate all active tokens if unsure.

Feedback / Pattern Update:
  Predicted: CRITICAL → Actual: CRITICAL ✓
  Pattern: NEW — timing_attack_on_auth_primitive
  Knowledge base entry:
    {pattern: "timing_attack_on_auth_primitive",
     signals: ["== in auth dir", "token/key comparison", "no hmac import"],
     correct_severity: CRITICAL,
     correct_min_layers: 4,
     grep_targets: ["auth/", "session/", "crypto/", "token/"]}
```
