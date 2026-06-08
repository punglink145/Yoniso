# Severity Signals Reference — Yoniso v3.1.0

Detailed severity matrix, security signal catalog, data-loss signal catalog,
change-type classification, and discrepancy handling.

---

## Full Severity Matrix

### CRITICAL — Service Down or Irreversible Damage

| Observable Signal | Why Critical |
|-------------------|--------------|
| Crash, panic, segfault, OOM kill, deadlock, infinite loop | Service down — no workaround |
| Data corruption, data loss, silent wrong-persistence | Irreversible damage |
| Auth bypass, privilege escalation | Security boundary broken |
| Exposed secret (API key, token, password in logs/code) | Credential compromise |
| SQLi, XSS, RCE, command injection | Remote exploitation vector |
| Destructive migration (DROP COLUMN/TABLE without backup) | Data gone permanently |
| Irreversible user impact (wrong email sent to all users, wrong charge) | No undo possible |

### HIGH — User-Visible Incorrect Behavior

| Observable Signal | Why High |
|------------------|----------|
| Wrong output in primary business path | User gets incorrect result |
| API contract break (schema change without version) | Downstream consumers break |
| Observed race condition (not theoretical) | Non-deterministic failure |
| Memory leak > 10MB/h | Degrades over time |
| Performance regression > 50% on primary path | Usability impact |
| Concurrency bug (deadlock, lost update, dirty read) | Data integrity risk under load |
| Production-impacting regression | Previously working feature broken |

### MEDIUM — Bug Exists but Main Path Works

| Observable Signal | Why Medium |
|------------------|------------|
| Edge-case wrong behavior (non-primary path) | Affects subset of users/scenarios |
| Missing input validation | Could become worse with unexpected input |
| Incomplete guard clause | Partial protection only |
| Deprecated API usage (still functional) | Future breakage risk |
| Non-critical path wrong behavior | Low user impact |

### LOW — Zero Behavioral Change

| Observable Signal | Why Low |
|------------------|---------|
| Typo in non-functional text | No behavior change |
| Formatting only | No behavior change |
| Comment fix | No behavior change |
| Rename-only (no logic change) | No behavior change |
| Non-functional warning suppression | No behavior change |

---

## Security Signal Catalog

These code patterns signal security relevance. If ANY match, the bug IS
security-relevant:

### Authentication & Authorization
- Changes in `auth/`, `middleware/auth`, `guards/`, `permissions/`
- JWT/session/token generation, validation, or parsing
- OAuth flow, API key handling, credential storage
- Password hashing, crypto operations, signing

### Injection & Input Safety
- Input sanitization, validation bypass, deserialization
- SQL query construction (`raw`, `execute`, string concatenation into query)
- File path manipulation (`os.path.join(user_input, ...)`, `Path(...)` with user data)
- Shell command execution (`subprocess`, `os.system`, `exec`, `eval`)

### Infrastructure & Configuration
- CORS, CSP, rate-limit, or security header changes
- Error messages that might leak internal state to users
- TLS/certificate validation changes
- Environment variable or secret management changes

### Classification Rule
If any security signal matches → `security_bug = true` (from signal, not claim).
Cite the specific evidence (e.g., "auth middleware change at `auth.py:42`").

---

## Data-Loss Signal Catalog

### Destructive Operations
- `DELETE FROM`, `TRUNCATE`, `DROP TABLE/COLUMN/INDEX`
- Migration that removes or renames a column
- `os.remove`, `shutil.rmtree`, file overwrite without temp-copy
- `UNLINK`, `DROP DATABASE`, `DROP SCHEMA`

### State Mutation Risks
- State mutation without prior snapshot/backup
- Database write (`INSERT`, `UPDATE`, `UPSERT`) without explicit transaction boundary
- Cache invalidation without repopulation path
- Redis `FLUSHDB`/`FLUSHALL` or equivalent
- Queue/topic deletion without draining

### Classification Rule
If any data-loss signal matches → `data_loss_risk = true` (from signal, not claim).

---

## Change-Type Classification

Replace naive file count with change-type analysis:

| Change Type | Escalation Effect | Examples |
|-------------|-------------------|----------|
| Logic change in >= 1 file | Count toward depth | Algorithm fix, condition change, new branch |
| API contract change | +1 effective file (even if 1 file) | Signature change, return type change, status code change |
| Schema migration | Cross-subsystem by definition | New/removed column, index change, constraint change |
| Config change affecting runtime behavior | Count as 1 file | Env var, feature flag, timeout, rate limit |
| Rename-only, format-only, comment-only, dead-code removal | Do NOT count toward E7 | No behavioral change |

---

## Discrepancy Handling

If agent self-reports `severity = LOW` but signals match a higher severity:

1. **Auto-classify wins.** The signal-based classification overrides self-report.
2. **Flag the discrepancy.** Note that agent self-assessment was wrong.
3. **Agent must justify** why the matching signals don't apply in this case.
4. **If unjustified → gate rejects.** Fix must use the higher severity.

This prevents agents from downplaying bugs to reduce required analysis depth.
