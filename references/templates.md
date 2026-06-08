# Templates Reference — Yoniso v3.1.0

Copy-paste templates for each Yoniso output format.

---

## Template 1: Bug Fix (Complete)

```
Yoniso Assessment: [CRITICAL|HIGH|MEDIUM|LOW]
Signals: [list observable evidence — crash trace, data-loss operation,
          auth middleware change, API break, race log, edge-case repro]
Severity: [classification] — [which signal triggered this level]
Min Why Layers: [N]

Root Cause Chain:
  L1: [function/line/condition that failed] because [immediate cause]
  L2: [why L1 was possible] — [missing guard/contract/test/validation]
  L3: (if applicable) [why review/CI/process allowed L2]
  L4: (if applicable) [why system architecture permits this class]

Fix Decision: [concrete change at file:line] — [why this fixes it]

Verification: [test command, manual repro step, log check]

Feedback / Pattern Update:
  Predicted severity: [X] → Actual impact: [Y]
  Discrepancy: [none|false_positive|false_negative]
  Pattern: [NEW pattern name | KNOWN pattern name — hit count updated]
```

---

## Template 2: Quick Fix (LOW Severity — Short Form)

```
Yoniso: LOW — [typo|formatting|comment|rename] at [file:line]
Why: [one-line reason]
Fix: [one-line change]
Done. No further Yoniso analysis needed.
```

---

## Template 3: Implementation Plan

```
Yoniso Planning Check

Assumptions:
  - [assumption 1 — what we believe is true]
  - [assumption 2]
  - [assumption N]

Risk Signals:
  - [risk 1]: severity if wrong = [CRITICAL|HIGH|MEDIUM], probability = [high|med|low]
  - [risk 2]: severity if wrong = [...], probability = [...]

Depth Needed: [how many Yoniso layers each risk warrants]

Decision:
  What: [what to build]
  Order: [what first, what second]
  Gates: [what must be true before proceeding to next step]

Validation Plan:
  - [how to confirm assumption 1]
  - [how to test risk 1 is mitigated]
  - [how to measure success]
```

---

## Template 4: Code Review Finding

```
Yoniso Review Finding

Evidence: [file:line] — [code pattern or behavior observed]
Severity: [CRITICAL|HIGH|MEDIUM|LOW]

Root Cause:
  [why the issue exists — one or two causal sentences]

Required Fix: [concrete change needed — code, config, or design]

Test/Guard Needed:
  - [specific test to write]
  - [lint rule, CI check, or hook to add]
```

---

## Template 5: Architecture Decision

```
Yoniso Architecture Check

Decision: [what architecture decision is being made]

Signals (observable facts driving this):
  - [signal 1]
  - [signal 2]

Risk: [what breaks if wrong] — severity: [CRITICAL|HIGH|MEDIUM]

Root Analysis:
  L1: [what problem does this architecture solve?]
  L2: [why did the current architecture allow this problem?]
  L3: [what process/skill gap led us to the current architecture?]

Alternatives considered:
  - [Alt A]: trade-off = [...]
  - [Alt B]: trade-off = [...]

Validation: [how will we know this decision was right? When do we revisit?]
```

---

## Template 6: Post-Fix Feedback

```
Yoniso Post-Fix Feedback — [Bug ID or Description]

Predicted severity: [X] (classified on [date])
Actual impact: [Y] (observed after fix)

Comparison: [MATCH|MISCLASSIFY false_positive|MISCLASSIFY false_negative]

If MISCLASSIFY:
  What we missed: [signal that was present but not classified correctly]
  Why the classification was wrong: [root cause of the misclassification]
  Correction: [new severity for this pattern] → update knowledge base

Pattern update:
  Pattern name: [name]
  Previous classification: [old severity, old min_layers]
  Corrected classification: [new severity, new min_layers]
  Hit count: [N]
```
