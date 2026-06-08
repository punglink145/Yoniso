# Deterministic Enforcement — Yoniso v3.1.0

## What This Skill Can and Cannot Do

### CAN DO (Prompt-Level Guidance)

Yoniso provides detailed behavioral instructions to Claude Code. When the skill
is active, Claude receives the operating loop, severity tables, depth matrices,
quality gates, and output contracts as part of its system prompt. A capable
model will follow these instructions in its responses.

The skill **guides** Claude's behavior. It does not **guarantee** it.

### CANNOT DO (Requires External Tooling)

Yoniso as a skill cannot:

- Block a commit if the why-chain is too shallow
- Verify that severity was classified from signals
- Validate that all 4 quality gates were checked
- Prevent Claude from skipping the post-fix feedback step
- Enforce that known-pattern instances were all grep'd and fixed

These require **deterministic enforcement** — external scripts, hooks, or CI
that run regardless of what the language model outputs.

---

## Deterministic Enforcement Strategy

### Option 1: Pre-Commit Hook (Local)

Add to `.git/hooks/pre-commit` or `.githooks/pre-commit`:

```bash
#!/bin/bash
# Check if SKILL.md is valid (for skill development)
if [ -f "SKILL.md" ]; then
    python scripts/validate_skill.py || {
        echo "SKILL.md validation failed. Run: python scripts/validate_skill.py"
        exit 1
    }
fi
```

### Option 2: CI Gate (Recommended)

Use the included `.github/workflows/ci.yml` which runs:

- `python scripts/validate_skill.py` — validates SKILL.md structure
- `python -m pytest -q` — runs structural tests

Add branch protection rules in GitHub to require CI green before merge.

### Option 3: Claude Code Hooks

Claude Code supports hooks in `.claude/settings.json`. Example hook that runs
the validator before commits:

```json
{
  "hooks": {
    "PreCommit": [
      {
        "matcher": "SKILL.md",
        "command": "python scripts/validate_skill.py"
      }
    ]
  }
}
```

This is only relevant for the Yoniso repo itself (skill development). For
projects using Yoniso, the skill is consumed as a prompt — hooks are for the
consuming project's own enforcement needs.

### Option 4: Code Review Checklist

Add these items to the PR template of any project using Yoniso:

```markdown
## Yoniso Check (for bug fixes)

- [ ] Severity classified from observable signals (not self-report)
- [ ] Security/data-loss signals scanned — evidence cited
- [ ] Min layers computed from escalation matrix
- [ ] Each why-chain layer passes 4 quality gates
- [ ] Known pattern → grep_all_scan + all instances fixed
- [ ] Shallow output is decision-bearing
- [ ] Post-fix feedback recorded
```

### Option 5: PR Gate Script (for consuming projects)

Create a project-specific script that checks the PR description for Yoniso
fields before allowing merge. This is lightweight and doesn't depend on Claude
following the protocol perfectly — it just ensures the human reviewer saw the
Yoniso output.

---

## Enforcement Level by Severity

| Severity | Minimum Enforcement |
|----------|-------------------|
| LOW | Skill prompt guidance is sufficient |
| MEDIUM | Skill prompt + code review checklist |
| HIGH | Skill prompt + CI gate + code review checklist |
| CRITICAL | Skill prompt + CI gate + human security review + protected branch |

---

## Verifying the Skill Itself

For the Yoniso repository, the validator and test suite provide structural
enforcement:

```bash
# Validate SKILL.md structure
python scripts/validate_skill.py

# Run tests
python -m pytest -q
```

These verify that the skill file is well-formed, not that Claude follows it
correctly at runtime. Runtime correctness depends on model capability + prompt
quality. The skill maximizes prompt quality; deterministic tooling handles the
rest.
