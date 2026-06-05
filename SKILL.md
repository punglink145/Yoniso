---
name: yoniso
description: YONISO-MANASIKARA v3.0.0 — recursive root questioning with signal-based classification (not self-report). Three-phase discipline: (1) PRE-FIX assess severity/security/data-loss from observable signals, (2) DURING-FIX chain why-layers through quality heuristics, (3) POST-FIX gate with feedback loop. Trigger on /yoniso and proactively on any fix, plan, review, or architectural decision.
---

# Yoniso — Recursive Root Questioning v3.0.0

YONISO-MANASIKARA: ก่อนแก้ — ประเมินความลึกจากสัญญาณที่สังเกตได้. ระหว่างแก้ — ถาม "ทำไม" แต่ละชั้นต้องผ่านเกณฑ์คุณภาพ. หลังแก้ — gate + feedback loop.

**v3.0.0 fixes 6 structural gaps from v2:**
1. Self-reporting trust → signal-based auto-classification
2. Layer quality not validated → 4-point quality heuristic per layer
3. Weak signal (files_touched) → change_type dimension added
4. Length proxy for depth → qualitative shallow-output criteria
5. Reactive-only → 3-phase proactive (recite before, guide during, gate after)
6. No feedback loop → post-fix discrepancy audit

---

## Recital (recite verbatim as the first thing in your response)

> **YONISO-MANASIKARA v3.0.0:**
> 1. **PRE-FIX ASSESS.** Classify severity/security/data-loss from observable signals — not your opinion. Crash/data-loss/auth-bypass = CRITICAL. Wrong output/API break = HIGH. Edge-case/validation = MEDIUM. Typo/rename = LOW. Security signals: auth middleware, crypto, session, SQL construction, shell exec, deserialization. Data-loss signals: DELETE/TRUNCATE/DROP, column removal, state mutation without backup, filesystem write without transaction.
> 2. **COMPUTE DEPTH.** Escalation matrix dictates min layers from signals. Base = 2. CRITICAL/security/data-loss/recurrence = 4. HIGH/known-pattern/cross-subsystem = 3.
> 3. **CHAIN WHY — every layer must pass 4 checks.** (a) SPECIFIC: names a concrete identifier. (b) CAUSAL: uses "because", "which caused", "allowing", "without". (c) NOVEL: not a restatement of the layer above. (d) ACTIONABLE: identifies something that can be changed.
> 4. **THINK DEEP, WRITE SHALLOW.** Shallow output must contain the DECISION, not a summary. If you can delete it without losing the decision, it's not shallow enough. Length ratio is a symptom check, not the rule.
> 5. **FIX FIRST, QUESTION AFTER.** Diagnosis never blocks action.
> 6. **POST-FIX FEEDBACK.** After fix lands: did predicted severity match actual impact? If mismatch → record the discrepancy. The next bug of this pattern must use the corrected classification.

---

## Phase 1: Pre-Fix Assessment (BEFORE writing code)

The agent must classify the bug from **observable signals**, not subjective judgment. Self-reported fields are cross-checked against signal evidence.

### 1A. Severity — classify from observable facts

| Signal | Severity | Why |
|---|---|---|
| Crash, panic, segfault, OOM kill, deadlock, infinite loop | **CRITICAL** | Service down — no workaround possible |
| Data corruption, data loss, silent wrong-persistence | **CRITICAL** | Irreversible damage |
| Auth bypass, privilege escalation, exposed secret, SQLi, XSS, RCE | **CRITICAL** | Security boundary broken |
| Wrong output in primary business path, API contract break | **HIGH** | User-visible incorrect behavior, no crash |
| Race condition (observed, not theoretical), memory leak > 10MB/h | **HIGH** | Degrades over time or under concurrency |
| Performance regression > 50% on primary path | **HIGH** | Usability impact |
| Edge-case wrong behavior (non-primary path), missing validation | **MEDIUM** | Bug exists but main path works |
| Deprecated API usage, non-blocking warning, cosmetic defect | **LOW** | No functional impact |
| Typo (non-functional), formatting, comment fix, rename | **LOW** | Zero behavioral change |

**Rule:** Classify at the HIGHEST matching signal. A crash in an auth handler is CRITICAL (crash + auth = highest = CRITICAL).

### 1B. Security — detect from code surface, not claim

These code patterns signal security relevance. If ANY match, the bug IS security-relevant:

- Changes in `auth/`, `middleware/auth`, `guards/`, `permissions/`
- JWT/session/token generation, validation, or parsing
- OAuth flow, API key handling, credential storage
- Password hashing, crypto operations, signing
- Input sanitization, validation bypass, deserialization
- SQL query construction (`raw`, `execute`, string concatenation into query)
- File path manipulation (`os.path.join(user_input, ...)`, `Path(...)` with user data)
- Shell command execution (`subprocess`, `os.system`, `exec`, `eval`)
- CORS, CSP, rate-limit, or security header changes
- Error messages that might leak internal state to users

