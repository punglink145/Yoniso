# YONISO-MANASIKARA v3.1.0

> Recursive root-cause discipline for Claude Code — classify signals, chain
> why-layers, fix first, feed back.
>
> โยนิโสมนสิการ — หลักการตั้งคำถามย้อนกลับ สำหรับ Claude Code

---

## What Problem This Solves

Claude Code tends to patch surface-level symptoms without asking **why the bug
existed in the first place.** Yoniso forces signal-based severity
classification, minimum why-chain depth, layer quality checks, action-first
fixes, and post-fix feedback — so fixes are root-cause fixes, not symptom
patches.

YONISO เกิดจาก agent ชอบแก้บั๊กแบบ surface-level โดยไม่ถามว่า *ทำไมบั๊กถึงเกิดตั้งแต่แรก*

**Timeline:**

| Date | Event |
|------|-------|
| 02 Jun 2026 | ADR-022 APPROVED (Triad 2-of-3) — 9arm enforcement activated |
| 02 Jun 2026 | First yoniso commit — closed root-causes from scheduler audit |
| 05 Jun 2026 | **v3.0.0** — signal-based auto-classification + 4-point layer quality heuristics |
| 08 Jun 2026 | **v3.1.0** — production-grade: validator, CI, 22 tests, progressive disclosure |

**DNA:** YONISO is the only **LMA-native** skill among the 5 in the 9ARM bundle — purpose-built for enforcing recursive root questioning, not ported from existing skills.

---

## When to Use

- **Fixing bugs** — classify severity before touching code
- **Reviewing code** — trace every finding to root cause
- **Writing plans** — surface assumptions and risk signals
- **Architecture decisions** — validate why the current architecture allows the
  problem
- **Investigating regressions** — why did the previous fix fail?
- **Security/data-loss incidents** — mandatory 4-layer chain

---

## Installation

### Personal Skill (Recommended)

```bash
# Clone into your skills directory
git clone https://github.com/punglink145/Yoniso ~/.claude/skills/yoniso
```

Then Claude Code auto-loads it when relevant, or invoke with `/yoniso`.

### Project Skill

Copy `SKILL.md` into `.claude/skills/yoniso/` in your project root.

### Direct Invocation

Type `/yoniso` in any Claude Code session.

---

## Usage

### Automatic

The skill's description triggers Claude Code to load Yoniso when you ask to:

- Fix a bug
- Review code / PR
- Write an implementation plan
- Make an architecture decision
- Investigate a regression
- Assess security or data-loss risk

### Direct

```
/yoniso
```

Or explicit prompts:

- "Use Yoniso to fix this bug."
- "Review this PR with Yoniso."
- "Apply Yoniso before changing this architecture."

---

## How It Works

### 3-Phase Discipline

1. **PRE-FIX ASSESS** — classify severity from observable signals (crash, auth,
   data-loss, API break, race, edge-case). Auto-classify wins over self-report.

2. **DURING-FIX** — chain why-layers to computed depth. Each layer must pass 4
   quality gates: Specific, Causal, Novel, Actionable.

3. **POST-FIX FEEDBACK** — compare predicted vs actual severity. Record
   discrepancies. Update pattern knowledge.

### Severity → Depth

| Severity | Min Layers | When |
|----------|------------|------|
| LOW | 1 | Typo, format, rename — do not over-analyze |
| MEDIUM | 2 | Edge-case, missing validation |
| HIGH | 3 | API break, race condition, perf regression |
| CRITICAL | 4 | Crash, data-loss, auth bypass, SQLi/RCE |
| Security / Data-loss / Recurrence | 4 | Always — regardless of apparent severity |

### Output

Every Yoniso output carries the **decision**, not a summary. Action-first.
Shallow. If you can delete the output without changing what to do next, it
failed.

For details, see `SKILL.md` and `references/`.

---

## What's New in v3.1.0

- **Valid YAML frontmatter** — fixed colon-in-description parse error
- **Progressive disclosure** — `SKILL.md` is ~170 lines (down from 264);
  detailed matrices moved to `references/`
- **References split** — severity signals, why-chain quality, templates,
  examples, deterministic enforcement
- **Validator + tests + CI** — `scripts/validate_skill.py`, `tests/`, and
  `.github/workflows/ci.yml`
- **Clearer trigger description** — optimized for Claude Code auto-loading
- **Deterministic enforcement caveat** — documents what the skill CANNOT
  enforce by prompt alone, with strategies for hooks/CI/checklists
- **Activation banner** — replaces the wasteful verbatim recital with a short
  `[yoniso v3.1.0]` banner
- **Depth proportionality rule** — explicitly warns against over-analyzing LOW
  and under-analyzing CRITICAL

---

## File Structure

```
Yoniso/
├── SKILL.md                              # Claude Code skill definition
├── README.md                             # This file
├── LICENSE                               # MIT
├── references/
│   ├── severity-signals.md               # Full severity matrix + catalogs
│   ├── why-chain-quality.md              # 4-gate heuristics + shallow-output
│   ├── templates.md                      # Copy-paste output templates
│   ├── examples.md                       # Worked examples (LOW→CRITICAL)
│   └── deterministic-enforcement.md      # Hooks/CI/validator strategy
├── scripts/
│   └── validate_skill.py                 # SKILL.md structural validator
├── tests/
│   ├── test_skill_structure.py           # Structural tests
│   └── test_skill_content.py             # Content tests
└── .github/workflows/
    └── ci.yml                            # CI: validator + pytest
```

---

## Development

### Run Validator

```bash
python scripts/validate_skill.py
```

### Run Tests

```bash
pip install pytest
python -m pytest -q
```

---

## License

MIT

---

## Origin / ที่มา

YONISO was born from **R-CORE-007** in the LMA (Local Multi-Agent OS) project.
Agents kept patching symptoms without asking *why* the bug existed. The skill
was purpose-built as the only LMA-native discipline in the 9ARM bundle.

Originally part of a private monorepo. Extracted to a standalone skill
repository so any Claude Code user can install it.
