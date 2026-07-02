# code-review Bridge — Yoniso v3.3.0 (tier-3 breadth)

## The three tiers

Yoniso and Anthropic's `code-review` plugin are **different axes**, not
competitors:

| Tier | Tool | Axis | Fires when | Cost |
|------|------|------|------------|------|
| **T1 — depth** | yoniso skill (auto-loaded) | discipline: severity → why-chain → 4 gates | any bug / plan / review turn | light, single context |
| **T2 — breadth (vanilla)** | `/code-review` (Anthropic plugin) | multi-agent PR scan, flat-80 cutoff | invoked on a PR | heavy, 5 Sonnet + N Haiku |
| **T3 — breadth (severity-weighted)** | `/yoniso-review` (this repo) | T2 fan-out + yoniso severity routing | invoked on a PR with a critical/security/data-loss surface | heavy (same fan-out) |

**They never run at the same time** — yoniso is the always-on discipline; the
review commands are opt-in PR workflows. "Merging" therefore means **layering**,
not folding one file into another (forking the upstream plugin would inherit its
update + attribution burden for no gain).

## What the merge actually changes

T2's flat "drop everything below 80" cutoff has two known failure modes:

1. **under-surface** a low-confidence CRITICAL/security/data-loss bug (a 60 that
   is a real auth bypass gets filtered out), and
2. **over-surface** a HIGH-confidence MEDIUM/LOW nitpick (an 85 typo wastes a
   reviewer's eye).

T3 fixes both with a **severity-weighted threshold** (yoniso §2 severity + a
security/data-loss flag drive the cutoff; first match wins):

| condition | Keep when confidence ≥ | Why |
|-----------|------------------------|-----|
| severity = CRITICAL | **50** | a missed CRITICAL costs more than a false alarm |
| security_or_data_loss = true (any severity) | **50** | escalates a MEDIUM/HIGH security or data-loss issue to the low bar |
| severity = HIGH | **65** | important; verify, don't over-filter |
| severity = MEDIUM | **80** | the T2 default |
| severity = LOW | **drop** | yoniso: LOW needs 1 why + fix; it is nitpick noise in a PR comment |

The scorer therefore returns `(severity, security_or_data_loss, confidence)` —
the boolean flag is what stops a missing-rate-limit (a security signal rated
MEDIUM, conf 65) from being silently dropped by the MEDIUM ≥ 80 row. The
fan-out, the per-issue Haiku confidence scoring, and the `gh pr comment` output
all stay intact — T3 only swaps the filter and tags each finding with severity
(+ a one-line root cause for CRITICAL/HIGH).

## When to use which

| Situation | Use |
|-----------|-----|
| Fixing a bug, writing a plan, single-file review, any normal turn | **T1 yoniso** (auto) |
| Vanilla PR breadth scan, no known critical surface | **T2 `/code-review`** |
| PR touching auth / crypto / migrations / data paths / privileges | **T3 `/yoniso-review`** |
| You want the shortest review (triage) | **T3** (LOW dropped, severity-ordered) |

## Token economics

Merging does **not** cut raw tokens — the tools fire on different triggers, so
they never run together. The real savings:

- **LOW dropped** in T3 → shorter `gh pr comment`, less reviewer noise (human
  time, not model tokens).
- **Severity ordering + root-cause one-liners** → reviewer acts on CRITICAL
  first, fewer re-review cycles.
- The bigger, independent win (shipped in v3.2.0): the runtime validator +
  `Stop` hook block shallow yoniso output *before the turn ends*, cutting
  rework. That is orthogonal to this merge.

## Install

`/yoniso-review` is a slash command. To activate it in Claude Code:

```bash
cp commands/yoniso-review.md ~/.claude/commands/yoniso-review.md
```

Then restart Claude Code (or reload commands). Invoke with `/yoniso-review`.

(The command lives in this repo as a versioned source template, the same way
`.claude/settings.example.json` does — copy, don't symlink, so updates to the
skill don't silently change a live command.)

## Provenance / license

- The fan-out workflow (eligibility → CLAUDE.md list → summary → 5 review agents
  → per-issue scorer → re-check → `gh comment`) is adapted from the
  `code-review` plugin in the `claude-plugins-official` marketplace snapshot
  (Anthropic, MIT). This is a **frozen adaptation of that snapshot** — if the
  upstream plugin changes its fan-out (agent count, inline-comment path, etc.),
  this bridge does not track it automatically; re-diff against upstream before
  relying on "same fan-out" claims. Keep this attribution if you redistribute.
- The severity table, the 4 quality gates, the security/data-loss flag, and the
  severity-weighted threshold are yoniso's.
