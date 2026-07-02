---
allowed-tools: Bash(gh issue view:*), Bash(gh search:*), Bash(gh issue list:*), Bash(gh pr comment:*), Bash(gh pr diff:*), Bash(gh pr view:*), Bash(gh pr list:*)
description: Code review a pull request with yoniso severity-weighted filtering
disable-model-invocation: false
---

Provide a code review for the given pull request, **severity-weighted**.

This adapts Anthropic's official `code-review` workflow (the `/code-review`
plugin) — same fan-out, same confidence scoring — but replaces its flat
"<80" cutoff with a **severity-weighted threshold** drawn from the yoniso
discipline skill. The point: never lose a low-confidence CRITICAL, and never
waste a reviewer's eye on a HIGH-confidence LOW nitpick.

To do this, follow these steps precisely:

1. Use a Haiku agent to check if the pull request (a) is closed, (b) is a draft,
   (c) does not need a code review (automated PR, or trivially obviously ok), or
   (d) already has a code review from you. If so, do not proceed.
2. Use a Haiku agent to list file paths to (not contents of) any relevant
   CLAUDE.md files: the root CLAUDE.md (if any), plus any CLAUDE.md in
   directories the PR modified.
3. Use a Haiku agent to view the pull request and return a summary of the change.
4. Launch 5 parallel Sonnet agents to independently review the change. Each
   agent returns a list of issues, and for EACH issue must return:
   `(severity, one_line_finding, reason, evidence_link)`
   where **severity ∈ {CRITICAL, HIGH, MEDIUM, LOW}** is classified from the
   observable signal using this table (classify at the HIGHEST matching signal):

   | Signal | Severity |
   |--------|----------|
   | crash, data-loss/corruption, auth bypass, privilege escalation, exposed secret, SQLi/XSS/RCE, destructive migration, irreversible impact | **CRITICAL** |
   | wrong output on primary path, API contract break, observed race, major perf regression (>50%), concurrency bug, prod regression | **HIGH** |
   | edge-case bug, missing validation, incomplete guard, non-primary path wrong behavior | **MEDIUM** |
   | typo, formatting, comment, rename-only, non-functional warning | **LOW** |

   Security signals = auth middleware, crypto, session, SQL construction, shell
   exec, deserialization, file-path manipulation, CORS/CSP/rate-limit changes,
   error messages leaking internal state.
   Data-loss signals = DELETE/TRUNCATE/DROP, column removal, state mutation
   without backup, filesystem write without transaction, cache invalidation
   without repopulation path.

   The 5 agents:
   a. **#1 CLAUDE.md compliance** — do the changes comply with the CLAUDE.md?
      (CLAUDE.md guides Claude writing code; not every line applies to review.)
   b. **#2 shallow bug scan** — read just the diff, surface only large bugs.
      Avoid extra context, nitpicks, and likely false positives.
   c. **#3 git history** — read blame/history of modified code; bugs in light
      of that historical context.
   d. **#4 previous PR comments** — read prior PRs touching these files; check
      for comments that also apply here.
   e. **#5 code-comment compliance** — read code comments in modified files;
      ensure the change complies with guidance in those comments.

5. For each issue from step 4, launch a parallel Haiku agent that takes the PR,
   the issue (with its proposed severity), and the CLAUDE.md list (from #2), and
   returns `(severity, security_or_data_loss, confidence)` where:
   - **severity ∈ {CRITICAL, HIGH, MEDIUM, LOW}** (the scorer may correct the
     proposed severity if the signal was misclassified);
   - **security_or_data_loss ∈ {true, false}** — true iff the issue touches a
     security or data-loss signal (see §2 signal lists below), *regardless* of
     its severity (a missing rate-limit is a security signal even if rated
     MEDIUM);
   - **confidence** is 0-100, how certain it is a real issue.
   Use this rubric verbatim:
   a. 0 — false positive that doesn't survive light scrutiny, or pre-existing.
   b. 25 — might be real, might be FP; couldn't verify. Stylistic only if the
      relevant CLAUDE.md explicitly calls it out.
   c. 50 — verified real issue, but possibly a nitpick or rare in practice; not
      very important relative to the rest of the PR.
   d. 75 — double-checked; very likely a real issue hit in practice; the PR's
      approach is insufficient; important and directly impacts functionality, or
      directly mentioned in the relevant CLAUDE.md.
   e. 100 — double-checked; definitely a real issue that will happen frequently;
      evidence directly confirms it.

6. **SEVERITY-WEIGHTED FILTER (this replaces the flat <80 cutoff):** keep an
   issue iff its (severity, security_or_data_loss, confidence) passes — evaluate
   top-down, first match wins:
   | condition | keep when confidence ≥ |
   |-----------|------------------------|
   | severity = CRITICAL | **50** |
   | security_or_data_loss = true (any other severity) | **50** |
   | severity = HIGH | **65** |
   | severity = MEDIUM | **80** |
   | severity = LOW | **always drop** |

   Rationale: a missed CRITICAL costs more than a false alarm; a security or
   data-loss issue escalates to the low bar even when rated MEDIUM/HIGH; a LOW
   nitpick is noise regardless of confidence. If nothing passes, skip to the
   no-issues comment format in step 8.

7. Use a Haiku agent to repeat the eligibility check from #1.

8. Comment on the PR via `gh`. For the comment:
   a. Keep it brief; no emojis.
   b. Sort findings CRITICAL → HIGH → MEDIUM (LOW is already dropped).
   c. For **CRITICAL and HIGH** findings, append a one-line root cause: the
      proximate cause + the systemic reason it was possible (an L1 + L2 summary
      — full why-chain depth is not required in the comment).
   d. Link and cite code with full sha1 + line range.

   Format (example, 3 findings):

   ---

   ### Code review (yoniso severity-weighted)

   Found 3 issues:

   1. **[CRITICAL]** auth bypass via `alg=none` accepted at auth.py:42
      _root cause: `verify_jwt()` skips signature check on the None-alg branch; no algorithm allowlist was added in v2.1._
      <link to file+line with full sha, ≥1 line context each side>

   2. **[HIGH]** lost update on cart total at checkout.py:88 under concurrent POST
      _root cause: read-modify-write is non-atomic; never wrapped in SELECT … FOR UPDATE._
      <link>

   3. **[MEDIUM]** empty-string SKU returns 200 null row at inventory.py:21 (CLAUDE.md says "reject empty SKU")
      <link>

   Generated with Claude Code.

   ---

   Or, if nothing passed the filter:

   ---

   ### Code review (yoniso severity-weighted)

   No issues passed the severity-weighted threshold (CRITICAL/security/data-loss
   ≥ 50, HIGH ≥ 65, MEDIUM ≥ 80; LOW dropped). Checked for bugs and CLAUDE.md
   compliance.

   Generated with Claude Code.

   ---

Notes:
- Do not build/typecheck — CI handles that separately.
- Use `gh` (not web fetch) for all GitHub interaction.
- Make a todo list first.
- Cite and link each bug (CLAUDE.md references must be linked).
- Full sha only when linking (no `$(git rev-parse HEAD)`; the comment renders
  Markdown directly).
- Workflow adapted from the `code-review` plugin in the
  `claude-plugins-official` marketplace snapshot (Anthropic, MIT); severity
  weighting + root-cause tagging added by the yoniso skill. This is a **frozen
  adaptation of that snapshot**, not a live proxy — if the upstream plugin
  changes its fan-out, this command does not track it automatically.
