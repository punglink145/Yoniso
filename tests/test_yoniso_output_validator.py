"""Tests for scripts/validate_yoniso_output.py — the runtime output validator.

Two layers:
  - fixture-driven: every pass/*.md must pass all rules; every fail/*.md
    must fail at least one.
  - unit: rule helpers (min_layers_for, has_causal, has_actionable, is_novel,
    parse) behave per SKILL.md §3-§5.

Run: python -m pytest -q tests/test_yoniso_output_validator.py
"""
import importlib.util
import json
import pathlib
import subprocess
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "validate_yoniso_output.py"
FIX = ROOT / "tests" / "fixtures" / "yoniso_outputs"

# Load the validator as a module (no package install needed).
# Register in sys.modules BEFORE exec so @dataclass can resolve cls.__module__.
_spec = importlib.util.spec_from_file_location("vyo", SCRIPT)
vyo = importlib.util.module_from_spec(_spec)
sys.modules["vyo"] = vyo
_spec.loader.exec_module(vyo)


def _run_cli(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True, text=True, encoding="utf-8",
    )


# ── Fixture-driven ───────────────────────────────────────────────────────
@pytest.mark.parametrize("path", sorted((FIX / "pass").glob("*.md")))
def test_pass_fixture(path):
    findings = vyo.evaluate(vyo.parse(path.read_text(encoding="utf-8")))
    failed = [f.rule if hasattr(f, "rules") else f.rule for f in findings if not f.passed]
    assert not failed, f"{path.name} should PASS but failed rules: {failed}"


@pytest.mark.parametrize("path", sorted((FIX / "fail").glob("*.md")))
def test_fail_fixture(path):
    findings = vyo.evaluate(vyo.parse(path.read_text(encoding="utf-8")))
    failed = [f.rule for f in findings if not f.passed]
    assert failed, f"{path.name} should FAIL but passed every rule"


# ── Severity → min layers (§3) ───────────────────────────────────────────
def test_min_layers_base():
    assert vyo.min_layers_for("LOW", "") == 1
    assert vyo.min_layers_for("MEDIUM", "") == 2
    assert vyo.min_layers_for("HIGH", "") == 3
    assert vyo.min_layers_for("CRITICAL", "") == 4


def test_min_layers_security_escalates():
    # A security/data-loss signal forces depth 4 regardless of assessment.
    assert vyo.min_layers_for("MEDIUM", "auth bypass via jwt") == 4
    assert vyo.min_layers_for("LOW", "drop column migration") == 4


# ── Causal / Actionable gates (§5) ───────────────────────────────────────
@pytest.mark.parametrize("phrase", [
    "because the guard was missing",
    "which caused the null deref",
    "allowing the bypass",
    "without a transaction",
    "due to the missing await",
    "leading to data loss",
    "ทำให้เกิดข้อผิดพลาด",
])
def test_has_causal_true(phrase):
    assert vyo.has_causal(phrase)


@pytest.mark.parametrize("phrase", [
    "the function returns 5",
    "this is a statement of fact",
    "a correlation was observed",
])
def test_has_causal_false(phrase):
    assert not vyo.has_causal(phrase)


@pytest.mark.parametrize("phrase", [
    "add a null guard",
    "remove the dead code",
    "fix the off-by-one",
    "add a test category",
    "เพิ่ม guard clause",
])
def test_has_actionable_true(phrase):
    assert vyo.has_actionable(phrase)


@pytest.mark.parametrize("phrase", [
    "the system is complex",
    "users might try to brute force",
    "we should be more careful",
])
def test_has_actionable_false(phrase):
    assert not vyo.has_actionable(phrase)


# ── Novelty gate ─────────────────────────────────────────────────────────
def test_is_novel_first_layer():
    assert vyo.is_novel("anything", None)


def test_is_novel_rejects_restatement():
    assert not vyo.is_novel("user.email was accessed", "user.email was accessed")


def test_is_novel_rejects_substring():
    # cur is a substring of prev → restatement
    assert not vyo.is_novel("abc", "abcdef abc")


def test_is_novel_accepts_new_info():
    assert vyo.is_novel(
        "API contract gap, 12 call sites, design mismatch",
        "Null deref because get_user() returned None",
    )


# ── Parse ────────────────────────────────────────────────────────────────
def test_parse_extracts_fields():
    text = (
        "Yoniso Assessment: HIGH\n"
        "Signals: race at x.py:1\n"
        "Severity: HIGH — race\n"
        "Min Why Layers: 3\n"
        "Root Cause Chain:\n"
        "  L1: proximate because x\n"
        "  L2: systemic\n"
        "Fix Decision: Add a lock at x.py:1\n"
        "Verification: run the test\n"
    )
    doc = vyo.parse(text)
    assert doc.assessment == "HIGH"
    assert doc.min_why_layers == "3"
    assert len(doc.chain_lines) == 2
    assert doc.fix_decision.startswith("Add a lock")


# ── CLI behavior ─────────────────────────────────────────────────────────
def test_cli_exit_zero_on_pass():
    r = _run_cli("--file", str(FIX / "pass" / "MEDIUM-edge.md"), "--quiet")
    assert r.returncode == 0, r.stderr


def test_cli_exit_one_on_fail():
    r = _run_cli("--file", str(FIX / "fail" / "shallow-chain.md"), "--quiet")
    assert r.returncode == 1


def test_cli_json_output():
    r = _run_cli("--file", str(FIX / "pass" / "LOW-typo.md"), "--json")
    assert r.returncode == 0
    data = json.loads(r.stdout)
    assert data["passed"] is True
    assert isinstance(data["findings"], list) and data["findings"]


def test_cli_json_reports_failure():
    r = _run_cli("--file", str(FIX / "fail" / "missing-severity.md"), "--json")
    assert r.returncode == 1
    data = json.loads(r.stdout)
    assert data["passed"] is False
    rules = {f["rule"] for f in data["findings"]}
    assert "R_SEVERITY_ENUM" in rules
