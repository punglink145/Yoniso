---
name: yoniso
description: >-
  Recursive root cause discipline for Claude Code. Use when fixing bugs,
  reviewing code, writing implementation plans, making architecture decisions,
  investigating regressions, classifying severity/security/data-loss risk, or
  preventing shallow symptom patches. Applies signal-based severity, minimum
  why-chain depth, layer quality checks, action-first fixes, and post-fix
  feedback. Invoke via /yoniso.
---

# YONISO-MANASIKARA v3.1.0

Recursive root questioning — classify signals, chain why-layers through quality
heuristics, fix first, feed back.

**When this skill activates:**
- `/yoniso` invoked directly
- Claude is about to fix a bug, review code, write a plan, make an architecture
  decision, investigate a regression, or assess security/data-loss risk

---

## What This Skill Does

Yoniso changes how Claude Code approaches bugs, plans, and reviews. Instead of
patching symptoms, Claude classifies observable signals first, computes required
analysis depth, builds a quality-gated why-chain, acts, and records feedback.
The result: root cause fixes, not surface patches.

---

## Activation

Output a one-line banner, then proceed:

> `[yoniso v3.1.0] signals=[...] severity=[...] layers=[...]`

Do NOT recite the full protocol. The banner confirms the discipline is engaged.
For `/yoniso` direct invocation, the user is asking for the full protocol —
output §2–§7 below.

---

## §1. Operating Loop

1. **Classify signals** — observable facts from crash, auth, data, API, race,
   perf, edge-case, typo patterns (see §2).
2. **Compute min depth** — from severity/security/data-loss/recurrence/
   cross-subsystem signals (see §3).
3. **Build why-chain** — each layer must be specific, causal, novel, actionable
   (see §4).
4. **Act first** — diagnosis never blocks the fix. Write the fix, then explain.
5. **Output decision** — shallow output carries the decision, not a summary.
6. **Record feedback** — after fix lands: did predicted severity match actual
   impact? Update pattern knowledge.

---

## §2. Severity — Classify from Observable Signals

| Signal | Severity |
|--------|----------|
| Crash, data-loss/corruption, auth bypass, privilege escalation, exposed secret, SQLi/XSS/RCE, destructive migration, irreversible user impact | **CRITICAL** |
| Wrong output on primary path, API contract break, observed race condition, major perf regression (>50%), concurrency bug, production regression | **HIGH** |
| Edge-case bug, missing validation, incomplete guard, non-primary path wrong behavior | **MEDIUM** |
| Typo, formatting, comment, rename-only, non-functional warning | **LOW** |

**Rule:** Classify at the HIGHEST matching signal. Auto-classify wins over
self-report. If discrepancy → agent must justify why signals don't apply.

Security signals: auth middleware, crypto, session, SQL construction, shell
exec, deserialization, file-path manipulation, CORS/CSP/rate-limit changes,
error messages leaking internal state.

Data-loss signals: DELETE/TRUNCATE/DROP, column removal, state mutation
without backup, filesystem write without transaction, cache invalidation
without repopulation path.

---

## §3. Depth — Min Layers from Signals

Base = **2 layers**. Escalation:

| ID | Signal | Min Layers |
|----|--------|------------|
| E1 | severity = HIGH | 3 |
| E2 | severity = CRITICAL | 4 |
| E3 | known pattern in knowledge base | 3 |
| E4 | recurrence ≥ 1 (same bug returned) | 4 |
| E5 | security_bug = true (from code surface) | 4 |
| E6 | data_loss_risk = true (from operations) | 4 |
| E7 | >3 effective files (logic/API/schema only) | 3 |
| E8 | cross_subsystem = true | 3 |

Multiple triggers → highest layer wins (not additive).

---

## §4. Layer Definitions

| Layer | Question | Must Identify |
|-------|----------|---------------|
| **L1: Proximate** | What specifically broke? | Function, line, condition, state |
| **L2: Systemic** | Why was that possible? | Missing guard/contract/test/validation |
| **L3: Process** | Why did review/test/CI allow it? | CI gap, missing lint rule, missing test category |
| **L4: Meta** | Why does the system permit this class? | Architectural pattern, missing abstraction |