**Evidence rule:** If classified as `security_bug = true`, name the specific signal (e.g., "auth middleware change at `auth.py:42`").

### 1C. Data-loss risk — detect from operations

- `DELETE FROM`, `TRUNCATE`, `DROP TABLE/COLUMN`
- Migration that removes or renames a column
- State mutation without prior snapshot/backup
- `os.remove`, `shutil.rmtree`, file overwrite without temp-copy
- Database write (`INSERT`, `UPDATE`, `UPSERT`) without explicit transaction boundary
- Cache invalidation without repopulation path

### 1D. Change-type dimension (replaces naive file count)

| Change Type | Escalation effect |
|---|---|
| Logic change in ≥ 1 file | Count toward depth |
| API contract change | +1 effective file (even if 1 file) |
| Schema migration | Cross-subsystem by definition |
| Config change affecting behavior at runtime | Count as 1 file |
| Rename-only, format-only, comment-only, dead-code removal | Do NOT count toward E7 |

### 1E. Discrepancy detection

If the agent self-reports `severity = LOW` but signals match CRITICAL → **gate rejects with discrepancy flag**. Auto-classify always wins over self-report in case of conflict. The agent must justify why signals don't apply.

---

## Phase 2: During-Fix — Why-Chain with Quality Gate

### 2A. Layer depth requirement (from signals)

Base = **2 layers**. Escalated by signals (Phase 1):

| ID | Signal | Min Layers |
|---|---|---|
| E1 | severity = HIGH | 3 |
| E2 | severity = CRITICAL | 4 |
| E3 | known_pattern in knowledge base | 3 |
| E4 | recurrence_count ≥ 1 (same bug returned) | 4 |
| E5 | security_bug = true (from signal, not claim) | 4 |
| E6 | data_loss_risk = true (from signal, not claim) | 4 |
| E7 | change_type logic/API/schema in > 3 effective files | 3 |
| E8 | cross_subsystem = true | 3 |

Multiple triggers → highest layer wins (not additive).

### 2B. Layer quality heuristics — ALL 4 must pass per layer

Each why-chain layer is validated against 4 criteria. A layer that fails any criterion is **rejected** and must be rewritten.

#### Criterion 1: SPECIFICITY — names a concrete identifier

**Pass:** `"flush() in BufferPool.release() at buffer_pool.py:142 skips the fsync path when use_async=false"`
**Fail:** `"there was a sync issue"` — no identifier
**Fail:** `"the function didn't work"` — no identifier

Check: grep for at least one of: function name, file:line, variable name, config key, error code, API endpoint.

#### Criterion 2: CAUSALITY — uses causal language

**Pass:** `"because validate_input() returns None for empty strings, which caused downstream to dereference without checking"`
**Fail:** `"the input was empty"` — statement of fact, not cause
**Fail:** `"it broke after the refactor"` — correlation, not causation

Check: must contain at least one of: "because", "which caused", "allowing", "without", "due to", "as a result of", "leading to", "therefore".

#### Criterion 3: NOVELTY — not a restatement of the layer above

**L1:** `"Null pointer dereference at user.email because get_user() returned None"`
**L2 PASS:** `"get_user() can return None because the API contract doesn't guarantee a non-null return, and no caller-side guard exists at any of the 12 call sites"`
**L2 FAIL:** `"user.email was accessed on null user"` — restates L1

Check: L2 must introduce new information not present in L1. If L2 can be generated by paraphrasing L1, it fails.

#### Criterion 4: ACTIONABILITY — identifies something changeable

**Pass:** `"No rate-limit middleware on the login endpoint; add @rate_limit(5/min) decorator"`
**Fail:** `"users might try to brute force passwords"` — not changeable
**Fail:** `"the system is complex"` — not changeable

Check: names at least one of: code to add/change/remove, config to set, test to write, hook/lint rule to add, process to change, monitoring to add.

### 2C. Layer definition (what each layer answers)

| Layer | Question | Must identify |
|---|---|---|
| **L1: Proximate** | What specifically broke? | Function, line, condition, state that failed |
| **L2: Systemic** | Why was that breakage possible? | Missing guard/contract/test/validation that allowed it |
| **L3: Process** | Why did the process allow this? | Missing review step, CI gap, missing lint rule, missing test category |
| **L4: Meta** | Why does the system permit this class? | Architectural pattern, organizational norm, missing abstraction layer |

### 2D. Think deep, write shallow — qualitative criteria

The 30% length ratio is a **symptom check**, not the rule. The real criteria:

1. **Decision-bearing:** Shallow output must contain the decision made. If you can delete the shallow output without changing what the reader would do next, it fails.
2. **No summary:** If shallow output starts with "In summary" / "To recap" / "The above analysis shows" → it's a summary, not shallow output. Delete and rewrite.
3. **Action-first:** Shallow output leads with the action: "Fix: add null guard at `auth.py:42` + add `strictNullChecks` to tsconfig."
4. **Length check (symptom only):** If length > 30% of deep → investigate. But passing length doesn't mean passing quality.

