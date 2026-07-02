#!/usr/bin/env python3
"""validate_yoniso_output.py — runtime validator for a Yoniso assessment.

Unlike validate_skill.py (which checks the SKILL.md *file* structure), this
validates the *output* a model emits when it claims to follow Yoniso. The skill
prompt GUIDES behavior; this script ENFORCES it deterministically.

Input : markdown text on stdin or --file PATH (the Yoniso Output Contract form).
Exit  : 0 = pass, 1 = fail. Use --json for machine-readable results.

Contract enforced (SKILL.md §6 + references/why-chain-quality.md):
  Yoniso Assessment: <CRITICAL|HIGH|MEDIUM|LOW>
  Signals: <observable evidence>
  Severity: <highest-matching-signal justification>
  Min Why Layers: <N>
  Root Cause Chain:
    L1: <proximate>
    L2: <systemic>
    [L3..L4 per depth]
  Fix Decision: <action-first>
  Verification: <how to confirm>
  Feedback / Pattern Update: <predicted vs actual>   (optional)

Rules:
  R_SEVERITY_ENUM          assessment present + valid enum
  R_SIGNALS_NONEMPTY       signals cite observable evidence
  R_SEVERITY_CONSISTENCY   CRITICAL -> security/data-loss signal present
  R_MIN_LAYERS_FIELD       Min Why Layers field present + numeric
  R_CHAIN_DEPTH            #layers >= severity-derived minimum
  R_LAYER_SPECIFIC         each layer names a concrete identifier
  R_LAYER_CAUSAL           each layer uses causal language
  R_LAYER_NOVEL            each layer adds new info (not a restatement)
  R_LAYER_ACTIONABLE       L2+ layers name something changeable (L1 describes, not prescribes)
  R_FIX_ACTION_FIRST       Fix Decision present + leads with the action
  R_VERIFICATION           Verification present + observable
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from typing import Optional

# ── Severity → minimum why-layers (SKILL.md §3) ──────────────────────────
# Base 2; HIGH 3; CRITICAL/security/data-loss/recurrence 4 (highest wins).

SECURITY_SIGNALS = [
    "auth", "jwt", "session", "token", "sqli", "xss", "rce", "crypto",
    "password", "oauth", "permission", "privilege", "cors", "csp",
    "rate limit", "rate-limit", "secret", "credential", "injection",
]
DATA_LOSS_SIGNALS = [
    "delete", "truncate", "drop", "remove", "migration", "destroy",
    "flush", "unlink", "irreversible", "data loss", "data-loss",
    "corrupt",
]

# ── Layer quality gate patterns (references/why-chain-quality.md) ────────
# NOTE: English keywords use \b (safe: bounded by ASCII punctuation). Thai
# keywords use plain substring (re \b is unreliable across Thai/ASCII, see
# reference-thai-regex-redaction-gotcha).

IDENTIFIER_RE = re.compile(
    r"`[^`]+`"                              # backtick-wrapped code
    r"|[A-Za-z0-9_./\\-]+\.[A-Za-z0-9]+:\d+"  # file.ext:line
    r"|\b[A-Za-z_][A-Za-z0-9_]*\([^)]*\)"     # function(...)
    r"|:\d+"                                  # :line ref
    r"|\b[A-Z][A-Z0-9_]{2,}\b"                # UPPER_SNAKE config/error code
)

CAUSAL_WORDS_EN = [
    "because", "which caused", "allowing", "without", "due to",
    "leading to", "therefore", "as a result", "caused by", "so that",
    "since", "thus",
]
CAUSAL_WORDS_TH = ["เพราะ", "ทำให้", "จึง", "เนื่องจาก", "เป็นเหตุ", "ส่งผลให้"]

ACTIONABLE_WORDS_EN = [
    "add", "remove", "fix", "change", "replace", "update", "test",
    "config", "hook", "guard", "validate", "migrate", "revert", "set",
    "implement", "refactor", "lint", "monitor", "instrument", "guard",
    "wrap", "fail", "block",
]
ACTIONABLE_WORDS_TH = ["เพิ่ม", "ลบ", "แก้", "เปลี่ยน", "ตั้ง", "ย้าย", "ปิด", "เปิด"]

ACTION_FIRST_RE = re.compile(
    r"^\s*(fix|add|remove|change|replace|update|revert|implement|"
    r"migrate|set|refactor|roll\s*back|rollback|guard|block|wrap)\b",
    re.IGNORECASE,
)


# ── Parsing ──────────────────────────────────────────────────────────────
KNOWN_FIELDS = [
    "yoniso assessment",
    "signals",
    "severity",
    "min why layers",
    "root cause chain",
    "fix decision",
    "verification",
    "feedback / pattern update",
    "feedback",
]


@dataclass
class YonisoDoc:
    assessment: str = ""
    signals: str = ""
    severity: str = ""
    min_why_layers: str = ""
    chain_lines: list[str] = field(default_factory=list)
    fix_decision: str = ""
    verification: str = ""
    feedback: str = ""


def parse(text: str) -> YonisoDoc:
    """Parse a Yoniso markdown output into its contract fields."""
    doc = YonisoDoc()
    lines = text.splitlines()

    # Find section header positions: a line "Field:" or "Field / X:" at start.
    headers: list[tuple[str, int]] = []
    for i, line in enumerate(lines):
        m = re.match(r"^\s*([A-Za-z][A-Za-z /]*?):\s*(.*)$", line)
        if not m:
            continue
        key = m.group(1).strip().lower()
        if key in KNOWN_FIELDS:
            headers.append((key, i))

    def field_value(key: str) -> str:
        for idx, (k, i) in enumerate(headers):
            if k != key:
                continue
            start = lines[i].split(":", 1)[1]
            end = headers[idx + 1][1] if idx + 1 < len(headers) else len(lines)
            body = "\n".join([start] + lines[i + 1 : end]).strip()
            return body
        return ""

    doc.assessment = field_value("yoniso assessment").strip()
    doc.signals = field_value("signals").strip()
    doc.severity = field_value("severity").strip()
    doc.min_why_layers = field_value("min why layers").strip()
    doc.fix_decision = field_value("fix decision").strip()
    doc.verification = field_value("verification").strip()
    doc.feedback = (
        field_value("feedback / pattern update") or field_value("feedback")
    ).strip()

    # Root Cause Chain: collect L1:/L2:/... lines until next header.
    chain_key = "root cause chain"
    for idx, (k, i) in enumerate(headers):
        if k != chain_key:
            continue
        end = headers[idx + 1][1] if idx + 1 < len(headers) else len(lines)
        for line in lines[i + 1 : end]:
            lm = re.match(r"^\s*L(\d+)\s*[:.\-]\s*(.+)$", line)
            if lm:
                doc.chain_lines.append(f"L{lm.group(1)}: {lm.group(2).strip()}")
    return doc


# ── Rule helpers ─────────────────────────────────────────────────────────
def has_security_signal(text: str) -> bool:
    t = text.lower()
    return any(s in t for s in SECURITY_SIGNALS)


def has_data_loss_signal(text: str) -> bool:
    t = text.lower()
    return any(s in t for s in DATA_LOSS_SIGNALS)


def min_layers_for(assessment: str, signals: str) -> int:
    if assessment == "CRITICAL":
        return 4
    if assessment == "HIGH":
        return 3
    if has_security_signal(signals) or has_data_loss_signal(signals):
        return 4
    if assessment == "MEDIUM":
        return 2
    if assessment == "LOW":
        return 1
    return 2  # unknown -> base


def has_causal(text: str) -> bool:
    t = text.lower()
    if any(re.search(rf"\b{re.escape(w)}\b", t) for w in CAUSAL_WORDS_EN):
        return True
    return any(w in t for w in CAUSAL_WORDS_TH)


def has_actionable(text: str) -> bool:
    t = text.lower()
    if any(re.search(rf"\b{re.escape(w)}\b", t) for w in ACTIONABLE_WORDS_EN):
        return True
    return any(w in t for w in ACTIONABLE_WORDS_TH)


def is_novel(cur: str, prev: Optional[str]) -> bool:
    if prev is None:
        return True
    c, p = cur.lower().strip(), prev.lower().strip()
    if not c or c == p:
        return False
    # Restatement if one is a near-substring of the other.
    if c in p or p in c:
        return False
    return True


# ── Rules → findings ─────────────────────────────────────────────────────
@dataclass
class Finding:
    rule: str
    passed: bool
    detail: str = ""


def evaluate(doc: YonisoDoc) -> list[Finding]:
    out: list[Finding] = []
    assessment = doc.assessment.upper().strip()

    # R_SEVERITY_ENUM
    out.append(Finding(
        "R_SEVERITY_ENUM",
        assessment in {"CRITICAL", "HIGH", "MEDIUM", "LOW"},
        f"assessment='{doc.assessment or '(missing)'}'",
    ))

    # R_SIGNALS_NONEMPTY
    out.append(Finding(
        "R_SIGNALS_NONEMPTY",
        len(doc.signals) >= 3,
        "signals must cite observable evidence" if not doc.signals else "ok",
    ))

    # R_SEVERITY_CONSISTENCY — CRITICAL requires a security/data-loss signal
    sig_blob = f"{doc.signals} {doc.severity}"
    if assessment == "CRITICAL":
        out.append(Finding(
            "R_SEVERITY_CONSISTENCY",
            has_security_signal(sig_blob) or has_data_loss_signal(sig_blob),
            "CRITICAL requires a security or data-loss signal cited in Signals/Severity",
        ))

    # R_MIN_LAYERS_FIELD
    mwl_ok = bool(re.match(r"^\d+$", doc.min_why_layers.strip()))
    out.append(Finding(
        "R_MIN_LAYERS_FIELD",
        mwl_ok,
        f"Min Why Layers='{doc.min_why_layers or '(missing)'}'",
    ))

    # R_CHAIN_DEPTH — compare against severity-derived minimum
    want = min_layers_for(assessment, sig_blob)
    have = len(doc.chain_lines)
    out.append(Finding(
        "R_CHAIN_DEPTH",
        have >= want,
        f"have {have} layers, need >= {want} (severity={assessment or '?'})",
    ))

    # Per-layer gates
    prev: Optional[str] = None
    for i, line in enumerate(doc.chain_lines):
        body = line.split(":", 1)[1].strip() if ":" in line else line
        tag = f"L{i+1}"

        out.append(Finding(
            f"R_LAYER_SPECIFIC/{tag}",
            bool(IDENTIFIER_RE.search(body)),
            f"{tag} must name a concrete identifier (file:line / `code` / func() / UPPER_KEY)",
        ))
        out.append(Finding(
            f"R_LAYER_CAUSAL/{tag}",
            has_causal(body),
            f"{tag} must use causal language (because/which caused/without/due to/leading to)",
        ))
        out.append(Finding(
            f"R_LAYER_NOVEL/{tag}",
            is_novel(body, prev),
            f"{tag} must add new information beyond the layer above",
        ))
        # ACTIONABLE is enforced from L2 onward — L1 is the proximate layer
        # ("what broke"), whose job is to describe, not prescribe. L2+ must
        # name something changeable (SKILL.md §4 layer semantics).
        if i >= 1:
            out.append(Finding(
                f"R_LAYER_ACTIONABLE/{tag}",
                has_actionable(body),
                f"{tag} must identify something changeable (add/test/guard/config/...)",
            ))
        prev = body

    # R_FIX_ACTION_FIRST
    fix_ok = bool(doc.fix_decision) and bool(ACTION_FIRST_RE.search(doc.fix_decision))
    out.append(Finding(
        "R_FIX_ACTION_FIRST",
        fix_ok,
        "Fix Decision must be present and lead with the action (Fix:/Add:/Remove:/Revert:/...)",
    ))

    # R_VERIFICATION
    out.append(Finding(
        "R_VERIFICATION",
        len(doc.verification) >= 3,
        "Verification must describe how to confirm the fix",
    ))

    return out


# ── CLI ──────────────────────────────────────────────────────────────────
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--file", help="read output from PATH (default: stdin)")
    ap.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    ap.add_argument("--quiet", action="store_true", help="only summary line")
    args = ap.parse_args()

    if args.file:
        try:
            text = open(args.file, encoding="utf-8").read()
        except OSError as e:
            print(f"FAIL: cannot read {args.file}: {e}", file=sys.stderr)
            return 1
    else:
        text = sys.stdin.read()

    findings = evaluate(parse(text))
    failed = [f for f in findings if not f.passed]

    if args.json:
        print(json.dumps({
            "passed": not failed,
            "findings": [
                {"rule": f.rule, "passed": f.passed, "detail": f.detail}
                for f in findings
            ],
        }, ensure_ascii=False, indent=2))
    elif not args.quiet:
        for f in findings:
            mark = "PASS" if f.passed else "FAIL"
            print(f"[{mark}] {f.rule} — {f.detail}")

    total = len(findings)
    print(
        f"\n{'PASS' if not failed else 'FAIL'}: "
        f"{total - len(failed)}/{total} rules passed, {len(failed)} failed",
        file=sys.stderr if args.json else sys.stdout,
    )
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