---

## §5. Layer Quality — 4 Gates Per Layer

Each layer must pass ALL 4:

1. **SPECIFIC** — names a concrete identifier (function, file:line, variable,
   config key, API endpoint, error code). NOT "there was a sync issue."
2. **CAUSAL** — uses causal language ("because", "which caused", "allowing",
   "without", "due to", "leading to"). NOT correlation or observation.
3. **NOVEL** — introduces new information beyond the layer above. NOT a
   paraphrase or restatement.
4. **ACTIONABLE** — identifies something changeable (code, config, test, lint
   rule, process, monitoring). NOT "the system is complex."

A layer failing any gate is rejected and must be rewritten.

---

## §6. Output Contract

### For Fixes

```
Yoniso Assessment: [CRITICAL|HIGH|MEDIUM|LOW]
Signals: [observable evidence — crash/data/auth/API/race/edge-case]
Severity: [classification with highest-matching-signal justification]
Min Why Layers: [N]
Root Cause Chain:
  L1: [proximate]
  L2: [systemic]
  [L3..L4 per depth]
Fix Decision: [what to change, where, why]
Verification: [how to confirm the fix works]
Feedback / Pattern Update: [predicted vs actual; pattern knowledge update]
```

### For Plans

```
Yoniso Planning Check
Assumptions: [what we assume to be true]
Risk Signals: [what could break, severity if it does, probability]
Depth Needed: [how deep to investigate each risk]
Decision: [what to build, in what order, with what gates]
Validation Plan: [how to confirm the decision was right]
```

### For Reviews

```
Yoniso Review Finding
Evidence: [file:line, code pattern, observed behavior]
Severity: [CRITICAL|HIGH|MEDIUM|LOW]
Root Cause: [why the issue exists in the current code]
Required Fix: [concrete change needed]
Test/Guard Needed: [how to prevent recurrence]
```

### Depth Proportionality

- **LOW severity:** 1 concrete why + fix is enough. Do NOT over-analyze.
- **CRITICAL/security/data-loss:** Isolate blast radius first. Preserve
  evidence. Identify rollback/backup needs. Then fix. Do NOT proceed with blind
  edits.

---

## §7. Pattern Matrix

| Pattern | Location | Action |
|---------|----------|--------|
| **NEW** | — | Run full protocol. Post-fix: add to knowledge base. |
| **KNOWN** | SAME location | Regression. Check why previous fix didn't hold (→ E4). |
| **KNOWN** | DIFFERENT location | **ESCALATE.** Grep ALL instances. Fix each. Check: were any previously misclassified? |

---

## §8. Deterministic Enforcement

This skill provides **prompt-level behavioral guidance.** It cannot force Claude
Code to perform checks or block commits.

For hard enforcement, add:
- **Validator script:** `scripts/validate_skill.py` — validates SKILL.md structure
- **CI:** `.github/workflows/ci.yml` — runs validator + tests on push/PR
- **Claude Code hooks:** configure in `.claude/settings.json` to run validators
  before commits (see `references/deterministic-enforcement.md`)
- **Code review checklist:** add Yoniso gates to PR templates
- **Protected branch checks:** require CI green before merge

The severity tables and quality gates in this skill guide Claude's output. They
do not guarantee Claude will apply them. For critical systems, combine with
deterministic tooling.

---

## References

- `references/severity-signals.md` — full severity matrix, security/data-loss catalogs, change-type classification
- `references/why-chain-quality.md` — 4-gate heuristics with pass/fail examples, shallow-output criteria
- `references/templates.md` — copy-paste templates for fixes, plans, reviews, post-fix feedback
- `references/examples.md` — worked examples (LOW, MEDIUM, HIGH, CRITICAL)
- `references/deterministic-enforcement.md` — hook/CI/validator strategy