---

## Phase 3: Post-Fix Gate + Feedback Loop

### 3A. Pre-merge gate checklist

Before merge, confirm ALL of:

- [ ] Severity classified from observable signals (Phase 1A) — NOT self-reported
- [ ] Security/data-loss signals scanned (Phase 1B/1C) — evidence cited
- [ ] Min layers computed from escalation matrix (Phase 2A)
- [ ] Why-chain has ≥ min_layers entries
- [ ] Each layer passes ALL 4 quality heuristics (Phase 2B)
- [ ] Known pattern + different location → grep_all_scan produced + all instances fixed
- [ ] Shallow output is decision-bearing (Phase 2D) — not just a summary
- [ ] Deep reasoning exists and is non-empty
- [ ] diagnosis_blocks_action is NOT set (Phase 5: fix first)

### 3B. Feedback loop — discrepancy audit

After fix lands and impact is known:

1. **Compare:** Did predicted severity match actual impact?
   - `predicted=LOW, actual=CRITICAL` → **MISCLASSIFY (false negative)** — record
   - `predicted=CRITICAL, actual=LOW` → **MISCLASSIFY (false positive)** — record
2. **Record discrepancy** in project post-mortem or pattern knowledge base
3. **Next bug of same pattern** → use corrected classification, not original

### 3C. Pattern → Knowledge Base handoff

After fix lands:
- NEW pattern → add to knowledge base with signal signature
- KNOWN pattern → update hit count, verify classification was correct
- Knowledge base entry format: `{pattern_name, signals, correct_severity, correct_min_layers, false_positives, false_negatives}`

---

## Pattern Matrix (updated)

| Pattern | Location | Action |
|---|---|---|
| **NEW** | — | Run Phase 1-3. Post-fix: add to knowledge base. |
| **KNOWN** | **SAME** location | Regression. Check why previous fix didn't hold (→ E4 recurrence). |
| **KNOWN** | **DIFFERENT** location | **ESCALATE.** Grep ALL instances. Fix each. Cross-check: were any of these previously classified wrong? |

---

## Decision Tree (complete)

```
START
  │
  ├─ Phase 1: PRE-FIX ASSESS
  │   ├─ Scan observable signals (crash/corruption/auth/data-loss/API-break/race/perf)
  │   ├─ Classify severity → CRITICAL/HIGH/MEDIUM/LOW (highest matching signal)
  │   ├─ Detect security surface (auth/crypto/session/SQL/exec/file-path)
  │   ├─ Detect data-loss risk (DELETE/TRUNCATE/DROP/migration/no-backup)
  │   ├─ Compute change-type (logic/API/schema/config vs rename/format/comment)
  │   └─ Resolve self-report vs auto-classify discrepancy → auto-classify WINS
  │
  ├─ Phase 2: COMPUTE DEPTH + CHAIN WHY
  │   ├─ Apply escalation matrix → min_layers
  │   ├─ Draft why-chain (L1→L2→[L3]→[L4])
  │   ├─ Validate each layer against 4 quality heuristics
  │   │   ├─ SPECIFICITY: concrete identifier present?
  │   │   ├─ CAUSALITY: causal language present?
  │   │   ├─ NOVELTY: not a restatement of layer above?
  │   │   └─ ACTIONABILITY: identifies something changeable?
  │   └─ Reject + rewrite any layer that fails
  │
  ├─ Phase 3: SHALLOW OUTPUT
  │   ├─ Extract decision (not summary)
  │   ├─ Action-first format
  │   └─ Length ratio check (symptom only, ≤30%)
  │
  ├─ FIX FIRST (diagnosis never blocks action)
  │
  └─ Phase 3B: POST-FIX FEEDBACK
      ├─ Compare predicted vs actual severity
      ├─ Record discrepancy if any
      └─ Update knowledge base
```

---

## Operating Rules

- **Recite once per session**, in your first response when invoked. Do not re-recite.
- **Recite verbatim.** Never paraphrase, shorten, or skip lines.
- **Phase 1 before Phase 2.** Do not start why-chain before classifying from signals.
- **Signals, not opinions.** Every severity/security/data-loss claim must cite a specific observable signal.
- **Auto-classify wins.** If self-report conflicts with signal evidence, auto-classify overrides. Agent must justify why signals don't apply.
- **4 quality checks per layer.** A layer that fails specificity/causality/novelty/actionability is NOT a layer — it's filler. Rewrite it.
- **Decision-bearing shallow output.** If deleting the shallow output wouldn't change what the reader does, it fails.
- **Grep before fixing known patterns.** Scan the whole repo before touching the first file.
- **Post-fix feedback is mandatory.** After any fix at MEDIUM+, record whether predicted severity was correct.
- **The recital is a constraint YOU carry** — not advice to deliver back to the user.
