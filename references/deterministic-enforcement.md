# Deterministic Enforcement — Yoniso v3.3.0

## What This Skill Can and Cannot Do

### CAN DO (Prompt-Level Guidance)

Yoniso provides detailed behavioral instructions to Claude Code. When the skill
is active, Claude receives the operating loop, severity tables, depth matrices,
quality gates, and output contracts as part of its system prompt. A capable
model will follow these instructions in its responses.

The skill **guides** Claude's behavior. It does not **guarantee** it.

### CANNOT DO (Requires External Tooling)

As a pure prompt, Yoniso cannot enforce itself. The repo now ships tooling that
closes most of this gap (see "Now enforced" below); what remains external:

**Now enforced (via `scripts/validate_yoniso_output.py` + Stop hook):**
- Block a turn if the why-chain is too shallow (R_CHAIN_DEPTH + exit 2)
- Verify severity was classified from signals (R_SEVERITY_CONSISTENCY)
- Validate the 4 quality gates per layer (R_LAYER_SPECIFIC/CAUSAL/NOVEL/ACTIONABLE)
- Require an action-first fix and a verification step

**Still requires human/CI process (not prompt-enforceable):**
- Prevent skipping the post-fix feedback step (the field is optional in v1)
- Enforce that known-pattern instances were all grep'd and fixed
- Reject a plausible-but-wrong root cause (the validator checks shape, not truth)

These need **deterministic enforcement** beyond a single turn — repo-wide
greps, protected branches, and human review.

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

### Option 3: Claude Code Hooks (Runtime Output Validation)

Claude Code hooks live in `.claude/settings.json`. **There is no `PreCommit`
hook event in Claude Code** — the real hook events are `PreToolUse`,
`PostToolUse`, `UserPromptSubmit`, `Stop`, `SubagentStop`, `Notification`,
`SessionStart`, `SessionEnd`, and `PreCompact`. "Run something before a git
commit" is a **git** hook (Option 1), not a Claude Code event.

The Claude Code hook that fits Yoniso is `Stop` — it fires after Claude
finishes a turn and receives `last_assistant_message` on stdin, so a validator
can check whether the output actually follows the Yoniso contract (severity
classified from signals, min why-layers, 4 quality gates, action-first):

```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "python scripts/validate_yoniso_output.py"
          }
        ]
      }
    ]
  }
}
```

A `Stop` hook can block continuation by exiting with code 2 and feeding a
reason back to Claude on stderr. This is the deterministic runtime gate the
skill alone cannot provide — the prompt *guides*, the hook *enforces*.

> NOTE: `scripts/validate_yoniso_output.py` is a proposed addition (see §below).
> It validates runtime output, unlike `scripts/validate_skill.py` which only
> validates the SKILL.md *file* structure.
>
> Refs: https://code.claude.com/docs/en/hooks · https://code.claude.com/docs/en/hooks-guide

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
